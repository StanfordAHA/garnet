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
stash=`mflowgen stash init -p $stashdir | awk '{print $NF}'`
echo "Created stash '$stash'"
# E.g. stash=/sim/tmp/deleteme.prh_stash/2021-0410-mflowgen-stash-3e0809


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
    # ...
    #  - author buildkite-agent
    #    hash: d56728
    #    msg: 10695-10-rtl
    #    step: rtl


    function find_hash {
        python << EOF
import yaml
with open('$1', 'r') as f: data = yaml.load(f)
for dict in data:
  if dict['msg']=='$2':
      print(dict['hash']); exit()
EOF
}

# Testing
# stepid='10695-10-rtl'
# find_hash tmp $stepid

    for yml in $stashdir/*/.mflowgen.stash.yml; do
        echo searching $yml...
        $hash=$(find_hash $yml $stepid)
        if [ "$hash" ]; then
            echo "FOUND hash $hash"
            break
        fi
    done
    
    # Pull the step into our new context
    echo mflowgen stash pull --hash $hash
    mflowgen stash pull --hash $hash

    # Okay buh-bye don't need you no more
    mflowgen stash drop --hash $hash

    # Done!
    echo ''

done

# Let's see what we done did
(cd $gold; mflowgen stash list --all)

# Clean up
echo "CLEANING UP"
set -x
ls -l $stashdir
/bin/rm -rf $stashdir
