#!/bin/bash
set -eu ; # exit immediately on failure

action=run
[ "$1" == "--help" ] && action=help
[ "$1" == "--test" ] && action=test

if [ "$action" == "run" ]; then
    # E.g.
    #   rundir='/build/gold230/full_chip'
    #    pstep='/build/gold230/full_chip/29-cadence-innovus-postroute_hold'
    rundir=$1
    pstep=$1/*-cadence-innovus-postroute_hold

    function build_step {
        echo "steps:"
        echo "- label:   '$1'"
        echo "  command: '$2'"
    }
    if test -e $pstep; then
        echo "# success! hold step '$pstep' already exists."

    elif test -e ${pstep}-fail3; then

        # Failed thrice, that's too many
        build_step "GIVE UP" "exit 13"

    elif test -e ${pstep}-fail2; then

        # Failed twice; final retry
        build_step try3 ".buildkite/bin/prh.sh $rundir else fail3"

    elif test -e ${pstep}-fail1; then

        # Failed once; retry
        build_step try2 ".buildkite/bin/prh.sh $rundir else fail2"

    else

        # First try
        build_step try1 ".buildkite/bin/prh.sh $rundir else fail1"

    fi
    exit
fi


if [ "$action" == "help" ]; then cat<<EOF
# ------------------------------------------------------------------
# Usage:
#     prh-onestep.sh <rundir>
#
# Example:
#     prh-onestep.sh /build/gold230/full_chip
#
# Looks for existence of hold step <rundir>/*-cadence-innovus-postroute_hold
#
# if \$step exists, exit without doing anything
# 
# if \${step}-fail2 exists, build step to do exit 13 w/ label "GIVE UP" maybe
#   - label:   "GIVE UP"
#     command: 'exit 13'
# 
# if \${step}-fail1 exists, build step to run "prh.sh <rundir> else fail2" (I think)
#   - label:   prh-try2
#     command: '.buildkite/bin/prh.sh <rundir> else fail2'
# 
# else build step to run "prh.sh <rundir> else fail1" (I think)
#   - label:   prh-try1
#     command: '.buildkite/bin/prh.sh /build/gold230/full_chip else fail1'
#
# ------------------------------------------------------------------
# "prh.sh <rundir> else fail1" should do something like this:
#    - <rundir> should exist already from prev steps
#    - step *-postroute_hold should not exist yet
#    - build step=*-postroute_hold and check for errors
#    - if build succeeds, we're done
#    - if build fails, rename \$step => "\$step-<failname>"
# 
# ------------------------------------------------------------------
# Final directory structure should look something like this:
# 
#   % ls -1d /build/gold230/*postroute_hold
#       29-cadence-innovus-postroute_hold
#       29-cadence-innovus-postroute_hold-fail1
# 
# Worst case:
# 
#   % ls -1d /build/gold230/*postroute_hold
#       29-cadence-innovus-postroute_hold-fail1
#       29-cadence-innovus-postroute_hold-fail2
#       29-cadence-innovus-postroute_hold-fail3
# 
# ------------------------------------------------------------------
# Call this script with something like
# 
#    env:
#        BUILDPIPE : ".buildkite/prh-onestep.sh /build/gold230/full_chip"
# 
#    steps:
#      # postroute_hold attempt 1
#      - command: '\$\$BUILDPIPE | buildkite-agent pipeline upload'
#      - wait: { continue_on_failure: true }
# 
#      # postroute_hold attempt 2
#      - command: '\$\$BUILDPIPE | buildkite-agent pipeline upload'
#      - wait: { continue_on_failure: true }
# 
#      # postroute_hold final attempt
#      - command: '\$\$BUILDPIPE | buildkite-agent pipeline upload'
#      - wait: ~
# 
# ------------------------------------------------------------------
EOF
exit
fi

# UNIT TESTS
if [ "$action" == "test" ]; then 

    tmpdir=/tmp/deleteme.prh-onstep-tests.$$
    function do_test {
        echo "-------------------------------------------------------------"
        echo "Contents of build dir '$tmpdir'"
        contents=$(cd $tmpdir; ls -1 | sed 's/^/    /')
        [ "$contents" ] || contents="    <empty>"
        echo "$contents"
        echo ""
        $0 $tmpdir
        echo ""
        /bin/rm -rf $tmpdir/*
    }
    ########################################################################
    # success! no need to do anything more
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold
    do_test

    ########################################################################
    # - label:   'try1'
    #   command: '.buildkite/bin/prh.sh $tmpdir else fail1'
    do_test

    ########################################################################
    # - label:   'try2'
    #   command: '.buildkite/bin/prh.sh $tmpdir else fail2'
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold-fail1
    do_test

    ########################################################################
    # - label:   'try3'
    #   command: '.buildkite/bin/prh.sh $tmpdir else fail3'
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold-fail1
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold-fail2
    do_test

    ########################################################################
    # success! no need to do anything more
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold-fail1
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold-fail2
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold
    do_test

    ########################################################################
    # - label:   'GIVE UP'
    #   command: 'exit 13'
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold-fail1
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold-fail2
    mkdir -p $tmpdir/29-cadence-innovus-postroute_hold-fail3
    do_test



    /bin/rm -rf $tmpdir
fi
