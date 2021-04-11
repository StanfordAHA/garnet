#!/bin/bash

# Usage: prh-setup <GOLD>

# Fetches, from indicated gold dir <GOLD>, all pre-built steps
# necessary to run postroute_hold. Creates about 14G of stuff.

# Caller did this I think
# echo "+++ PRH TEST RIG SETUP - stash pull context from $GOLD";

# Identify a gold dir
# gold=/sim/buildkite-agent/gold/full_chip
gold=$1

function STASH {

    # Not necessary no more...right?
    #     echo "mflowgen stash link --path $stash; mflowgen $*"
    #     echo okay now do it
    #     mflowgen stash link --path $stash; mflowgen stash $*

    echo DOING mflowgen stash $*
    set -x
    mflowgen stash $* |& tr -cd "[:print:][:blank:]\n" | sed 's/\[[0-9]*m//g'
    set +x
}

# One stash to rule them all...
yml=$gold/.mflowgen.stash.yml
if test -e $yml; then
    stash=$(cat $yml | awk '{print $NF; exit}')
    echo "Use existing gold stash '$stash'"
    stashdir=$stash
else
    echo "$gold not linked yet"

    echo "First delete old stash dir if exists"
    stashdir=/sim/tmp/deleteme.prh_stash
    if test -e $stashdir; then
        echo "delete existing stash $stashdir..."
        /bin/rm -rf $stashdir
    fi
    
    echo "make and initialize a new one"
    echo mflowgen stash init -p $stashdir
    stash=`mflowgen stash init -p $stashdir | awk '{print $NF}'`
    echo "Created stash '$stash'"

    (cd $gold; STASH link -p $stashdir)


fi

echo "Using stash '$stash'"
STASH link -p $stashdir


# Already done did...as part of init...right...?
# Link up
# (cd $gold; mflowgen stash link --path $stash); echo ''

# It's not linked in yet
# STASH list --all

# mflowgen stash list --all |& tr -cd "[:ctl:]"




# STASH link --path $stash
pwd
STASH list --all



echo DBG25 --------------------------------------------------------
(cd $gold; STASH list --all)
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

    # stepid=$$-${step}

    echo step=$step num=$stepnum name=$stepname # id=$stepid

    echo "Looking for step $step"
    STASH list --all

    # See if step is already stashed
    # E.g. " - 435de6 [ 2021-0410 ] buildkite-agent sealring -- 17827-11-sealring"
    # stepname=sealring
    STASH list --all | awk '$1=="-" && $7=="'$stepname'" { print $7; exit }'
    hash=$(STASH list --all | awk '$1=="-" && $7=="'$stepname'" { print $2; exit }')
    if ! [ "$hash" ]; then
        # need to grap the step from goldie
        (cd $gold; STASH push -s $stepnum -m $step)

        # stepname=pre-route
               STASH list --all | awk '$1=="-" && $NF=="'$step'" { print $2; exit }'
        hash=$(STASH list --all | awk '$1=="-" && $NF=="'$step'" { print $2; exit }')
        echo $hash

    fi
    
    # Pull the step into our new context
    echo STASH pull --hash $hash

    ERROR=
    if [ "$hash" ]; then
        STASH pull --hash $hash |& grep Error && ERROR=true
        if [ "$ERROR" ]; then 
            echo yes i see it
            echo could not find $hash

            STASH list --all
            echo could not find $hash
            STASH list --verbose
            echo could not find $hash
            exit 13; 

        fi
    else
        # echo could not find hash for stepid $stepid
        echo could not find hash for step $step
        exit 13
    fi
    



#     # Okay buh-bye don't need you no more
#     STASH drop --hash $hash

#     # Here's the tricky part
#     d=/sim/tmp/${stashdir}/*/*-$hash
#     ls -d $d
#     ls $d
#     echo deleting $d
# 
#     echo STASH drop --hash $hash
#     STASH drop --hash $hash
# 
#     echo deleted $d
#     ls -d $d
#     ls $d

    # /bin/rm -rf $d



    # Done!
    echo ''

done

# Let's see what we done did
(cd $gold; STASH list --all)

# # Clean up
# echo "CLEANING UP"
# set -x
# # ls -l $stashdir
# # /bin/rm -rf $stashdir
# 
# echo looking for big baddies
# if ! [ "$stashdir" ]; then
#     echo "ERROR cannot find stashdir '$stashdir'"
# 
# else
#     steps=$(
#         find $stashdir -name .mflowgen.stash.node.yml \
#         | sed 's,/.mflowgen.stash.node.yml$,,'
#     )
#     for f in $steps; do
# 
# #         set -x
#         # Find pid of each step in stash
#         yml=$f/.mflowgen.stash.node.yml
#         grep 'msg: ' $yml
#         pid=$(grep 'msg: ' $yml | sed 's/-/ /' | awk '{print $2}')
# 
# # e.g. msg: 12012-12-soc-rtl
# 
#         echo I am $$
#         echo found candidate pid=$pid
#         VALID=
#         echo "$pid" | egrep '^[0-9]+$' >& /dev/null && VALID=true
#         if [ "$VALID" ]; then
#             echo found pid=$pid
#             FOUND_PROCESS=
#             (ps --pid $pid | grep $pid >& /dev/null) && FOUND_PROCESS=true
#             if ! [ "$FOUND_PROCESS" ]; then
#                 echo Found orphan step $f
#                 echo to do: /bin/rm -rf $f
#             else
#                 echo not an orphan -- step has valid process attached
#             fi
#         fi
#         
#         set +x
#     done
# 
# fi
# 
# exit 13
