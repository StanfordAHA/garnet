#!/bin/bash

# Usage: $0 <refdir>

# Using reference/cached build in <refdir>, find and link to the
# necessary context for running a single target step in an mflowgen
# build

# E.g. for cadence-innovus-postroute_hold we would link two steps from
# <refdir> into current (build) dir
# 
#     ln -s 23-cadence-innovus-flowsetup <refdir>/23-cadence-innovus-postroute
#     ln -s 31-cadence-innovus-postroute <refdir>/30-cadence-innovus-postroute

# Example usage: run standalone step "cadence-innovus-postroute_hold"
# in $RUNDIR using cached information in $REFDIR":
# 
#     # 1. Designate a reference directory from which we will pull context.
#     REFDIR=/build/gold
#
#     # 2. Build the design framework
#     mflowgen run --design $GARNET_HOME/mflowgen/full_chip
#
#     # 3. Build standalone context and execute target step "postroute_hold"
#     get-step-context.sh $REFDIR cadence-innovus-postroute_hold
#     make cadence-innovus-postroute_hold

REF=$1
target_step=$2
target_step=cadence-innovus-postroute_hold


DBG=0

echo "--- BEGIN $0 $*" | sed "s,$GARNET_HOME,\$GARNET_HOME,"
echo "  where GARNET_HOME=$GARNET_HOME"

echo "+++ STANDALONE TEST RIG SETUP - build symlinks to steps in $REF/full_chip";

function find_dependences {
    # Example: 
    #    find_dependences cadence-innovus-postroute_hold
    # 
    # Returns:
    #      adk
    #      cadence-innovus-postroute
    #      cadence-innovus-flowsetup

    stepname="$1"
    stepnum=`make list | awk '$NF == "'$step'"{print $2; exit}'`
    echo "FOUND $stepnum $stepname"

    # Note for some reason it ignores adk dependences.
    # Seems to work anyway I guess?
    deps=`make info-$stepnum |& grep -v warning | sed 's/|//g' \
         | awk '$NF ~ /^[0-9]/ {print $NF}; /^Parameters/{exit}' \
         | sed "/$step\$/,\\$d" \
         | egrep -v 'freepdk|tsmc' \
         | sed 's/^[0-9]*[-]//'`

    echo $deps
}

# Find-dependences came up with this:

set +x
find_dependences cadence-innovus-postroute_hold
set -x
echo ""
echo ""
echo ""




for step in cadence-innovus-postroute cadence-innovus-flowsetup; do

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

echo "+++ TODO LIST";
echo "make -n cadence-innovus-postroute_hold"
make -n cadence-innovus-postroute_hold
|& egrep "^mkdir.*output" | sed "s/output.*//" | egrep -v ^Make'


# # Did we get away with it? Example of how to check:
# echo "+++ TODO LIST"
# function make-n-filter { egrep '^mkdir.*output' | sed 's/output.*//' | egrep -v ^Make ;}
# make -n cadence-innovus-postroute_hold |& make-n-filter



# NOTES


exit
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

