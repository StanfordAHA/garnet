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

stepdir=`echo *-$step`
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
        set +x
        tag="HANG MONITOR $(date +%H:%M)" ; # per-loop tag

        # grep -l:
        #   Suppress normal output; instead print the name of each matching file.
        #   Scanning stops on the first match [for each file?].

        hunglogs=$(grep -ls 'slow or hanging' *postroute_hold/qrc*.log)
        for log_name in $hunglogs; do

            set -x
            echo "$tag Found slow hanging log '$log_name'"
            echo $tag $log_name
            
            # Find innovus process id where e.g. log_name is 
            # 32-cadence-innovus-postroute_hold/qrc_2934_20210606_01:55:44.log'
            # and so pid=2934
            pid=$(echo $log_name | sed 's/^.*qrc_//' | sed 's/_.*//')
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
            em='!'; echo "$tag KILL $pid$em"
            echo "kill $pid"
            kill $pid
            echo "$tag DONE"

            # But that's not all!
            # QDIR=/cad/cadence/EXT-ISR1_19.11.000_lnx86/tools.lnx86/extraction/bin/64bit
            # ITMP=/sim/tmp/innovus/sim/tmp/innovus
            # CMD1=r7arm-aha_buildkite-agent_MR0fEJ/tmp_qrc_QWq3Uu/qrc.cmd
            # CMD2=r7arm-aha_buildkite-agent_MR0fEJ/tmp_qrc_QWq3Uu/__qrc.qrc.cmd
            # GZ=$ITMP_temp_2934_r7arm-aha_buildkite-agent_MR0fEJ/tmp_qrc_QWq3Uu/qrc.def.gz
            # 24253 pts/17   Sl+    0:13 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD1 $GZ
            # 24461 pts/17   Sl+    0:15 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD2 $GZ
            # 24823 pts/17   Sl+    0:06 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD2 $GZ
            # 25109 pts/17   Sl+    0:06 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD2 $GZ
            # 25594 pts/17   Sl+    0:06 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD2 $GZ
            # 25595 pts/17   Sl+    0:06 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD2 $GZ
            # 25596 pts/17   Sl+    0:06 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD2 $GZ
            # 25597 pts/17   Sl+    0:06 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD2 $GZ
            # 25599 pts/17   Sl+    0:06 $QDIR/qrc -cmd $ITMP_temp_2934_$CMD2 $GZ
            echo "Haha no not even"
            echo "kill dangling qrc -cmd jobs"; echo ""
            ps ax | egrep temp_${pid}_ | grep -v grep
            bad_pids=`ps ax | egrep temp_${pid}_ | grep -v grep | awk '{print $1}'`
            echo kill $bad_pids
            kill $bad_pids; echo ""
            
            # ...and still more processes to kill :(
            # QDIR=/cad/cadence/EXT-ISR1_19.11.000_lnx86/tools.lnx86/extraction/bin/64bit
            # 24360 pts/17   S+     1:20 $QDIR/qrc -srv r7arm-aha 36989 0 -1
            # 24462 pts/17   S+     1:18 $QDIR/qrc -srv r7arm-aha 36989 1 -1
            # 24671 pts/17   S+     1:15 $QDIR/qrc -srv r7arm-aha 36989 2 -1
            # 24824 pts/17   S+     1:16 $QDIR/qrc -srv r7arm-aha 36989 3 -1
            # 25012 pts/17   S+     1:15 $QDIR/qrc -srv r7arm-aha 36989 4 -1
            # 25110 pts/17   S+     1:16 $QDIR/qrc -srv r7arm-aha 36989 5 -1
            # 25286 pts/17   S+     1:15 $QDIR/qrc -srv r7arm-aha 36989 6 -1
            # 25478 pts/17   S+     1:16 $QDIR/qrc -srv r7arm-aha 36989 7 -1
            echo "kill dangling qrc -srv jobs"
            ps x | grep 'qrc..srv'; echo ""
            bad_pids=`ps x | grep 'qrc..srv' | awk '{print $1}'`
            echo kill $bad_pids
            kill $bad_pids; echo ""

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

# If no logs, script hangs forever maybe, because then logs=""
# and "grep $log" waits for stdin at "other errors?" below
if ! test -d *-cadence-innovus-postroute_hold/qrc*.log; then
    echo "ERROR Cannot find QRC logs something must have failed"
    echo "ERROR maybe a lost license like in build 420"
    exit 13
fi

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
