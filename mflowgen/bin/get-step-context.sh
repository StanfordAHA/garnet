#!/bin/bash

if [ "$1" == "--help" ]; then cat <<EOF

USAGE: $0 <refdir> <step>

DESCRIPTION:
Builds symbolic links to the appropriate collateral in reference dir
<refdir> such that you can locally run mflowgen step <step>.

EXAMPLE USE CASE:
Suppose you have a design with multiple mflowgen steps.

A version of the design exists in some directory "/build/chip1",
but now you are putting together a new version "/build/chip2".

You want to reuse the existing chip1 collateral up through step
"cadence-innovus-postroute_hold" and then rerun that step locally.

You can do this:
  % cd /build/chip2
  % get-step-context.sh /build/chip1 cadence-innovus-postroute_hold
  % make *-cadence-innovus-postroute_hold

NOTES:
To use this command, you should be in a valid mflowgen directory with
a Makefile such that "make list" gives a valid list of mflowgen steps.

Linked nodes are renumbered as appropriate to account for changes in
the graph between <refdir> and local dir.

E.g. for <step> = 'cadence-innovus-postroute_hold' it might link
these two steps from <refdir> into current (build) dir

    ln -s ./23-cadence-innovus-flowsetup <refdir>/22-cadence-innovus-flowsetup
    ln -s ./31-cadence-innovus-postroute <refdir>/30-cadence-innovus-postroute

REAL-WORLD EXAMPLE: 
To e.g. run standalone step "cadence-innovus-postroute_hold"
using cached information in refdir "/build/gold":

    1 Build the design framework
    mflowgen run --design $GARNET_HOME/mflowgen/full_chip

    2 Build (link to) standalone context for the build
    get-step-context.sh /build/gold cadence-innovus-postroute_hold

    3 Execute target step "postroute_hold"
    make cadence-innovus-postroute_hold
EOF
exit
fi

if [ "$1" == "--from" ]; then shift; fi
REF=$1

if [ "$2" == "--step" ]; then shift; fi
target_step=$2

# target_step=cadence-innovus-postroute_hold

echo "--- BEGIN $0 $*" | sed "s,$GARNET_HOME,\$GARNET_HOME,"
echo "  where GARNET_HOME=$GARNET_HOME"
echo "+++ STANDALONE TEST RIG SETUP - build symlinks to steps in $REF/full_chip";

########################################################################
########################################################################
########################################################################

function get_predecessors {

    # Example:
    #    get_predecessors cadence-innovus-postroute_hold
    # 
    # Returns predecessor 'cadence-innovus-postroute_hold' nodes:
    #      cadence-innovus-postroute
    #      cadence-innovus-flowsetup
    # 
    # Notes:
    #   - Ignores adk steps because it's better to redo those from scratch.
    #   - Must run in a valid mflowgen design dir i.e. one with a '.mflowgen' subdir.
    #   - Could do "test -e .mflowgen || ERROR"

    target_step=${1} ; # E.g. "rtl"
#     target_step=cadence-innovus-postroute_hold

    stepdir=$(/bin/ls .mflowgen | egrep "^[0-9]*-${target_step}") ; # E.g. "11-rtl"
    config_file=".mflowgen/${stepdir}/configure.yml"

    # Look in config.yml to find this:
    #     edges_i:
    #       adk:
    #       - f: adk
    #         step: 7-freepdk-45nm
    #       design.checkpoint:
    #       - f: design.checkpoint
    #         step: 31-cadence-innovus-postroute
    #       innovus-foundation-flow:
    #       - f: innovus-foundation-flow
    #         step: 23-cadence-innovus-flowsetup
    # 
    # Use that to print this (ignores adk nodes, see?)
    #     cadence-innovus-postroute
    #     cadence-innovus-flowsetup

    (cat $config_file; echo "xxx") | sed -n '/^edges_i/,/^[^ ]/p' \
    | awk '
        $(NF-1) == "f:" { f = $NF }
        f == "adk" { next }
        $1 == "step:" { print $2 }' \
    | sed 's/^[0-9]*[-]//'
}
echo ""; echo "NODE PREDS"
# get_predecessors cadence-innovus-postroute_hold
get_predecessors $target_step
echo ""


