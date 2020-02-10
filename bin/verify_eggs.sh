#!/bin/bash
# Verify eggs in requirements.txt file
# Example: verify_eggs.sh $garnet/requirements.txt -v

function where_this_script_lives {
  # Where this script lives
  scriptpath=$0      # E.g. "build_tarfile.sh" or "foo/bar/build_tarfile.sh"
  scriptdir=${0%/*}  # E.g. "build_tarfile.sh" or "foo/bar"
  if test "$scriptdir" == "$scriptpath"; then scriptdir="."; fi
  # scriptdir=`cd $scriptdir; pwd`
  (cd $scriptdir; pwd)
}
script_home=`where_this_script_lives`

# -v / verbose mode
# Yeah no I know this is not the right way to do this
unset VERBOSE
if [ "$2" == "-v" ]; then VERBOSE=true; fi
if [ "$1" == "-v" ]; then VERBOSE=true; shift; fi

# GARNET_HOME default assumes script lives in $GARNET_HOME/bin
[ "$GARNET_HOME" ] || GARNET_HOME=`(cd $script_home/..; pwd)`

# (optional) first arg is requirements.txt file
# rfile=$1
# [ "rfile" ] || rfile=$GARNET_HOME/requirements.txt
[ "$1" ] && rfile=$1 || rfile=$GARNET_HOME/requirements.txt
[ "$VERBOSE" ] && echo rfile=$rfile

# Sample requirements.txt file:
#     -e git://github.com/StanfordAHA/gemstone.git#egg=gemstone
#     -e git://github.com/StanfordAHA/canal.git#egg=canal
#     -e git://github.com/phanrahan/peak.git#egg=peak
#     -e git://github.com/StanfordAHA/lassen.git@cleanup#egg=lassen
#     -e git://github.com/rdaly525/MetaMapper.git#egg=metamapper
#     -e git://github.com/Kuree/karst.git#egg=karst
#     -e git://github.com/joyliu37/BufferMapping#egg=buffer_mapping
#     -e git+git://github.com/pyhdi/pyverilog.git#egg=pyverilog
#     ordered_set
#     coreir>=2.0.50
#     magma-lang>=2.0.0
#     mantle>=2.0.0
#     cosa
#     -e git://github.com/leonardt/fault.git#egg=fault
#     hwtypes
#     archipelago

# Verify eggs and their branches e.g. 'cleanup' and 'master' respectively:
#     -e git://github.com/StanfordAHA/lassen.git@cleanup#egg=lassen
#     -e git://github.com/rdaly525/MetaMapper.git#egg=metamapper

# Note egg names with underbars turn into egg names with dashes(!?) e.g.
# -e git://github.com/joyliu37/BufferMapping#egg=buffer_mapping
# => pip3 list | grep mapping
# => buffer-mapping 0.0.5    /usr/local/src/buffer-mapping
# FIXME I don't see this underbar thing in the sed script...?

# Build slightly cleaned-up list of eggs, repos and (optional) branches
#   -e git://github.com/StanfordAHA/lassen.git@cleanup#egg=lassen
#   -e git://github.com/rdaly525/MetaMapper.git#egg=metamapper
#   ...
# becomes
#   http://github.com/StanfordAHA/lassen.git@cleanup#egg=lassen
#   http://github.com/rdaly525/MetaMapper.git#egg=metamapper
#   ...
eggs=`grep 'egg=' $rfile | sed 's/^.*git:/http:/'`
if [ "$VERBOSE" ]; then
    echo ""
    for e in $eggs; do echo $e; done
    echo ""
fi


# "list" is kind of expensive, so just do it once
tmpfile=/tmp/tmp.verify_eggs.$USER.$$
pip3 list > $tmpfile.piplist
# echo $tmpfile
# cat $tmpfile

for e in $eggs; do
    # Find SHA-1 of egg installed in local environment

    # Note egg names with underbars turn into egg names with dashes(!?) e.g.
    # E.g. "egg=buffer_mapping" => "egg=buffer-mapping"
    eggname=`echo $e | sed 's/.*egg=//' | sed 's/_/-/'`
    eggname_orig=`echo $e | sed 's/.*egg=//'`
    [ "$VERBOSE" ] && echo $eggname

    # E.g. location="/usr/local/src/lassen"
    location=`cat $tmpfile.piplist | awk '$1 == "'$eggname'"{print $3}'`
    if ["$location" == ""]; then
        echo "***ERROR Cannot find egg '$eggname'"
        echo    "Consider doing something like this:"
        echo    "    cd /usr/local"
        echo -n "    sudo pip3 install ";
        egrep   "=$eggname_orig\$" $rfile | cat
        echo ""
        continue
    fi
    [ "$VERBOSE" ] && echo "  $location"

    # Local SHA
    local_sha=`cd $location; git log | awk '{print $2; exit}'`

    # What branch do we want? Default to master unless at-sign e.g.
    # remote_egg="http://github.com/StanfordAHA/lassen.git@cleanup"
    remote_egg=`echo $e | sed 's/#egg=.*//'`
    repo=`echo $remote_egg | awk -F "@" '{print $1}'`
    branch=`echo $remote_egg | awk -F "@" '{print $2}'`
    [ "$branch" == "" ] && branch=master
    [ "$VERBOSE" ] && echo "  $repo/$branch"

    remote_sha=`git ls-remote $repo $branch | awk '{print $1}'`
    if [ "$VERBOSE" ]; then
        echo "    $local_sha"
        echo "    $remote_sha"
    fi
    if [ "$local_sha" != "$remote_sha" ]; then
        [ "$VERBOSE" ] && echo ""
        echo    "***ERROR SHA dont match for repo vs. local egg '$eggname'"
        echo    "Consider doing something like this:"
        echo    "    sudo pip3 uninstall $eggname"
        echo    "    cd $location/.."
        echo -n "    sudo pip3 install ";
        egrep "=$eggname_orig\$" $rfile | cat
        echo ""
    else
        [ "$VERBOSE" ] && echo "    okay"
        [ "$VERBOSE" ] && echo ""
    fi
done





#     # e.g. e="lassen     http://github.com/StanfordAHA/lassen.git  cleanup"
#     # make an array maybe
#     ea=
#     egg=`echo $e | awk '{print $1}'`
#     branch_wanted=`echo $e | sed 's/#.*//'`
#     [ "$VERBOSE" == "true" ] && echo -n "$egg/$branch_wanted"
#     location=`cat $tmpfile | awk '$1 == "'$egg'"{print $3}'`
#     # E.g. location = "/usr/local/src/pyverilog"
#     if [ "$location" == "" ]; then
#         [ "$VERBOSE" == "true" ] && echo "  ...not an egg"
#     else
#         branch_found=`cd $location; git branch | awk '/*/ {print $NF}'`
# #         echo -n " loc=$location"
# #         echo    " branch=$branch_found"
#         if [ "$branch_found" == "$branch_wanted" ]; then
#             [ "$VERBOSE" == "true" ] && echo " ...looks good"
#         else
#             echo ""
#             echo "***WARNING Wanted $egg from branch '$branch_wanted,' found '$branch_found'"
#             echo "Consider doing something like this:"
#             echo "    cd $location/../.."
#             echo "    sudo pip3 uninstall $egg"
#             echo "    sudo pip3 install" `egrep "$egg\$" $rfile`
#             echo ""
#         fi
#         
#     fi
# done
# [ "$VERBOSE" == "true" ] && echo rm $tmpfile
# rm $tmpfile.piplist



# pip list

# becomes
#   lassen     http://github.com/StanfordAHA/lassen.git  cleanup
#   metamapper http://github.com/rdaly525/MetaMapper.git






# eggs=`grep egg= $GARNET_HOME/requirements.txt \
#     | sed 's|.*/||'`
# 
# echo $eggs

#     | sed 's/==.*//' \
#     | sed 's/buffer_mapping/buffer-mapping/' \
#     | sed 's/ordered_set/ordered-set/' \
#     | sed 's/cosa/CoSA/' \
#     | awk '{print $1}'
#   `
# 

########################################################################
exit
cat <<EOF

Not enough to check branch/version number of eggs! Sometimes (at least
once) compatibility breaks even though branch and version number stays
the same. Must check...? git hash number? versus...? known good env..? 
which is...where...? in remote repo i guess.

so:
  1. find git hash of egg installed in my environment
  2. compare to git hash of remote egg
  3. see if they match

E.g. to check my lassen egg against remote, based on requirement
  -e git://github.com/StanfordAHA/lassen.git@cleanup#egg=lassen

we do something like
  % pip3 list | grep lassen
  lassen         0.0.1    /usr/local/src/lassen        

  % (cd /usr/local/src/lassen; git log | head -1)
  commit f45cc2b354d32e6adcdfed5c8fb24f16e2c31e10

now check the remote egg. need api's i guess?

  % git ls-remote git://github.com/StanfordAHA/lassen.git cleanup
  f45cc2b354d32e6adcdfed5c8fb24f16e2c31e10        refs/heads/cleanup

hey look they match!

EOF
