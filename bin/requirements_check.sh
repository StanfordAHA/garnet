#!/bin/bash

# Exit on error in any stage of any pipeline
set -eo pipefail

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true; fi

function subheader {
  pfx=$1; shift
  echo "------------------------------------------------------------------------"
  echo "$*"
}

##############################################################################
subheader +++ VERIFY PYTHON VERSION

# Note python3 on r7arm is currently found in /usr/local/bin
# ALSO
#     echo "coreir only works if /usr/local/bin comes before /usr/bin."
#     echo 'export PATH=/usr/local/bin:$PATH'
#     echo ""
export PATH=/usr/local/bin:$PATH


# Check for python3.7 FIXME I'm sure there's a better way... :(
# ERROR: Package 'peak' requires a different Python: 3.6.8 not in '>=3.7' :(
v=`python3 -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
echo "Found python version $v -- should be at least 3007"
if [ $v -lt 3007 ] ; then
  echo ""; echo "ERROR found python version $v -- should be 3007"; exit 13
fi
echo ""

# expr `pwd` : '.*/tapeout_16$' > /dev/null && rightplace=true || rightplace=false
# if [ $rightplace != true ] ; then
#   echo ""
#   echo "ERROR looks like you're in the wrong place"
#   echo "- you are here:   `pwd`"
#   echo "- should be here: .../tapeout_16"
#   exit 13
# fi

##############################################################################
subheader +++ VERIFY PYTHON PACKAGE REQUIREMENTS

function check_pip {
  # echo "Verifying existence of python package '$1'..."
  pkg="$1"; pkg_found=true
  found=`pip3 list | awk '$1=="'$pkg'"{ print "found"}'`
  if [ $found ] ; then 
    [ $VERBOSE == true ] && echo "  Found package '$pkg'"
    return 0
  else
    echo "  ERROR Cannot find installed python package '$pkg'"
    exit 13
  fi
}

pip3 check requirements.txt \
  || echo "ERROR bad packages maybe, might need to do pip3 install -r requirements.txt"

packages=`cat requirements.txt \
    | sed 's/.*egg=//' \
    | sed 's/==.*//' \
    | sed 's/buffer_mapping/buffer-mapping/' \
    | sed 's/ordered_set/ordered-set/' \
    | sed 's/cosa/CoSA/' \
    | awk '{print $1}'
  `
echo Need python packages $packages
found_missing=false
for pkg in $packages; do
  (check_pip $pkg) || found_missing=true
done
if [ $found_missing == true ]; then
  echo ""
  echo "ERROR missing packages, maybe need to do pip3 install -r requirements.txt"
  exit 13
fi
echo Found all packages
