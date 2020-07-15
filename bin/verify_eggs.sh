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

# GARNET_HOME default assumes script lives in $GARNET_HOME/bin
[ "$GARNET_HOME" ] || GARNET_HOME=`(cd $script_home/..; pwd)`
garnet=$GARNET_HOME

# HELP
function help {
    echo "$0 <requirements-file>"
    echo "    Check to see if you have required python eggs for building garnet chip"
    echo "    <requirements-file> defaults to '$GARNET_HOME/requirements.txt'"
    echo ""
    echo OPTIONAL COMMAND-LINE SWITCHES
# TODO     echo "    --egg=egg1 --egg=egg2 ...   # Check only specified eggs"
    echo "    -v      # verbose"
    echo "    --debug # debug mode"
    echo "    -h      # help"
    echo ""
}
rfile=$GARNET_HOME/requirements.txt ; # default

# Command-line args / switches
unset VERBOSE; unset DEBUG
for s in $*; do
  [ "$s" ==  "-h"       ] && help && exit
  [ "$s" == "--help"    ] && help && exit
  [ "$s" ==  "-v"       ] && VERBOSE=true
  [ "$s" == "--verbose" ] && VERBOSE=true
  [ "$s" == "--debug"   ] && DEBUG=true
  expr "$s" : "-" > /dev/null || rfile=$s
done
[ "$DEBUG" ] && VERBOSE=true
[ "$DEBUG" ] && echo rfile=$rfile

# # (optional) first arg is requirements.txt file
# # rfile=$1
# # [ "rfile" ] || rfile=$GARNET_HOME/requirements.txt
# [ "$1" ] && rfile=$1 || rfile=$GARNET_HOME/requirements.txt
# [ "$DEBUG" ] && echo rfile=$rfile


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
# => python -m pip list | grep mapping
# => buffer-mapping 0.0.5    /usr/local/src/buffer-mapping
# FIXME I don't see this underbar thing in the sed script...?

# Build slightly cleaned-up list of eggs, repos and (optional) branches
#   -e git://github.com/StanfordAHA/lassen.git@cleanup#egg=lassen
#   -e git://github.com/rdaly525/MetaMapper.git#egg=metamapper
#   ...
# becomes
#   https://github.com/StanfordAHA/lassen.git@cleanup#egg=lassen
#   https://github.com/rdaly525/MetaMapper.git#egg=metamapper
#   ...
#
# 06/2020 here's something new
#   -e git+https://github.com/StanfordAHA/lake@multimaster#egg=lake
# 
# eggs=`grep 'egg=' $rfile | sed 's/^.*git:/http:/'`
# eggs=`grep 'egg=' $rfile | sed 's/^.*git:/http:/' | sed 's/^-e git+//'`
eggs=`grep 'egg=' $rfile | sed 's/^.*git:/https:/' | sed 's/^-e git+htt/htt/'`
if [ "$DEBUG" ]; then
    echo ""
    for e in $eggs; do echo "FOUND EGG '$e'"; done
    echo ""
fi

# "list" is kind of expensive, so just do it once
tmpfile=/tmp/tmp.verify_eggs.$USER.$$
python --version
python -m pip list --format columns > $tmpfile.piplist

n_warnings=0; n_errors=0;
echo "CHECKING EGGS"
for e in $eggs; do
    # Find SHA-1 of egg installed in local environment

    # Note egg names with underbars turn into egg names with dashes(!?) e.g.
    # E.g. "egg=buffer_mapping" => "egg=buffer-mapping"
    eggname=`echo $e | sed 's/.*egg=//' | sed 's/_/-/'`
    eggname_orig=`echo $e | sed 's/.*egg=//'`
    # [ "$DEBUG" ] && echo $eggname
    echo $eggname...

    location=`cat $tmpfile.piplist | awk '$1 == "'$eggname'"{print $3}'`
    # E.g. location="/usr/local/src/lassen"
    if [ "$location" == "" ]; then
        n_errors=$((n_errors+1))
        echo "***ERROR Cannot find egg '$eggname'"; echo ""
        if [ "$VERBOSE" ]; then
            pip=`type -P pip`
            echo    "Consider doing something like:"
            echo    "    pip install -r $garnet/requirements.txt"
            echo    "    --- OR ---"
            echo -n "    sudo $pip install "; egrep "=$eggname_orig\$" $rfile | cat
            echo ""
        fi
        continue
    fi
    [ "$DEBUG" ] && echo "  LOCATION=$location"
    
    if [ `expr match $location '.*site-packages'` != 0 ]; then
        n_warnings=$((n_warnings+1))
        echo "***WARNING '$eggname' is a package in $location, not an egg"; echo "";
        [ "$DEBUG" ] && echo ""
        continue
    fi

    # Local SHA
    local_sha=`cd $location; git log | awk '{print $2; exit}'`

    # What branch do we want? Default to master unless at-sign e.g.
    # remote_egg="http://github.com/StanfordAHA/lassen.git@cleanup"
    remote_egg=`echo $e | sed 's/#egg=.*//'`
    repo=`echo $remote_egg | awk -F "@" '{print $1}'`
    branch=`echo $remote_egg | awk -F "@" '{print $2}'`
    [ "$branch" == "" ] && branch=master

