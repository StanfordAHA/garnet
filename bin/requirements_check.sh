#!/bin/bash

function help {
    echo "$0"
    echo "    Check to see if you have required environment for building garnet chip"
    echo ""
    echo OPTIONAL COMMAND-LINE SWITCHES
    echo "    -h | --help    # help"
    echo "    -v | --verbose # wordy" 
    echo "    -q | --quiet   # not wordy (default)"
    echo "    --pd_only      # Skip python package and egg checks"
    echo "    --nofail       # continue on failure (default for now)"
    echo ""
}

# switches=($*); for s in "${switches[@]}"; do

########################################################################
# Command-line switches / args / argv
FAIL_ON_ERROR=false; VERBOSE=false
PD_ONLY=false
for s in $*; do
  [ "$s" ==  "-h"       ] && help && exit
  [ "$s" == "--help"    ] && help && exit
  [ "$s" ==  "-q"       ] && VERBOSE=false
  [ "$s" == "--quiet"   ] && VERBOSE=false
  [ "$s" ==  "-v"       ] && VERBOSE=true
  [ "$s" == "--verbose" ] && VERBOSE=true
  [ "$s" == "--nofail"  ] && FAIL_ON_ERROR=false
  [ "$s" == "--pd_only" ] && PD_ONLY=true
done
# echo VERBOSE=$VERBOSE; echo FAIL_ON_ERROR=$FAIL_ON_ERROR

