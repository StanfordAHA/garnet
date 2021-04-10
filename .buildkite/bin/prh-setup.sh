#!/bin/bash

# Usage: prh-setup <GOLD>

# Fetches, from indicated gold dir <GOLD>, all pre-built steps
# necessary to run postroute_hold. Creates about 14G of stuff.

# Caller did this I think
# echo "+++ PRH TEST RIG SETUP - stash pull context from $GOLD";

# Initialize the stash in tmp dir

# okay that didn't work :(
# stashdir=/sim/tmp/deleteme.prh_stash$$

stashdir=/sim/tmp/deleteme.prh_stash

# stash=`mflowgen stash init -p $stashdir | awk '{print $NF}'`
# echo "Created stash '$stash'"
# # E.g. stash=/sim/tmp/deleteme.prh_stash/2021-0410-mflowgen-stash-3e0809

# What does this do?
stash=$(/bin/ls -d $stashdir/* | head -1)
if [ "$stash" ]; then
    echo "Use existing stash '$stash'"
else
    stash=`mflowgen stash init -p $stashdir | awk '{print $NF}'`
    echo "Created stash '$stash'"
fi




# mflowgen stash list

# Identify a gold dir
# gold=/sim/buildkite-agent/gold/full_chip
gold=$1

# Link up
(cd $gold; mflowgen stash link --path $stash); echo ''

echo DBG25 --------------------------------------------------------
(cd $gold; mflowgen stash list --all)
echo DBG25 --------------------------------------------------------

DBG=
# for step in `(cd $gold; /bin/ls -d [0-9]*) | head -3`; do
set -x
for step in `(cd $gold; /bin/ls -d [0-9]*)`; do
    SKIP=

    # Skip tsmc16 step b/c huge and takes forever;
    # skip others b/c don't need them for context
    for skip in tsmc16 postroute_hold lvs drc rdl signoff; do
        (echo $step | grep $skip) && SKIP=true
    done
    if [ "$SKIP" ]; then printf "SKIP\n\n"; continue; fi

    # Grap and stash step from cache
    echo $step
    stepnum=$(echo $step | sed 's/-.*//')
    stepname=$(echo $step | sed 's/^[0-9]*-//')
    stepid=$$-${step}
    echo step=$step num=$stepnum name=$stepname id=$stepid

    (cd $gold; mflowgen stash push -s $stepnum -m $stepid)

    echo DBG50 --------------------------------------------------------
    (cd $gold; mflowgen stash list --all)
    echo DBG50 --------------------------------------------------------

    ################################################################
    # Find hash num of what we just pushed ('list' doesn't show it) (WHY???)
    # Name of stashed step is something like
    # $stashdir/2021-0407-mflowgen-stash-772a46/2021-0407-rtl-137bce

    # 'mflowgen stash list' is unreliable, hash field is blank sometimes (!)
    #
    # BUT can search $stashdir/*/.mflowgen.stash.yml
    #
    # cat /sim/tmp/deleteme.prh_stash/2021-0410-mflowgen-stash-3e0809/.mflowgen.stash.yml 
    #  - author buildkite-agent
    #    hash: d56728
    #    msg: 10695-10-rtl
    #    step: rtl




    function find_hash {
        python3 << EOF
import yaml
with open('$1', 'r') as f: dict = yaml.safe_load(f)
# print(dict)
if dict['msg']=='$2':
    print(dict['hash']); exit()


# for dict in data
#   if dict['msg']=='$2':
#       print(dict['hash']); exit()

EOF
}
# find_hash $f $stepid



# Testing
# stepid='10695-10-rtl'
# find_hash tmp $stepid

#     f=/sim/tmp/deleteme.prh_stash/2021-0410-mflowgen-stash-66183e/.mflowgen.stash.yml
#     stepid='8393-9-pre-route'
#     find_hash $f $stepid




#     for yml in $stashdir/*/.mflowgen.stash.yml; do
#     /bin/ls -ld  \

    for yml in $stashdir/*/*-${stepname}-*/.mflowgen.stash.node.yml; do
        echo searching $yml...

        echo ---
        echo $stepid
        cat $yml
        echo $stepid
        echo ---


        hash=$(find_hash $yml $stepid)
        if [ "$hash" ]; then
            echo "FOUND hash $hash"
            break
        fi
    done
    
    # Pull the step into our new context
    echo mflowgen stash pull --hash $hash
    ERROR=
    mflowgen stash pull --hash $hash |& grep Error && ERROR=true
    if [ "$ERROR" ]; then 
        echo yes i see it
        mflowgen stash list
        mflowgen stash list --all
        mflowgen stash list --verbose
        exit 13; 
    fi




    # Okay buh-bye don't need you no more
    mflowgen stash drop --hash $hash

    # Here's the tricky part
    d=/sim/tmp/deleteme.prh_stash/*/*-$hash
    ls -d $d
    ls $d
    echo deleting $d
    /bin/rm -rf $d

    # Done!
    echo ''

done

# Let's see what we done did
(cd $gold; mflowgen stash list --all)

# Clean up
echo "CLEANING UP"
set -x
# ls -l $stashdir
# /bin/rm -rf $stashdir

echo looking for big baddies
if ! [ "$stashdir" ]; then
    echo "ERROR cannot find stashdir '$stashdir'"

else

    for f in `/bin/ls -R $stashdir`; do
        pid=$$
        yml=$f/.mflowgen.stash.node.yml
        if egrep "msg: *$pid-" $f/.mflowgen.stash.node.yml; then
            echo Found a baddie = $f
            cat $yml
            echo Deleting the baddie
            /bin/rm -rf $f
        fi
    done
fi

exit 13