# Driving me crazy! Sometimes this works, sometimes no? For pyverilog mainly
    # I guess...? apparently...? "git+git" means use "develop" branch...?
    # E.g. git+git://github.com/pyhdi/pyverilog.git#egg=pyverilog
    (egrep "=$eggname_orig\$" $rfile | grep -v "git+git" >& /dev/null)\
        || branch="develop"

    [ "$DEBUG" ] && echo "  $repo/$branch"
    remote_sha=`git ls-remote $repo $branch | awk '{print $1}'`
    if [ "$DEBUG" ]; then
        echo "    $local_sha (local)"
        echo "    $remote_sha (remote)"
    fi
    if [ "$local_sha" != "$remote_sha" ]; then
        n_errors=$((n_errors+1))
        echo "***ERROR SHA dont match for repo vs. local egg '$eggname'"
        if [ "$VERBOSE" ]; then
            # pip="sudo `type -P pip`"
            echo    "Consider doing something like:"
            echo    "    pip install -r $garnet/requirements.txt"
            echo    "    --- OR ---"
            echo    "    pip uninstall $eggname"
            echo -n "    pip install "; egrep "=$eggname_orig\$" $rfile | cat
            echo ""
        fi
    else
        [ "$DEBUG" ] && echo "    okay"
    fi
    # [ "$VERBOSE" -o "$DEBUG" ] && echo ""


done

echo ""; echo "$n_errors errors, $n_warnings warnings"
if [ ! "$VERBOSE" ]; then
    echo ""
    echo "For more information do"
    echo "        $0 -v"
    echo ""
fi

echo done now we leave

# Failed final [ "$DEBUG" ] can cause bad exit status! :(
exit 0




#     # e.g. e="lassen     http://github.com/StanfordAHA/lassen.git  cleanup"
#     # make an array maybe
#     ea=
#     egg=`echo $e | awk '{print $1}'`
#     branch_wanted=`echo $e | sed 's/#.*//'`
#     [ "$DEBUG" == "true" ] && echo -n "$egg/$branch_wanted"
#     location=`cat $tmpfile | awk '$1 == "'$egg'"{print $3}'`
#     # E.g. location = "/usr/local/src/pyverilog"
#     if [ "$location" == "" ]; then
#         [ "$DEBUG" == "true" ] && echo "  ...not an egg"
#     else
#         branch_found=`cd $location; git branch | awk '/*/ {print $NF}'`
# #         echo -n " loc=$location"
# #         echo    " branch=$branch_found"
#         if [ "$branch_found" == "$branch_wanted" ]; then
#             [ "$DEBUG" == "true" ] && echo " ...looks good"
#         else
#             echo ""
#             echo "***WARNING Wanted $egg from branch '$branch_wanted,' found '$branch_found'"
#             echo "Consider doing something like this:"
#             echo "    cd $location/../.."
#             echo "    sudo pip uninstall $egg"
#             echo "    sudo pip install" `egrep "$egg\$" $rfile`
#             echo ""
#         fi
#         
#     fi
# done
# [ "$DEBUG" == "true" ] && echo rm $tmpfile
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
  % python -m pip list | grep lassen
  lassen         0.0.1    /usr/local/src/lassen        

  % (cd /usr/local/src/lassen; git log | head -1)
  commit f45cc2b354d32e6adcdfed5c8fb24f16e2c31e10

now check the remote egg. need api's i guess?

  % git ls-remote git://github.com/StanfordAHA/lassen.git cleanup
  f45cc2b354d32e6adcdfed5c8fb24f16e2c31e10        refs/heads/cleanup

hey look they match!

EOF
