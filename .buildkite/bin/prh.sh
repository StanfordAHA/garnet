#!/bin/bash

########################################################################
# Helper script for running postroute_hold standalone.
# Renames build dir with "pass" or "fail" extensions.
# 
# Usage:   "prh.sh <DESTDIR> else <failname>"
# Example: "prh.sh /build/prh3647/run0 else fail1"
# 
# - If <DESTDIR> does not exist, creates <DESTDIR> along with sufficient
#   context to run postroute_hold by linking to gold dir steps
#       *-cadence-innovus-postroute
#       *-cadence-innovus-flowsetup
# 
# - Otherwise, assumes context already exists
# 
# - Runs 'make postroute_hold' and checks for failure
# 
# - Records progress in make-prh.log file
# 
# - On failure, renames postroute_hold dir according to "else" cmd-line
#   parm e.g. "29-cadence-innovus-postroute_hold-fail1"
# 
# - Designed to be called from a buildkite yml script something like:
#       - command: 'prh.sh /build/gold230 else fail2'
# 
# Final directory structure should look something like this
# (failed twice, then passed):
# 
#   % ls -1 /build/gold230
#       29-cadence-innovus-postroute_hold-fail1
#       29-cadence-innovus-postroute_hold-fail2
#       29-cadence-innovus-postroute_hold

########################################################################
# Setup
########################################################################
echo "--- BEGIN $*"

# Cached design for postroute_hold inputs lives here
REF=/sim/buildkite-agent/gold

# Examples:
#    prh.sh /build/gold230      else fail1
#    prh.sh /build/prh3647/run0 else fail2
# 
# Build postroute_hold step in designated dir e.g. /build/qrh3549/run0
# On failure, rename curdir to <curdir>-$failname
DESTDIR=$1
failname=$3

# Use existing or build new?
if test -e "$DESTDIR"; then
    echo "--- Using existing context in '$DESTDIR'"
    USE_CACHE=
else
    echo "--- Building '$DESTDIR' using cached context from '$REF'"
    set -x; echo mkdir -p $DESTDIR; set +x
    USE_CACHE=true
fi

# Avoid collisions
if test -e make-prh.log; then
    for failno in 1 2 3 4 5 6 7 8 9; do
        if ! test -e make-prh-fail{$i}.log; then
            mv make-prh.log make-prh-fail{$i}.log
            break
        fi
    done
fi

# Replace current process image with one that tees output to log file
exec > >(tee -i $DESTDIR/make-prh.log) || exit 13

# Replace (new) current process image with one that sends stderr to stdout
exec 2>&1 || exit 13

# Set up the environment for the run
source mflowgen/bin/setup-buildkite.sh --dir $DESTDIR --need_space 1G;
mflowgen run --design $GARNET_HOME/mflowgen/full_chip;

if [ "$USE_CACHE" == 'true' ]; then

    # Build the necessary context to run postroute_hold step only.
    # Want two steps
    #     *-cadence-innovus-postroute
    #     *-cadence-innovus-flowsetup

    $GARNET_HOME/mflowgen/get-step-context.sh
fi

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

        # grep -l
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
########################################################################

function RUN_THE_STEP {
    # Executes mflowgen-run, which basically does 
    # - 'exit 13' prevents hang at prompt on innovus failure
    # - '||' prevents exit on error
    # - ENDSTATUS notification lets us process errors later
    # echo "--- restore-design and setup-session"; # set -o pipefail;


    # echo "--- DO MFLOWGEN-RUN"
    # echo exit 13 | ./mflowgen-run && echo ENDSTATUS=PASS || echo ENDSTATUS=FAIL

    echo "--- MAKE CADENCE-INNOVUS-POSTROUTE_HOLD"

    echo exit 13 | make cadence-innovus-postroute_hold \
        && echo ENDSTATUS=PASS || echo ENDSTATUS=FAIL

}
RUN_THE_STEP |& tee -i make-prh.log

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
    #     
    # If step failed, rename it to <step>-<failname> e.g.
    # "29-cadence-innovus-postroute_hold-fail1"
    result=$1
    step=`echo *cadence-innovus-postroute_hold`; echo $step
    if [ "$result" == "PASS" ]; then
        exit 0
    else
        set -x; mv ${step} ${step}-$failname; /bin/ls -1; exit 13
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
/bin/ls -1 | grep make-prh

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



# (exit 0)

#OLD
# 
# notes="
#   E.g. prh.sh /build/prh3555/run0 does this:
# 
#     # build and run in dir rundir=/build/prh3555/run0
#     if PASS then mv $rundir ${rundir}-pass
#     else for i in 1 2 3 4 5 6 7 8 9; do
#       failname=${rundir}-fail$i
#       if ! -e $failname; then mv $rundir $failname; break; fi
#     fi
# "

