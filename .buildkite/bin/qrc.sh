#!/bin/bash

# Helper script for the process of running postroute_hold step ten
# times in a row to try and see how often QRC fails.
# 
# Designed to be called from a buildkite yml script something like:
# 
#     env:
#       QRC : ".buildkite/bin/qrc.sh /build/qtry${BUILDKITE_BUILD_NUMBER}"
#     
#     steps:
# 
#     - label:    'qrc0'
#       commands:
#       - set -x; ${QRC}-0a || ${QRC}-0b || ${QRC}-0c
# 
#     - label:    'qrc1'
#       commands:
#       - set -x; ${QRC}-1a || ${QRC}-1b || ${QRC}-1c
# 
# If all goes well, builds a single dir e.g. '/build/qtry3574-0a'
# Otherwise, can retry up to two more times, in e.g.
#   '/build/qtry3574-0b' and '0c' respectively
# 
# Assumes a lot of assume-o's

# Cached design for postroute_hold inputs lives here
# REF=/sim/buildkite-agent/gold ; # no good, may have wrong numberings
REF=/build/gold.228

# Results will go to dirs e.g. /build/qtry.3549-{0,1,2,3,4,5,6,7,8,9}{a,b,c}
DESTDIR=$1

set -x
  mkdir -p $DESTDIR
set +x

# What the *hell* is this?
# Tee stdout to a log file 'make-qrc.log'
exec > >(tee -i $DESTDIR/make-qrc.log) || exit 13
exec 2>&1 || exit 13

# Set up the environment for the run
source mflowgen/bin/setup-buildkite.sh --dir $DESTDIR --need_space 1G;
mflowgen run --design $GARNET_HOME/mflowgen/full_chip;

# Build necessary dirs and link to cached info
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
# Until we can fix mflowgen repo, will need to fix main.tcl here.
# Mainly changing multi-cpu from 16 back to 8.

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
# Also see ~steveri/0notes/vto/qrc-slow-or-hanging.txt
function watch_for_hang {
    # sleep_period=1 ;  # Every second for testing
    sleep_period=750; # Check every fifteen minutes I guess
    while [ true ]; do
        tag="HANG MONITOR $(date +%H:%M)" ; # per-loop tag

        # grep -l
        #   Suppress normal output; instead print the name of each matching file.
        #   Scanning stops on the first match [for each file?].

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

# # Kill all background jobs (i.e. the watcher) when this script exits
# # (May not be strictly necessary...?)
# trap '
#   echo ""
#   echo "kill hung jobs"
#   sleep 1; # Wait a sec, see if they die on their own
#   [ "$(jobs -p)" ] && echo "no hung jobs to kill"
#   [ "$(jobs -p)" ] && kill $(jobs -p)
# ' EXIT

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

# Hung job
echo ''
echo 'Check for hung job'
pid=$(grep 'found hung process' hang-watcher.log | awk '{print $NF}')
if [ "$pid" ]; then
    echo "+++ QCHECK PROBLEM: HUNG JOB $pid"
    FOUND_ERROR=HUNG
    exit 13
fi

# Other QRC problems
echo ''
echo 'Check for QRC error(s)'
echo "egrep '^ Error messages'" qrc*.log
egrep '^ Error messages' qrc*.log
n_errors=$(egrep '^ Error messages' mflowgen-run.log | awk '{print $NF}')
for i in $n_errors; do 
    if [ "$i" -gt 0 ]; then 
        echo ''
        echo "+++ QCHECK PROBLEM: QRC ERRORS"
        echo "FAILED n_errors, flagging QRC for retry"
        FOUND_ERROR=QRC
        exit 13
    fi
done

# Unknown error
echo ''
echo 'Check for other / unknown error(s)'
if grep ENDSTATUS=FAIL mflowgen-run.log; then
    echo "+++ QCHECK: FAILED mflowgen with unknown cause, giving up now"
    FOUND_ERROR=FAIL
    exit 13
fi

# Huh, must have passed.
echo "+++ QCHECK: NO ERRORS FOUND, HOORAY!"
echo "+++ PASSED mflowgen first attempt"
echo "Hey looks like we got away with it"

# Clean up
echo ''
echo "--- save disk space, delete output design (?)"
set -x
ls -lR checkpoints/
/bin/rm -rf checkpoints/*
touch checkpoints/'deleted to save space'



########################################################################
# TRASH, see qrc.sh.trash, savedir/qrc*


