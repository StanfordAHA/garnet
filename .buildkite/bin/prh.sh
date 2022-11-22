#!/bin/bash

########################################################################
# postroute_hold fails sometimes, thus all this infrastructure for retry.
# 
# "prh.sh" does the following:
#   - make postroute_hold
#   - check for errors; exit 13 if errors found
#
# Note if "make postroute_hold" did error-checking correctly, we would
# not need prh.sh. Maybe a subject for a future github issue.
########################################################################

if [ "$1" == "--help" ]; then cat << '  EOF' | sed 's/^  //'
  Usage:
      prh.sh <rundir>

  Example:
      prh.sh /build/gold230/full_chip

  Summary:
      Runs postroute_hold step and checks for QRC errors / problems.

  ------------------------------------------------------------------
  Example buildkite pipeline usage (three strikes you're out):
  
     steps:
       - commands:
         - 'source setup-buildkite.sh --dir /build/gold/full_chip;
            echo "--- POSTROUTE_HOLD - FIRST ATTEMPT"; set -o pipefail;
            $$GARNET_HOME/.buildkite/bin/prh.sh |& tee make-prh1.log'
       - wait: { continue_on_failure: true }

       - commands:
         - 'source setup-buildkite.sh --dir /build/gold/full_chip;
            echo "--- POSTROUTE_HOLD - SECOND ATTEMPT"; set -o pipefail;
            $$GARNET_HOME/.buildkite/bin/prh.sh |& tee make-prh2.log'
       - wait: { continue_on_failure: true }

       - commands:
         - 'source setup-buildkite.sh --dir /build/gold/full_chip;
            echo "--- POSTROUTE_HOLD - FINAL ATTEMPT"; set -o pipefail;
            $$GARNET_HOME/.buildkite/bin/prh.sh |& tee make-prh3.log'
       - wait: { continue_on_failure: true }
  
  ------------------------------------------------------------------

  EOF
  exit
fi

echo "--- BEGIN $0 $*"

# Check to see if step has already been done successfully

step=cadence-innovus-postroute_hold
if (make -n $step |& grep 'Nothing to be done'); then
    echo "+++ STEP '$step' ALREADY COMPLETED"
    echo "Looks like this step has already been completed successfully"
    echo "If you want to rerun, you'll need to delete or rename it."
    exit
fi

# Rename existing (presumably failed) step if one exists

stepdir=*-$step
if test -e $stepdir; then
    echo "+++ RENAMING FAILED STEP"
    echo "Looks like a failed step '*-$step' exists already"
    for i in 0 1 2 3 4 5 6 7 8 9; do
        cand=${stepdir}-$i
        if ! test -e $cand; then
            echo "Renaming '$stepdir' => '$cand'"
            mv $stepdir $cand
            break
        fi
    done
    if test -e $stepdir; then 
        echo 'Too many renames'; exit 13
    fi
fi



# Little sanity check; list all the steps that will be taken.

echo "+++ TODO LIST"
function make-n-filter { egrep '^mkdir.*output' | sed 's/output.*//' | egrep -v ^Make ;}
make -n cadence-innovus-postroute_hold |& make-n-filter

########################################################################
# Start a background process to watch for hung job(s)
########################################################################

# Define the watcher, watches for 'slow or hanging' jobs warning
# Also see ~steveri/0notes/vto/qrc-slow-or-hanging.txt
# TODO? Could be separate script 'hang-watcher.sh'?

function watch_for_hang {
    # sleep_period=1 ;  # Every second for testing
    sleep_period=750; # Check every fifteen minutes I guess
    while [ true ]; do
        tag="HANG MONITOR $(date +%H:%M)" ; # per-loop tag

        # grep -l:
        #   Suppress normal output; instead print the name of each matching file.
        #   Scanning stops on the first match [for each file?].

        hunglogs=$(grep -ls 'slow or hanging' *postroute_hold/qrc*.log)
        for log_name in $hunglogs; do

            echo "$tag Found slow hanging log '$log_name'"
            echo $tag $log_name
            
            # Find innovus process id where 
            # e.g. if log_name=qrc_6717_20210326_21:19:09.log then pid=6717
            pid=$(echo $log_name | sed 's/^qrc_//' | sed 's/_.*//')
            echo "$tag process id=? $pid ?"
            echo "$tag found hung process $pid"

            # See if process exists (still)
            ps -p $pid || continue
            
            # Found a hung process; now kill it
            echo "Process $pid is (still) valid / running"
            echo ""
            echo 'List of hung processes dependent on $pid'
            echo 'ps -xo "%p %P %y %x %c" --sort ppid | grep $pid'
            ps -xo "%p %P %y %x %c" --sort ppid | grep $pid
            echo ""
            echo "$tag KILL $pid !"
            echo "kill $pid"
            kill $pid
            echo "$tag DONE"
            return
        done
        echo $tag No slow hangers yet...; sleep $sleep_period; continue
    done
}

# Launch the watcher
watch_for_hang |& tee -i hang-watcher.log &

########################################################################
# Run the step.
########################################################################

# - 'exit 13' prevents hang at prompt on innovus failure
# - '||' prevents exit on error
# - ENDSTATUS notification lets us process errors later
# echo "--- restore-design and setup-session"; # set -o pipefail;

echo "--- MAKE CADENCE-INNOVUS-POSTROUTE_HOLD"
echo exit 13 | make cadence-innovus-postroute_hold \
    && echo ENDSTATUS=PASS || echo ENDSTATUS=FAIL

########################################################################
# Kill hang-watcher; specifically, kill its dangling "tee" job
########################################################################
# 
# Want to kill BOTH jobs 19769 and 19772
# ------------------------------------------------------------------
# % jobs -l | sed 's/^/X/'
# X[1]+ 19769 Running                 watch_for_hang 2>&1
# X     19772                       | tee -i hang-watcher.log &
# ------------------------------------------------------------------

echo "--- KILL HANGWATCHER"
[ $DBG ] && (ps ax | grep hang | grep -v grep)
[ $DBG ] && jobs -l

echo ''
echo "Background jobs to kill:"; jobs -l
echo ''
for j in $(jobs -l | sed 's/^/X/' | awk '{print $2}'); do
  echo -n "kill ${j}..."
  kill $j || echo "no such process but that's okay"
done
# Give em a sec to die
echo ''; sleep 1; echo ''
[ $DBG ] && (ps ax | grep hang | grep -v grep)

########################################################################
# Check to see if succeeded or not
########################################################################

echo "+++ QCHECK: PASS or FAIL?"

# Hung job?
echo ''; echo 'Check for hung job...'
pid=$(grep 'found hung process' hang-watcher.log | awk '{print $NF}')
if [ "$pid" ]; then
    echo "QCHECK PROBLEM: HUNG JOB $pid - FAIL"
    FOUND_ERROR=HUNG; exit 13
else
    echo '...no hung job.'
fi
echo ''

# QRC errors?
logs=$(ls *-cadence-innovus-postroute_hold/qrc*.log)
for log in $logs; do
    echo "Check for QRC error(s) in '$log'"
    egrep '^ Error messages' $log
    n_errors=$(egrep '^ Error messages' $log | awk '{print $NF}')
    echo ''
    for i in $n_errors; do 
        if [ "$i" -gt 0 ]; then 
            echo "QCHECK PROBLEM: QRC ERRORS - FAIL"
            echo "FAILED n_errors, flagging QRC for retry"
            FOUND_ERROR=QRC; exit 13
        fi
    done
done

# Other errors?
echo 'Check for other / unknown error(s)...'
if (grep -v grep $log | grep ENDSTATUS=FAIL); then
    echo "QCHECK PROBLEM: FAILED mflowgen with unknown cause, giving up now"
    FOUND_ERROR=FAIL; exit 13
fi
echo ''

# Done!
echo "QCHECK: NO ERRORS FOUND, HOORAY! - PASS"
echo "Hey looks like we got away with it"

exit 0
