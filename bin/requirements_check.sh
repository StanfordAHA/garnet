#!/bin/bash

# Exit on error in any stage of any pipeline
set -eo pipefail

# We'll need this later; do it before any arg processing
function where_this_script_lives {
  # Where this script lives
  scriptpath=$0      # E.g. "build_tarfile.sh" or "foo/bar/build_tarfile.sh"
  scriptdir=${0%/*}  # E.g. "build_tarfile.sh" or "foo/bar"
  if test "$scriptdir" == "$scriptpath"; then scriptdir="."; fi
  # scriptdir=`cd $scriptdir; pwd`
  (cd $scriptdir; pwd)
}
script_home=`where_this_script_lives`

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
  [ "$VERBOSE" == "true" ] && echo -n "Want $pkg , "
  pkg="$1"; pkg_found=true
  # Note package name might have embedded version e.g. 'coreir>=2.0.50'
  pkg=`echo "$pkg" | awk -F '>' '{print $1}'`
  # FIXME really should check version number as well...
  found=`pip3 list | awk '$1=="'$pkg'"{ print "found"}'`
  if [ $found ] ; then 
    [ "$VERBOSE" == "true" ] && pip3 list | awk '$1=="'$pkg'"{ print "found pkg "$0}'
    [ "$VERBOSE" == "true" ] && echo "  Found package '$pkg'"
    return 0
  else
    echo ""
    echo "  ERROR Cannot find installed python package '$pkg'"
    exit 13
  fi
}

[ "$GARNET_HOME" == "" ] && GARNET_HOME=.
packages=`cat $GARNET_HOME/requirements.txt \
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
  echo "ERROR missing packages, maybe need to do pip3 install -r `pwd`/requirements.txt"
  exit 13
fi
echo Found all packages

##############################################################################
subheader +++ VERIFY PYTHON EGGS
$script_home/verify_eggs.sh $GARNET_HOME/requirements.txt


########################################################################
# "pip check" only checks integrity of installed packages;
# It does not look for or verify requirements.txt packages
if ! pip3 check; then
  echo "ERROR bad packages maybe, might need to do pip3 install"
  exit 13
fi
