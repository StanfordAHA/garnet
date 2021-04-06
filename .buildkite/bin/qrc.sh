#!/bin/bash

# Helper script for the process of running postroute_hold step ten
# times in a row to try and see how often QRC fails.
# 
# Designed to be called from a buildkite yml script something like:
# 
#     env:
#       DESTDIR : /build/qtry${BUILDKITE_BUILD_NUMBER}
# 
#     steps:
# 
#     - label:    'qrc0'
#       commands: '.buildkite/bin/qrc.sh $${DESTDIR}-0'
#     - wait:     { continue_on_failure: true }
#     
#     - label:    'qrc1'
#       commands: '.buildkite/bin/qrc.sh $${DESTDIR}-1'
#     - wait:     { continue_on_failure: true }
# 
#     ...
#     
#     - label:    'qrc9'
#       commands: '.buildkite/bin/qrc.sh $${DESTDIR}-9'
#     - wait:     { continue_on_failure: true }
# 
# Assumes a lot of assume-o's

# Cached design for postroute_hold inputs lives here
REF=/build/gold.228

echo $1; exit

# Results will go to dirs e.g. /build/qtry.3549-{0,1,2,3,4,5,6,7,8,9}
DESTDIR=$1


# DESTDIR=/build/qtry.${BUILDKITE_BUILD_NUMBER}
# 
# for i in 0 1 2 3 4 5 6 7 8 9; do
#     if ! test -e ${DESTDIR}-$i; then
#         DESTDIR=${DESTDIR}-$i
#         break
#     fi
# done

set -x
  mkdir -p $DESTDIR
set +x

# Tee stdout to a log file
exec > >(tee -i $DESTDIR/make-qrc.log) || exit 13
exec 2>&1 || exit 13


source mflowgen/bin/setup-buildkite.sh --dir $DESTDIR --need_space 1G;
mflowgen run --design $GARNET_HOME/mflowgen/full_chip;