DBG=
# for step in cadence-innovus-postroute cadence-innovus-flowsetup; do
for step in `get_predecessors $step`; do

    [ "$DBG" ] && echo Processing step $step

    # Find name of step in local dir; bug out if exists already
    [ "$DBG" ] && (make list |& egrep ": $step\$")
    stepnum=$(make list |& egrep ": $step\$" | awk '{print $2}')
    local_step=$stepnum-$step
    [ "$DBG" ] && (echo "Want local step $local_step"; echo '')
    if test -e $local_step; then
        echo "Looks like '$local_step' exists already"
        echo "Doing nothing for '$local_step'"
        continue
    fi

    # Find name of step in ref dir
    stepnum=$(cd $REF/full_chip; make list |& egrep ": $step\$" | awk '{print $2}')
    ref_step=$REF/full_chip/$stepnum-$step
    [ "$DBG" ] && echo "Found ref step $ref_step"
    if ! test -d $ref_step; then
        echo "hm look like $ref_step don't exist after all..."
        exit 13
    fi

    # Need '.prebuilt' to make it work for some reason...
    [ "$DBG" ] && echo "touch <refdir>/<step>/.prebuilt"
    touch $ref_step/.prebuilt

    # Link local to ref
    [ "$DBG" ] && echo "ln -s $ref_step $local_step"
    ln -s $ref_step $local_step
    echo "$local_step => $ref_step"
    [ "$DBG" ] && echo ''

done
echo ""

echo "+++ READY TO BUILD STANDALONE $target_step"
echo "make -n ${target_step}"
make -n ${target_step} \
  |& egrep "^mkdir.*output" | sed "s/output.*//" | egrep -v ^Make


exit
########################################################################
########################################################################
########################################################################
# To run locally on kiwi can do this:
do_this=OFF
if [ "$do_this" == "ON" ]; then

    # 1. Set up run and ref dirs
    T=/tmp/get-step-context; cd $T
    REFDIR=/build/gold; RUNDIR=$T/full_chip

    # 2. Set up to execute target step in $RUNDIR
    export GARNET_HOME=/nobackup/steveri/github/garnet
    sbk=$GARNET_HOME/mflowgen/bin/setup-buildkite.sh
    source $sbk --dir $RUNDIR |& tee log | less

    # 3. Jimmy up a fake tsmc16 library
    (cd /tmp/steveri/mflowgen.master/adks; ln -s freepdk-45nm tsmc16)

    # 4. Build the design framework
    mflowgen run --design $GARNET_HOME/mflowgen/full_chip

    ### >>> GOOD TO HERE <<< ###

    # 3. Build standalone context and execute target step "postroute_hold"
    mflowgen/bin/get-step-context.sh $REFDIR
    make cadence-innovus-postroute_hold
fi

exit
########################################################################
# Buildkite on arm machine should be able to do this:
do_this=OFF
if [ "$do_this" == "ON" ]; then

    # 1. Set up run and ref dirs
    T=/tmp/get-step-context; cd $T
    REFDIR=/build/gold; RUNDIR=$T/full_chip

    # 2. Set up to execute target step in $RUNDIR
    export GARNET_HOME=/sim/steveri/soc/components/cgra/garnet
    sbk=$GARNET_HOME/mflowgen/bin/setup-buildkite.sh
    source $sbk --dir $RUNDIR |& tee log | less

    # 3. No need to jimmy up a fake tsmc16 library
    # (cd /tmp/steveri/mflowgen.master/adks; ln -s freepdk-45nm tsmc16)

    # 4. Build the design framework
    mflowgen run --design $GARNET_HOME/mflowgen/full_chip

    ### >>> GOOD TO HERE <<< ###

    # 3. Build standalone context and execute target step "postroute_hold"
    mflowgen/bin/get-step-context.sh $REFDIR
    make cadence-innovus-postroute_hold
fi
