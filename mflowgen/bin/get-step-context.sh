#!/bin/bash

# LATER want this to work for any step. But...for now...

# Usage: $0 <refdir>
REF=$1

# Build the necessary context to run postroute_hold step only.
# Want two steps
#     *-cadence-innovus-postroute
#     *-cadence-innovus-flowsetup

# Example usage
# 
#     RUNDIR=/build/run230/full_chip
#     REFDIR=/build/gold
# 
#     source mflowgen/bin/setup-buildkite.sh --dir $RUNDIR
#     mflowgen/bin/get-step-context.sh $REFDIR
#     make cadence-innovus-postroute_hold

DBG=
echo "+++ PRH TEST RIG SETUP - symlink to steps in $REF/full_chip";
for step in cadence-innovus-postroute cadence-innovus-flowsetup; do

    echo $step
    stepnum=$(cd $REF/full_chip; make list |& egrep ": $step\$" | awk '{print $2}')
    ref_step=$REF/full_chip/$stepnum-$step
    [ "$DBG" ] && echo Found ref step $ref_step
    if ! test -d $ref_step; then
        echo "hm look like $ref_step don't exist after all..."
        exit 13
    fi

    # Need '.prebuilt' to make it work for some reason...
    [ "$DBG" ] && echo "touch <refdir>/<step>/.prebuilt"
    touch $ref_step/.prebuilt

    [ "$DBG" ] && (make list |& egrep ": $step\$")
    stepnum=$(make list |& egrep ": $step\$" | awk '{print $2}')
    local_step=$stepnum-$step
    [ "$DBG" ] && echo Found local step $local_step; echo ''

    [ "$DBG" ] && echo "Ready to do: ln -s $ref_step $local_step"
    ln -s $ref_step $local_step
    echo "$local_step => $ref_step"
    echo ''

done

# Did we get away with it?
echo "+++ TODO LIST"
function make-n-filter { egrep '^mkdir.*output' | sed 's/output.*//' | egrep -v ^Make ;}
make -n cadence-innovus-postroute_hold |& make-n-filter