########################################################################
# Exit on error in any stage of any pipeline
[ "$1" == "--nofail" ]         && FAIL_ON_ERROR=false
[ "$FAIL_ON_ERROR" == "true" ] && set -eo pipefail
found_errors=false
function ERROR {
    found_errors=true
    # To call from top level script do e.g.:   ERROR "error-msg foo fa" || exit 13
    # echo $FAIL_ON_ERROR $*;
    echo "***ERROR: $1"
    shift; while [ $# -gt 0 ] ; do echo "         $1"; shift; done
    if [ "$FAIL_ON_ERROR" == "true" ]; then exit 13; fi
}

function where_this_script_lives {
  scriptpath=$0      # E.g. "build_tarfile.sh" or "foo/bar/build_tarfile.sh"
  scriptdir=${0%/*}  # E.g. "build_tarfile.sh" or "foo/bar"
  if test "$scriptdir" == "$scriptpath"; then scriptdir="."; fi
  # scriptdir=`cd $scriptdir; pwd`
  (cd $scriptdir; pwd)
}
script_home=`where_this_script_lives`

function subheader {
  pfx=$1; shift; # Optional prefix for travis/buildkite logs...
  echo "------------------------------------------------------------------------"
  echo "$*"
}

# # GARNET_HOME default assumes script lives in $GARNET_HOME/bin
# [ "$GARNET_HOME" ] || GARNET_HOME=`(cd $script_home/..; pwd)`
# garnet=$GARNET_HOME
# GARNET_HOME=`(cd $script_home/..; pwd)`


##############################################################################
subheader +++ ENVIRONMENT VARIABLES
if [ ! "$GARNET_HOME" ]; then
    GARNET_HOME=`(cd $script_home/..; pwd)`
    ERROR "GARNET_HOME env var not set, you're sure to come a cropper"
    echo "   Should probably do: export GARNET_HOME=$GARNET_HOME"
    echo "   export GARNET_HOME=$GARNET_HOME"
    echo  ""
fi
garnet=$GARNET_HOME

if [ "$OA_HOME" ]; then
    ERROR "OA_HOME=$OA_HOME, should be unset, should do: unset OA_HOME"
    echo  "unset OA_HOME"
    echo  ""
fi
echo ""

##############################################################################
subheader +++ CAD TOOLS

# FIXME Little dumb hack so I can have multiline error messages for cad tools
SAVED_FAIL_ON_ERROR=$FAIL_ON_ERROR
FAIL_ON_ERROR=false

# Verify paths to tools - Genesis2.pl, innovus
tools_needed='
  Genesis2.pl
  innovus
  calibre
  qrc
'
for tool in $tools_needed; do
    unset found_tool
    type $tool >& /dev/null && found_tool=true
    if [ "$found_tool" ]; then
        echo Found $tool: `type -P $tool`
    else
        ERROR "$tool not found; recommend you do something like"\
              "source $GARNET_HOME/mflowgen/setup-garnet.sh"\
              ""
    fi
done

# FLEXLM / check for memory compiler license
if [ "$module" == "Tile_MemCore" ] ; then
    if [ ! -e ~/.flexlmrc ]; then
        ERROR 'I see no license file ~/.flexlmrc'\
              'You may not be able to run e.g. memory compiler'\
              'You may want to do e.g. "cp ~ajcars/.flexlmrc ~"' ''
    else
        echo ""
        echo FOUND \$HOME/.flexlmrc
        ls -l ~/.flexlmrc
        cat ~/.flexlmrc
        echo ""
    fi
fi

# /tmp needs a lot of space
if ! test -d "$TMPDIR"; then
    echo "Cannot find designated temp dir TMPDIR='$TMPDIR'"
    echo "Setting TMPDIR=/tmp instead"
    export TMPDIR=/tmp
fi
tmpdir=$TMPDIR
avail=`df $tmpdir --output=avail | tail -1`
avail_human=`df -H $tmpdir --output=avail | tail -1`
avail_human=`echo $avail_human` ; # Eliminate whitespace?
echo ""
echo "Looks like $tmpdir has $avail_human available space"
echo "-- Note need more than 3G for postroute of full chip"
echo "-- 60G has been enough in the past"
echo "-- Not sure about space < 60G and > 3G"
echo ""
# G=$(( 1024 * 1024 * 1024 ))
G=$(( 1024 * 1024 )) ; # As reported by df in 1024-byte blocks!
if [[ $avail -lt $(( 3 * $G )) ]]; then
    ERROR "less than 3G definitely NOT ENOUGH for full chip postroute"
    echo "Recommend you do something like 'export TMPDIR=/sim/tmp'"
    echo ""
    exit 13
elif [[ $avail -lt $(( 20 * $G )) ]]; then
    ERROR "less than 20G probably NOT ENOUGH for full chip postroute"
    echo "Recommend you do something like 'export TMPDIR=/sim/tmp'"
    echo ""
    exit 13
elif [[ $avail -lt $(( 60 * $G )) ]]; then
    echo "***WARNING less than 60G not (yet) proven to be enough"
    echo "           Recommend you do something like 'export TMPDIR=/sim/tmp'"
    echo ""
fi

FAIL_ON_ERROR=$SAVED_FAIL_ON_ERROR


##############################################################################
subheader +++ VERIFY PYTHON VERSION

# Note python on r7arm is currently found in /usr/local/bin
# ALSO
#     echo "coreir only works if /usr/local/bin comes before /usr/bin."
#     echo 'export PATH=/usr/local/bin:$PATH'
#     echo ""

# oops this is bad. isn't it?
# we want to check the current environment, not build our own!!!
# export PATH=/usr/local/bin:$PATH

# Check for python3.7 FIXME I'm sure there's a better way... :(
# ERROR: Package 'peak' requires a different Python: 3.6.8 not in '>=3.7' :(
v=`python -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`  ; # e.g. '3006'
V=`python -c 'import sys; print("%s.%s" % (sys.version_info[0],sys.version_info[1]))'`; # e.g. '3.6'
if [ $v -lt 3007 ] ; then
    ERROR "found python version $V -- should be at least 3.7"
else
    echo "Found python version $V, good enough (should be at least 3.7)"
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

########################################################################
# DOCKER ACCESSIBILITY CHECK
$script_home/check_docker.sh

########################################################################
# CHECKS SPECIFIC TO PHYSICAL DESIGN
if [ "$PD_ONLY" == "true" ]; then
    # Skip remaining checks, not relevant to pd (physical design)
    exit

else
    ##############################################################################
    subheader +++ VERIFY PYTHON PACKAGE REQUIREMENTS

    function check_pip {
      # echo "Verifying existence of python package '$1'..."
      [ "$VERBOSE" == "true" ] && echo -n "Want $pkg, "
      pkg="$1"; pkg_found=true
      # Note package name might have embedded version e.g. 'coreir>=2.0.50'
      pkg=`echo "$pkg" | awk -F '>' '{print $1}'`
      # FIXME really should check version number as well...
      found=`python -m pip list --format columns | awk '$1=="'$pkg'"{ print "found"}'`
      if [ $found ] ; then 
        [ "$VERBOSE" == "true" ] && \
            python -m pip list --format columns | awk '$1=="'$pkg'"{ print "found pkg "$0}' | sed 's/  */ /g'
        # [ "$VERBOSE" == "true" ] && echo "  Found package '$pkg'"
        return 0
      else
          ERROR "Cannot find installed python package '$pkg'"; echo ""
      fi
    }

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
    echo ""
    for pkg in $packages; do
        (check_pip $pkg) || found_missing=true
    done
    if [ $found_missing == true ]; then
      echo ""
      ERROR "ERROR missing packages, maybe need to do pip3 install -r `pwd`/requirements.txt"
    fi
    echo Found all packages
    echo ""

    set -x
    ##############################################################################
    subheader +++ VERIFY PYTHON EGGS
    echo ""
    echo "% GARNET_HOME/bin/verify_eggs.sh GARNET_HOME/requirements.txt"
    echo ""
    $script_home/verify_eggs.sh $* $GARNET_HOME/requirements.txt

    echo eggs be verify

    # Maybe not useful thinks I
    # ########################################################################
    # # "pip check" only checks integrity of installed packages;
    # # It does not look for or verify requirements.txt packages
    # if ! pip3 check; then
    #   echo "ERROR bad packages maybe, might need to do pip3 install"
    #   exit 13
    # fi
    # [ "$errors_found" == "true" ] && exit 13
fi
