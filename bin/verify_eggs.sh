#!/bin/bash
# Verify eggs in requirements.txt file
# Example: verify_eggs.sh $garnet/requirements.txt -v

# -v / verbose mode
# Yeah no I know this is not the right way to do this
VERBOSE=false
if [ "$2" == "-v" ]; then VERBOSE=true; fi
if [ "$1" == "-v" ]; then VERBOSE=true; shift; fi

# First arg is requirements.txt file
rfile=$1
[ "rfile" == "" ] && rfile=requirements.txt

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

tmpfile=tmp$$
grep 'egg=' $rfile \
    | sed 's|[^@#]*||' \
    | sed 's/^#/@master#/' \
    | sed 's/egg=//' \
    | sed 's/^@//' \
    > $tmpfile

eggs=`cat $tmpfile; rm $tmpfile`
# echo $eggs

# Now list looks like
#     master#gemstone
#     master#canal
#     master#peak
#     cleanup#lassen
#     ...

tmpfile=tmp$$
pip3 list > $tmpfile
# echo $tmpfile
# cat $tmpfile
for e in $eggs; do
    # echo $e
    egg=`echo $e | sed 's/.*#//'`
    branch_wanted=`echo $e | sed 's/#.*//'`
    [ "$VERBOSE" == "true" ] && echo -n "$egg/$branch_wanted"
    location=`cat $tmpfile | awk '$1 == "'$egg'"{print $3}'`
    # E.g. location = "/usr/local/src/pyverilog"
    if [ "$location" == "" ]; then
        [ "$VERBOSE" == "true" ] && echo "  ...not an egg"
    else
        branch_found=`cd $location; git branch | awk '{print $NF}'`
#         echo -n " loc=$location"
#         echo    " branch=$branch_found"
        if [ "$branch_found" == "$branch_wanted" ]; then
            [ "$VERBOSE" == "true" ] && echo " ...looks good"
        else
            echo ""
            echo "***WARNING Wanted $egg from branch '$branch_wanted,' found '$branch_found'"
            echo "Consider doing something like this:"
            echo "    cd $location/.."
            echo "    pip install " `egrep "$egg\$" $rfile`
            echo ""
        fi
        
    fi
done
[ "$VERBOSE" == "true" ] && echo rm $tmpfile
rm $tmpfile

# pip list






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