echo "--- QRC TEST RIG SETUP - copy/link cached info";
set -x;

    ln -s $REF/full_chip/12-tsmc16;
    ln -s $REF/full_chip/20-cadence-innovus-flowsetup;
    ln -s $REF/full_chip/28-cadence-innovus-postroute;

    step=cadence-innovus-postroute_hold;

    mkdir -p 29-${step}; cd 29-${step};

    d=$REF/full_chip/*-${step};

    # log dir
    mkdir -p logs; mkdir -p outputs

    # symlinks
    cp -rp $d/innovus-foundation-flow         . ;

    # plain files
    cp -p $d/mflowgen-check-postconditions.py . ;
    cp -p $d/mflowgen-check-preconditions.py  . ;
    cp -p $d/mflowgen-debug                   . ;
    cp -p $d/mflowgen-run                     . ;
    cp -p $d/configure.yml                    . ;
    cp -p $d/START.tcl                        . ;

    # dirs
    cp -rp $d/inputs  . ;
    cp -rp $d/scripts . ;
set +x;

echo "--- QRC TEST RIG SETUP - swap in new main.tcl";

########################################################################
# Build a new main.tcl

main_tcl_new='
setOptMode -verbose true

setOptMode -usefulSkewPostRoute true

setOptMode -holdTargetSlack  $::env(hold_target_slack)
setOptMode -setupTargetSlack $::env(setup_target_slack)

puts "Info: Using signoff engine = $::env(signoff_engine)"

if { $::env(signoff_engine) } {
  setExtractRCMode -engine postRoute -effortLevel signoff
}

# SR Mar 2021 changed multiCpuUsage from 16 back to 8.
# It seems to have helped the QRC core-dump problem
# (twenty-ish consecutive runs with no error). Also,
# from Innovus User Guide Product Version 19.10,
# dated April 2019, p. 1057:
# 
# "Generally, performance improvement will start to diminish beyond 8 CPUs."

echo ""
echo "--- BEGIN optDesign -postRoute -hold"
setDistributeHost -local
setMultiCpuUsage -localCpu 8

# Run the final postroute hold fixing
optDesign -postRoute -outDir reports -prefix postroute_hold -hold
'

########################################################################
# Write the new main.tcl

echo "$main_tcl_new" > scripts/main.tcl
echo '=================================================================='
echo 'cat scripts/main.tcl'
cat scripts/main.tcl
echo '=================================================================='

########################################################################
# Define the watcher, watches for 'slow or hanging' jobs warning
function watch_for_hang {
    # sleep_period=1 ;  # Every second for testing
    sleep_period=750; # Check every fifteen minutes I guess
    while [ true ]; do
        tag="HANG MONITOR $(date +%H:%M)" ; # per-loop tag

        # grep -l
        #   Suppress normal output; instead print the name of each input
        #   file from which output would normally have been printed.  The
        #   scanning will stop on the first match.

        hunglogs=$(grep -ls 'slow or hanging' qrc*.log)
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
            echo 'List of hung processes:'
            echo 'ps -xo "%p %P %y %x %c" --sort ppid | grep $pid'
            ps -xo "%p %P %y %x %c" --sort ppid | grep $pid
            echo ""
            echo "$tag KILL AND RESTART $pid !"
            echo "kill $pid"
            kill $pid
            echo "$tag DONE"
            return
        done
        echo $tag No slow hangers yet...; sleep $sleep_period; continue
    done
}

# Kill all background jobs (i.e. the watcher) when this script exits
# (May not be strictly necessary...?)
trap '
  echo ""
  echo "kill hung jobs"
  sleep 1; # Wait a sec, see if they die on their own
  [ "$(jobs -p)" ] && echo "no hung jobs to kill"
  [ "$(jobs -p)" ] && kill $(jobs -p)
' EXIT

# Launch the watcher
watch_for_hang |& tee -i hang-watcher.log &

########################################################################
# DO IT MAN! Run the step.

function RUN_THE_STEP {
    # Executes mflowgen-run, which basically does 
    # - 'exit 13' prevents hang at prompt on innovus failure
    # - '||' prevents exit on error
    # - ENDSTATUS notification lets us process errors later
    # echo "--- restore-design and setup-session"; # set -o pipefail;
    echo "--- DO MFLOWGEN-RUN"
    echo exit 13 | ./mflowgen-run && echo ENDSTATUS=PASS || echo ENDSTATUS=FAIL
}
RUN_THE_STEP |& tee -i mflowgen-run.log


########################################################################
echo "+++ QCHECK: PASS or FAIL?"

# If we reach this point, then one of three things has happened:
#   1. watcher detected slow hanger and killed the innovus job
#      (which I think results in ENDSTATUS=PASS(?))
#   2. qrc died, resulting in ENDSTATUS=FAIL
#   3. job succeeded w/ENDSTATUS=PASS








########################################################################
########################################################################
echo "+++ QCHECK QRC CHECK"

# If we reach this point, then one of three things has happened:
#   1. watcher detected slow hanger and killed the innovus job
#      (which I think results in ENDSTATUS=PASS(?))
#   2. qrc died, resulting in ENDSTATUS=FAIL
#   3. job succeeded w/ENDSTATUS=PASS

# Set FOUND_ERROR to
#     "NONE" : no errors found
#     "FAIL" : innovus failed, don't know why
#     "HUNG" : qrc stopped with hanged-jog warning
#     "QRC"  : qrc flagged one or more errors


########################################################################
# Set to FAIL if ENDSTATUS=FAIL
if   grep ENDSTATUS=FAIL mflowgen-run.log; then FOUND_ERROR=FAIL
else grep ENDSTATUS mflowgen-run.log;           FOUND_ERROR=NONE
fi

########################################################################
# Check for hung job (less likely error cause)
echo ''
echo 'Check for hung job'
pid=$(grep 'found hung process' hang-watcher.log | awk '{print $NF}')
if [ "$pid" ]; then
    echo "+++ QCHECK PROBLEM: HUNG JOB"
    FOUND_ERROR=HUNG
    echo "oooo looks like the job got hunged"
    echo "hunged job was number $pid maybe"
    echo 'hang watcher should have killed the hung job by now'
    echo "ps --pid=$pid"
    ps --pid=$pid  || echo 'yep looks like hanged job was killed okay'
    echo "should we retry???"


#     echo "if we were brave this is where we would do this:"
#     echo "kill -9 $pid"
#     echo "and then we'd initiate a retry, see below"
#     echo "but for now we gonna err out"
    # exit 13
    # FIXME/TODO: Check to see if job is really hung (how??)


########################################################################
# Override "FAIL" w/ "QRC" if find specific qrc errors (most likely error cause)
else
    echo ''
    echo "egrep '^ Error messages'" qrc*.log
    egrep '^ Error messages' qrc*.log
    n_errors=$(egrep '^ Error messages' mflowgen-run.log | awk '{print $NF}')
    for i in $n_errors; do 
        if [ "$i" -gt 0 ]; then 
            echo ''
            echo "+++ QCHECK PROBLEM: QRC ERRORS"
            echo "FAILED n_errors, flagging QRC for retry"
            FOUND_ERROR=QRC
            break
        fi
    done
fi

##################################################################
# Process FOUND_ERROR codes, retry if warranted

function cleanup {
    echo "--- save disk space, delete output design (?)"
    set -x
    ls -lR checkpoints/
    /bin/rm -rf checkpoints/*
    touch checkpoints/'deleted to save space'
}

if [ "$FOUND_ERROR" == "NONE" ]; then
    echo "+++ QCHECK: NO ERRORS FOUND, HOORAY!"
    echo "+++ PASSED mflowgen first attempt"
    echo "Hey looks like we got away with it"
    cleanup; exit

elif [ "$FOUND_ERROR" == "QRC" ]; then
    echo ''
    echo "Looks like QRC failed, will attempt one retry"
    echo "+++ QCHECK PROBLEM: INITIATING RETRY"

elif [ "$FOUND_ERROR" == "HUNG" ]; then
    echo "TBD (not ready to retry on this error yet)"
    echo "For now, this should have resulted in 'exit 13' above"
    echo "ERROR should never be here (for now)!"
    exit 13

elif [ "$FOUND_ERROR" == "FAIL" ]; then
    echo "Looks like innovus failed, dunno why"
    echo "Will attempt one retry anyway"

else
    echo "ERROR unknown code, should never be here!"
    exit 13
fi

########################################################################
# If we get this far, need a retry
echo "--- FAILED first attempt, going for a retry"
RUN_THE_STEP |& tee -i mflowgen-run-retry.log

if grep ENDSTATUS=FAIL mflowgen-run-retry.log; then
    echo "+++ QCHECK: FAILED mflowgen retry, giving up now"
    # My attempt at fflush(stdout) :(
    stdbuf -oL echo exit 13; stdbuf -o0 echo exit 13
    exit 13

else
    echo "+++ QCHECK RETRY: PASSED mflowgen retry, hooray I guess"
    cleanup; exit

fi

exit

########################################################################
# TRASH, see qrc.sh.trash


