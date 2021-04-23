#!/bin/bash

# TODO SOMEDAY maybe: make it generic e.g.
# make cadence-innovus-postroute_hold | check-for-qrc-errors.sh || rename-for-failure

if [ "$1" == "--help" ]; then cat << '  EOF' | sed 's/^  //'
  Usage:
      qrc.sh <rundir>

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

# If step exists already, exit without error

pstep=$rundir/*-cadence-innovus-postroute_hold
if test -e $pstep; then
    echo "--- Success! hold step '$pstep' already exists."
    exit 0
fi

########################################################################
# Log file make-prh.log
########################################################################

# Tee stdout to a log file 'make-prh.log'
# (Maybe smart. Maybe not smart. But imma do it anyway.)

# If log file exists already, rename it
if test -e make-prh.log; then
    for i in 0 1 2 3 4 5 6 7 8 9; do
        test -e make-prh-$i.log || break
    done
    mv make-prh.log make-prh-$i.log
fi

# First exec sends stdout to log file i guess?
# Second exec sends stderr to stdout i guess?
exec > >(tee -i $rundir/make-prh.log) || exit 13
exec 2>&1 || exit 13

########################################################################
# Setup
########################################################################

# Set up the environment for the run

echo "--- source mflowgen/bin/setup-buildkite.sh"
source  mflowgen/bin/setup-buildkite.sh --dir $rundir --need_space 1G;
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

# okay now
$GARNET_HOME/.buildkite/bin/prh.sh && RESULT=PASS || RESULT=FAIL


echo "+++ QCHECK: PASS or FAIL?"

if [ "$RESULT" == "PASS" ]; then

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
    
    exit 0
fi
    
if [ "$RESULT" == "FAIL" ]; then
    
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