# "prh.sh /build/prh3555/run2 else fail1" should do something like this:
#  - build new dir "/build/prh355/run2" and run qrc
#  - if prc succeeds, rename "/build/prh355/run2" => "/build/prh355/run2-pass
#  - if prc fails, rename "/build/prh355/run2" => "/build/prh355/run2-fail1"
# 



# # if DESTDIR exists, copy e.g. "/build/prh3647/run0" to "/build/prh3647/run0.fail1"
# if test -e $DESTDIR; then
#     echo "Found already-existing build dir '$DESTDIR'"
#     echo "Assume it's a fail; look for a place to stash it"
#     for i in 1 2 3 4 5 6 7 8 9; do
#         nextfail=$DESTDIR.fail$i
#         test -e $nextfail || break
#     done
#     echo "Found candidate fail dir name '$nextfail'"
#     set -x; mv $DESTDIR $nextfail; set +x
# fi







##############################################################################
##############################################################################
##############################################################################


# echo "+++ continue"

# echo "+++ PRH TEST RIG SETUP - stash-pull context from $GOLD";
# $GARNET_HOME/.buildkite/bin/prh-setup.sh $GOLD || exit 13

# # See if things are okay so far...
# echo CHECK1
# echo pwd=`pwd`
# /bin/ls -1
# echo ''


# echo "--- QRC TEST RIG SETUP - swap in new main.tcl";
# echo "temporarily changed setup-buildkite.sh to use mfg branch 'qrc-crash-fix'"
# echo '========================================================================'
# echo '========================================================================'
# echo '========================================================================'
# set -x
#   (cd ../mflowgen; git branch) || echo nope
#   cat ../mflowgen/steps/cadence-innovus-postroute_hold/scripts/main.tcl || echo nope
# set +x
# echo '========================================================================'
# echo '========================================================================'
# echo '========================================================================'


#     if [ "$exit_status" == "PASS" ]; then
#         # If running standalone, rename top-level dir with "pass"
#         # New regime means no rename
#         # set -x; mv $d ${d}-pass     ; /bin/ls -1; exit 0
#         exit 0
#     else
#         set -x; mv $d ${d}-$failname; /bin/ls -1; exit 13
#     fi


# 
# #   /build/prh3658/run0
# #   /build/prh3658/run0.fail1
# dirs=`pwd`*
# 
# # E.g. output=
# # /build/prh3658/run0:
# #    QCHECK: NO ERRORS FOUND, HOORAY! - PASS"
# echo ''
# for d in $dirs; do
#     echo "${d}:"
#     echo -n '    '
#     egrep '^QCHECK.*(PASS|FAIL)$' ${d}*/make-prh.log
#     # egrep '^\+++ QCHECK.*PASS' $d/make-prh.log
# done


# ########################################################################
# # TO TEST: Move this code to the top and set TEST_ONLY=true
# TEST_ONLY=
# if [ "$TEST_ONLY" ]; then
#     # for i in 1 2 3 4 5 6 7 8 9 0; do
#     # Create dirs; fail or pass at random dice roll
#     rundir=$1; failname=$3
#     [ "$rundir" ] || exit 13
#     ls -1 ${rundir}*/..
# 
#     # Odd runs pass, even runs fail
#     if [ $[RANDOM%2] -eq 0 ]; then 
#         echo PASS; 
#         set -x; mkdir -p ${rundir}-pass; set +x
#         ls -1 ${rundir}*/..
#         exit 0;
#     else
#         echo FAIL; 
#         set -x; mkdir -p ${rundir}-${failname}; set +x
#         ls -1 ${rundir}*/..
#         exit 13;
#     fi
#     exit
# done


# echo "+++ CLEAN UP, delete 14G of context"
# 
# # Clean up
# echo ''
# echo "--- save disk space, delete output design (?)"
# if test -d checkpoints; then
#     ls -lR checkpoints/
#     /bin/rm -rf checkpoints/*
#     touch checkpoints/'deleted to save space'
# fi
# echo ''
# 
# echo "--- save disk space, delete copied gold steps"
# prhname=$(/bin/ls -d *postroute_hold); echo $prhname
# for step in $(/bin/ls -d [0-9]*); do
#     if [ "$step" == "$prhname" ]; then
#         echo "SKIP '$prhname' (obviously)"; continue
#     else
#         echo "/bin/rm -rf $step"
#         /bin/rm -rf $step
#     fi
# done

