#!/bin/bash

# TODO SOMEDAY maybe: make it generic e.g.
# make cadence-innovus-postroute_hold | check-for-qrc-errors.sh || rename-for-failure

if [ "$1" == "--help" ]; then cat << '  EOF' | sed 's/^  //'
  Usage:
      prh.sh <rundir>

  Example:
      prh.sh /build/gold230/full_chip

  Summary:
      Runs postroute_hold step and checks for errors.
      On error, renames e.g. "*postroute_hold" => "*postroute_hold.fail1"

  Details:
  - Logs output to ./make-prh.log; if log exists already, rename it.

  - If <rundir> does not exist, create <rundir> along with sufficient
    context to run postroute_hold by linking to gold dir steps
        *-cadence-innovus-postroute
        *-cadence-innovus-flowsetup
  
  - cd to <rundir> and look for existence of step "postroute_hold".
  
  - If step exists, we're done, exit without doing anything (step already passed).
  
  - If step does not exist (yet), do "make postroute_hold"
  
  - On failure, copy logs to postroute_hold/ directory and rename
    postroute_hold => postroute_hold-fail1 or {fail2,fail3...} as appropriate.
  
  Final directory structure should look something like this
  (failed twice, then passed):
  
    % ls -1 /build/gold230/full_chip
        29-cadence-innovus-postroute_hold-fail1
        29-cadence-innovus-postroute_hold-fail2
        29-cadence-innovus-postroute_hold
  
  ------------------------------------------------------------------
  Example buildkite pipeline usage (three strikes you're out):
  
     env:
         PRH : "set -o pipefail; .buildkite/prh.sh /build/gold230/full_chip"
  
     steps:
       # postroute_hold attempt 1
       - command: '\$\$PRH |& tee make-prh.log0'
       - wait: { continue_on_failure: true }
  
       # postroute_hold attempt 2
       - command: '\$\$PRH |& tee make-prh.log1'
       - wait: { continue_on_failure: true }
  
       # postroute_hold final attempt
       - command: '\$\$PRH |& tee make-prh.log2'
       - wait: ~
  
  ------------------------------------------------------------------

  EOF
  exit
fi

echo "--- BEGIN '$*'"

########################################################################
# Find build directory $rundir
########################################################################

# Use existing <rundir> or build new?

rundir=$1
USE_CACHE=
if test -e "$rundir"; then
    echo "--- Using existing context in '$rundir'"
else
    echo "--- Will build '$rundir' using cached context from '$REF'"
    set -x; mkdir -p $rundir; set +x
    USE_CACHE=true
fi
cd $rundir

# If step exists already, exit without error

pstep=$1/*-cadence-innovus-postroute_hold
if test -e $pstep; then
    echo "--- Success! hold step '$pstep' already exists."
    exit 0
fi

########################################################################
# Log file make-prh.log
########################################################################

# Find an unused log name in case we need it.
for i in 0 1 2 3 4 5 6 7 8 9; do
    # Stop at first unused logfile name
    test -e make-prh-$i.log || break
done

# If log file exists already, rename it
test -e make-prh.log && mv make-prh.log make-prh-$i.log

# Tee stdout to a log file 'make-prh.log'
# (Maybe smart. Maybe not smart. But imma do it anyway.)
# First exec sends stdout to log file i guess?
# Second exec sends stderr to stdout i guess?
exec > >(tee -i ./make-qrc.log) || exit 13
exec 2>&1 || exit 13

########################################################################
# Setup
########################################################################

# Set up the environment for the run

echo "--- source mflowgen/bin/setup-buildkite.sh"
source mflowgen/bin/setup-buildkite.sh --dir $rundir --need_space 1G;
mflowgen run --design $GARNET_HOME/mflowgen/full_chip;

echo "--- CONTINUE '$*'"

# Build context from cache if none exists yet

if [ "$USE_CACHE" == 'true' ]; then

    # Build the necessary context to run postroute_hold step only.
    # Want two steps
    #     *-cadence-innovus-postroute
    #     *-cadence-innovus-flowsetup

    REF=/sim/buildkite-agent/gold
    $GARNET_HOME/mflowgen/bin/get-step-context.sh $REF || exit 13

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
# DO IT MAN! Run the step.
########################################################################

# - 'exit 13' prevents hang at prompt on innovus failure
# - '||' prevents exit on error
# - ENDSTATUS notification lets us process errors later
# echo "--- restore-design and setup-session"; # set -o pipefail;

echo "--- MAKE CADENCE-INNOVUS-POSTROUTE_HOLD"
echo exit 13 | make cadence-innovus-postroute_hold \
    && echo ENDSTATUS=PASS || echo ENDSTATUS=FAIL

########################################################################
# Check to see if succeeded or not
########################################################################

echo "+++ QCHECK: PASS or FAIL?"
pwd

# Could alternatively do this with a trap i guess...
function rename_and_exit {
    # Examples:
    #    rename_and_exit PASS
    #    rename_and_exit FAIL

    if [ "$1" == "PASS" ]; then
        exit 0
    else

        # Step failed; rename it to <step>-<failname> e.g.
        # "29-cadence-innovus-postroute_hold-fail1"

        step=`echo *cadence-innovus-postroute_hold | head -1`
        if ! test -e $step; then
            echo "ERROR cannot find step '$step'"
            exit 13
        fi

        # Find next unused fail extension -fail1, -fail2, -fail3 etc.
        # Note: if fail9 exists, we probably get an error on the "mv"
        for failnum in 1 2 3 4 5 6 7 8 9; do
            (ls -d ${step}-fail${failnum} >& /dev/null) || break
        done

        set -x ; # Make a record of the final actions

        # Move logs to (failed) step dir
        mv make-prh.log $step; mv hang-watcher.log $step

        # Rename step dir with failure extension e.g. 'fail1' or 'fail2'
        mv ${step} ${step}-fail${failnum}

        # Show failures so far and error out.
        /bin/ls -1d ${step}*
        exit 13
    fi
}

echo ''; echo 'Check for hung job'
pid=$(grep 'found hung process' hang-watcher.log | awk '{print $NF}')
if [ "$pid" ]; then
    echo "QCHECK PROBLEM: HUNG JOB $pid - FAIL"
    FOUND_ERROR=HUNG
    rename_and_exit FAIL
fi

echo ''; echo "Check for QRC error(s) in '$log'"
log='make-prh.log'
egrep '^ Error messages' $log
n_errors=$(egrep '^ Error messages' $log | awk '{print $NF}')
for i in $n_errors; do 
    if [ "$i" -gt 0 ]; then 
        echo ''
        echo "QCHECK PROBLEM: QRC ERRORS - FAIL"
        echo "FAILED n_errors, flagging QRC for retry"
        FOUND_ERROR=QRC
        rename_and_exit FAIL
    fi
done

echo ''; echo 'Check for other / unknown error(s)'
if (grep -v grep $log | grep ENDSTATUS=FAIL); then
    echo "QCHECK PROBLEM: FAILED mflowgen with unknown cause, giving up now"
    FOUND_ERROR=FAIL
    rename_and_exit FAIL
fi

echo "QCHECK: NO ERRORS FOUND, HOORAY! - PASS"
echo "Hey looks like we got away with it"

########################################################################
# Post-mortem
########################################################################

echo ""; echo "How many tries did it take?"
# E.g.
#       29-cadence-innovus-postroute_hold
#       29-cadence-innovus-postroute_hold-fail1
#       29-cadence-innovus-postroute_hold-fail2
/bin/ls -1 | grep cadence-innovus-postroute_hold; echo ''

echo ""; echo "What happened?"
# E.g.
#     make-prh.log - QCHECK: NO ERRORS FOUND, HOORAY! - PASS
#     make-prh-fail1.log - QCHECK: NO ERRORS FOUND, HOORAY! - PASS
#
egrep -H '^QCHECK.*(PASS|FAIL)$' make-prh*.log | sed 's/:/ - /'


########################################################################
# DONE!
########################################################################

rename_and_exit PASS
