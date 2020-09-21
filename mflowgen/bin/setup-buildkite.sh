#!/bin/bash

# Set up environment to run a buildkite test in the indicated directory.
# Examples:
#     source setup-buildkite.sh --dir /build/gold.100/full_chip
#     source setup-buildkite.sh --dir /build/gold.100/full_chip --need_space 30G

##############################################################################
# Script must be sourced; complain if someone tries to execute it instead.
# Stackoverflow says to do it this way (ish)
# Note BASH_SOURCE is a list of the entire source/call stack
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    # Oops looks like someone tried to execute this script; that's bad
    echo ""
    echo "ERROR!"
    echo "Do *not* execute this script ('$0')"
    echo "It should be only be *sourced* (from within a bash shell)"
    echo ""
    return 13 || exit 13
fi

##############################################################################
# Usage

# Note if file is sourced with no args, "$1" etc. defaults to
# enclosing scope e.g. might get $1="TCLSH=/bin/tclsh" (??)
# SO. To keep things honest, will require '--dir'

script=${BASH_SOURCE[0]}
function usage {
    cat <<EOF
Usage:
    source $script --dir < build-directory > [ OPTIONS ]

Description:
    Sets up to build the chip in the indicated directory.
    If no directory is specified, build happens in current directory
    "`pwd`"

Options:
  --need_space <amt>
      Make sure targ dir has least <amt> gigabytes available (default '100G')

Examples:
    source $script --dir /build/gold.100/full_chip
    source $script --dir /build/gold.100/full_chip --need_space 30G
    
EOF
}

########################################################################
# Args / switch processing

if ! [ "$1" == "--dir" ]; then
    echo ""
    echo "**ERROR: missing required arg '--dir' i.e. might want to do something like"
    echo "$script --dir ."
    echo ""
    usage; return 13
fi

build_dir=
VERBOSE=false
need_space=100G
while [ $# -gt 0 ] ; do
    case "$1" in
        -h|--help)    usage; return;    ;;
        -v|--verbose) VERBOSE=true;  ;;
        -q|--quiet)   VERBOSE=false; ;;
        --dir)        shift; build_dir="$1"; ;;

        # E.g. '--need_space' or '--want_space' or '--need-space'...
        --*_space)    shift; need_space="$1"; ;;
        --*-space)    shift; need_space="$1"; ;;

        # Any other 'dashed' arg
        -*)
            echo "***ERROR: unrecognized arg '$1'"; usage; return 13; ;;
    esac
    shift
done

echo ""
echo "Using build dir '$build_dir'"
echo "Will want $need_space available space."

# Unit tests
DO_UNIT_TESTS=false
if [ "$DO_UNIT_TESTS" == "true" ]; then # cut'n'paste
    script=setup-buildkite.sh
    clear; source $script
    clear; source $script --dir .
    clear; source $script --dir foo
    clear; source $script --dir foo --need_space 30G
fi

########################################################################
# GARNET_HOME
# Note "make rtl" (among others maybe) needs GARNET_HOME env var

if [ "$GARNET_HOME" ]; then
    echo "Found existing GARNET_HOME='$GARNET_HOME'; hope that's correct...!"
else
    echo "Searching for garnet home..."
    # setup assumes script_home == "$GARNET_HOME/mflowgen/bin/"
    function where_this_script_lives {
        # Where this script lives
        s=${BASH_SOURCE[0]}
        scriptpath=$s      # E.g. "build_tarfile.sh" or "foo/bar/build_tarfile.sh"
        scriptdir=${s%/*}  # E.g. "build_tarfile.sh" or "foo/bar"
        if test "$scriptdir" == "$scriptpath"; then scriptdir="."; fi
        # scriptdir=`cd $scriptdir; pwd`
        (cd $scriptdir; pwd)
    }
    script_home=`where_this_script_lives`
    export GARNET_HOME=`cd $script_home/../..; pwd`
    echo "Setting GARNET_HOME='$GARNET_HOME'; hope that's correct...!"
fi
echo ""
garnet=$GARNET_HOME

# (And/or could do something like
#   if [ "$USER" == "buildkite-agent" ]; then
#       export GARNET_HOME=$BUILDKITE_BUILD_CHECKOUT_PATH

# Unit tests
DO_UNIT_TESTS=false
if [ "$DO_UNIT_TESTS" == "true" ]; then # cut'n'paste
    echo $GARNET_HOME
    script=setup-buildkite.sh
    clear; source $script --dir .

    # See if it can use context to find a missing garnet home
    clear
    tmp=$GARNET_HOME
    unset GARNET_HOME
    echo $GARNET_HOME
    source $script --dir .
    echo $GARNET_HOME
    export GARNET_HOME=$tmp
fi


########################################################################
# SPACE CHECK -- generally need at least 100G for a full build
echo '+++ SPACE CHECK'

# Check partition containing target dir $build_dir" for sufficient space
# Find target build partition
dest_dir=`pwd`

function find_existing_dir {
    # Given a pathname such that only the first part of the pathname
    # might currently exist, find the existing portion of the path
    # E.g. given "/var/lib/foo/bar/tmp.lib", but only "/var/lib" exists atm,
    # return "/var/lib"

    #   'newdir/cachename' => return '.'
    #   'existing_dir/cachename' => return 'existing_dir'
    #   '/nobackup/steveri/newdir/cachename' => return '/nobackup/steveri'


    # Avoid infinite loops!
    # Worst-case, dirname should ultimately settle at either '/' or '.'
    d=$1; while ! test -d $d; do d=`dirname $d`; done
    echo $d
}
DO_UNIT_TESTS=false
if [ "$DO_UNIT_TESTS" == "true" ]; then # cut'n'paste for unit tests
    find_existing_dir newdir/cachename
    (cd /var; find_existing_dir lib)
    (cd /var; find_existing_dir lib/foo/bar)
    find_existing_dir /var/lib/foo/bar/tmp.txt
    find_existing_dir /var/lib/nfs
    find_existing_dir /var/lib/nfs/xtab
    find_existing_dir /var
    find_existing_dir /goob
    find_existing_dir /
fi

# Find currently-existing portion of target build dir
dest_dir=`find_existing_dir $build_dir`

# See if it has enough space
unset FAIL
$garnet/bin/space_check.sh -v $dest_dir $need_space || FAIL=true

# Process the results of the space check, PASS or FAIL
if ! [ "$FAIL" ]; then
    echo ""
    df -H $dest_dir; echo ""; echo "Good enough!"; echo ""
else
    # Note 'space_check' script (also) has its own cogent error messages
    echo "Consider reducing space requrement e.g."
    echo "  $script --dir $build_dir    --need_space 0G"
    echo ""
fi
unset FAIL

DO_UNIT_TESTS=false
if [ "$DO_UNIT_TESTS" == "true" ]; then # cut'n'paste for unit tests
    return 0
    clear; source $script --dir .
    clear; source $script --dir . --need_space 2000G
    clear; source $script --dir . --need_space 0G
fi

########################################################################
# Running out of space in /tmp!!?
export TMPDIR=/sim/tmp

########################################################################
# Clean up debris in /sim/tmp
$garnet/mflowgen/bin/cleanup-buildkite.sh


########################################################################
# Build environment and check requirements
function check_pyversions {
    echo ""
    echo PYTHON PATHS:
    echo "--------------"
    type -P python
    python --version
    pip --version
    echo "--------------"
}

# Buildkite agent uses pre-built common virtual environment
# /usr/local/venv_garnet on buildkite host machine r7arm-aha
# If you're not "buildkite-agent", you're on your own.

if [ "$USER" == "buildkite-agent" ]; then
    echo "--- ENVIRONMENT"; echo ""
    venv=/usr/local/venv_garnet
    if ! test -d $venv; then
        echo "**ERROR: Cannot find pre-built environment '$venv'"
        return 13
    fi
    echo "USING PRE-BUILT PYTHON VIRTUAL ENVIRONMENT '$venv'"
    source $venv/bin/activate

    check_pyversions

    # pip install -r $garnet/requirements.txt
    # Biting the bullet and updating to the latest everything;
    # also, it's the right thing to do I guess
    pip install -U -r $garnet/requirements.txt
fi


########################################################################
# FIXME Probably don't need this (/usr/local/bin stuff) any more...
# FIXME In fact it probably does more harm than good
# FIXME Need to do experiments to make sure it's safe to remove...
########################################################################
# Lots of useful things in /usr/local/bin. coreir for instance ("type"=="which")
# echo ""; type coreir
export PATH="$PATH:/usr/local/bin"; hash -r
# type coreir; echo ""
########################################################################


##############################################################################
# Set up paths for innovus, genus, dc etc.
# source $garnet/.buildkite/setup.sh
# source $garnet/.buildkite/setup-calibre.sh
# Use the new stuff
source $garnet/mflowgen/setup-garnet.sh

##############################################################################
# Recheck python/pip versions b/c CAD modules can muck them up :(
check_pyversions

##############################################################################
# OA_HOME weirdness
# OA_HOME *** WILL DRIVE ME MAD!!! ***
echo "--- UNSET OA_HOME"
echo ""
echo "buildkite (but not arm7 (???)) errs if OA_HOME is set"
echo "BEFORE: OA_HOME=$OA_HOME"
echo "unset OA_HOME"
unset OA_HOME
echo "AFTER:  OA_HOME=$OA_HOME"
echo ""

# Okay let's check and see what we got.
echo "--- REQUIREMENTS CHECK"; echo ""

# Maybe don't need to check python libs and eggs no more...?
# $garnet/bin/requirements_check.sh -v --debug
$garnet/bin/requirements_check.sh -v --debug --pd_only


########################################################################
# Find or create the requested build directory
if [ "$build_dir" ]; then

    # Build in the requested cache directory 'build_dir'
    build_dir="$build_dir"
    if test -d $build_dir; then
        echo "--- Using existing cache dir '$build_dir'"
        cd $build_dir
    else
        echo "--- Making new cache dir '$build_dir'"
        mkdir -p $build_dir
        cd $build_dir
    fi
fi
echo "--- Building in destination dir `pwd`"


##############################################################################
# NEW MFLOWGEN --- see far below for old setup
##############################################################################
# MFLOWGEN: Use a single common mflowgen for all builds why not
echo "--- INSTALL LATEST MFLOWGEN"
mflowgen=/sim/buildkite-agent/mflowgen
pushd $mflowgen
  git checkout master
  git pull
  TOP=$PWD; pip install -e .; which mflowgen; pip list | grep mflowgen
popd
echo ""
  
# Okay. Ick. If we leave it here, we get all these weird and very
# non-portable relative links e.g.
#    % ls -l /build/gold.112/full_chip/17-tile_array/10-tsmc16/
#    % multivt -> ../../../../../sim/buildkite-agent/mflowgen/adks/tsmc16/multivt/
# 
# So we make a local symlink to contain the damage. It still builds
# an ugly relative link but now maybe it's more contained, something like
#    % ls -l /build/gold.112/full_chip/17-tile_array/10-tsmc16/
#    % multivt -> ../../../mflowgen/adks/tsmc16/multivt/

mflowgen_orig=$mflowgen
ln -s $mflowgen_orig
mflowgen=`pwd`/mflowgen



########################################################################
# NEW ADK SETUP --- see far below for old setup
########################################################################
echo "--- ADK SETUP / CHECK"

echo COPY LATEST ADK TO MFLOWGEN REPO

# Copy the latest tsmc16 adk from a nearby repo; we'll use the one in steveri.
# 
# Note the adks must be touchable by current user, thus must copy
# locally and cannot e.g. use symlink to someone else's existing adk.

if [ "$USER" == "buildkite-agent" ]; then

    tsmc16=/sim/steveri/mflowgen/adks/tsmc16
    echo Copying adk from $tsmc16
    ls -l $tsmc16

    adks=$mflowgen/adks
    echo "Copying adks from '$tsmc16' to '$adks'"
    # Need '-f' to e.g. copy over existing read-only .git objects
    set -x; cp -frpH $tsmc16 $adks; set +x

    export MFLOWGEN_PATH=$adks
    echo "Set MFLOWGEN_PATH=$MFLOWGEN_PATH"; echo ""

else
    # FIXME/TODO what about normal users, can they use this?
    echo
    echo "WARNING you are not buildkite agent."
    echo "You'll probably need to find your own way to the adks."
    echo "Maybe something like:"
    echo "export MFLOWGEN_PATH='/my/path/to/adks/tsmc16'"
    echo ""
    echo "Meanwhile: found MFLOWGEN_PATH='$MFLOWGEN_PATH'"; echo ""
fi







##############################################################################
##############################################################################
##############################################################################
# END; everything from here down is to be deleted later
##############################################################################
##############################################################################
##############################################################################
#   update_cache=/build/gold.100/full_chip/17-tile_array
#   source mflowgen/test/bin/bk_setup.sh full_chip
#   cd $update_cache
#   pwd
#   ./mflowgen-run > mflowgen_run.log.$$PPID
# 
# 
# 
#   - 'mflowgen/test/test_module.sh full_chip
#        --debug
#        --update_cache /sim/buildkite-agent/gold.$$BUILDKITE_BUILD_NUMBER
#        --setup_only;
#      cd /build/gold.100/full_chip/17-tile_array
# 
# 
#   build_dir=/build/gold.100/full_chip/17-tile_array;
# 
#   '
#   cd $$build_dir; source 
#   

# OLD:
#     if test -d $venv; then
#         echo "USING PRE-BUILT PYTHON VIRTUAL ENVIRONMENT"
#         source $venv/bin/activate
#     else
#         echo "CANNOT FIND PRE-BUILT PYTHON VIRTUAL ENVIRONMENT"
#         echo "- building a new one from scratch"
#         # JOBDIR should be per-buildstep environment e.g.
#         # /sim/buildkite-agent/builds/bigjobs-1/tapeout-aha/
#         JOBDIR=$BUILDKITE_BUILD_CHECKOUT_PATH
#         pushd $JOBDIR
#           /usr/local/bin/python3 -m venv venv ;# Builds "$JOBDIR/venv" maybe
#           source $JOBDIR/venv/bin/activate
#         popd
#     fi
# 
#     check_pyversions
# 
#     # pip install -r $garnet/requirements.txt
#     # Biting the bullet and updating to the latest everything;
#     # also, it's the right thing to do I guess
#     pip install -U -r $garnet/requirements.txt

########################################################################
# OLD MFLOWGEN - delete after new code (below) has successfully
# completed a build or two...
# ########################################################################
# # Make a build space for mflowgen; clone mflowgen
# echo "--- CLONE *AND INSTALL* MFLOWGEN REPO"
# [ "$VERBOSE" == "true" ] && (echo ""; echo "--- pwd="`pwd`; echo "")
# if [ "$USER" == "buildkite-agent" ]; then
#     build=$garnet/mflowgen/test
# else
#     build=/sim/$USER
# fi
# 
# # CLONE
# test  -d $build || mkdir $build; cd $build
# test  -d $build/mflowgen || git clone https://github.com/cornell-brg/mflowgen.git
# mflowgen=$build/mflowgen
# 
# # INSTALL
# pushd $mflowgen
#   TOP=$PWD; pip install -e .; which mflowgen; pip list | grep mflowgen
# popd
# echo ""
########################################################################


########################################################################
# OLD ADK SETUP - delete after new code (below) has successfully
# completed a build or two...
########################################################################
# echo "--- ADK SETUP / CHECK"
# 
# # Copy the tsmc16 views into the adks directory.  Note the adks must
# # be touchable by current user, thus must copy locally and cannot
# # e.g. use symlink to someone else's existing adk.
# 
# # Find the tsmc16 libraries
# 
# # Check out official adk repo?
# #   test -d tsmc16-adk || git clone http://gitlab.r7arm-aha.localdomain/alexcarsello/tsmc16-adk.git
# # Yeah, no, that ain't gonna fly. gitlab repo requires username/pwd permissions and junk
# # Instead, let's just use a cached copy
# 
# # FIXME/TODO check to see if user can use official repo,
# # if so use that instead of cached copy, e.g.
# 
# # FIXME/TODO give buildkite-agent permission to use official repo
# 
# # tsmc16=/sim/steveri/mflowgen/adks/tsmc16-adk
# tsmc16=/sim/steveri/mflowgen/adks/tsmc16
# echo copying adk from $tsmc16
# ls -l $tsmc16
# 
# # Symlink to steveri no good. Apparently need permission to "touch" adk files(??)
# # test -e tsmc16 || ln -s ${tsmc16} tsmc16
# 
# set -x
# echo COPYING IN A FRESH ADK
# 
# # Copy to cache (gold) dir if that was requested, else use default
# if [ "$build_dir" ]; then
#     test -d $build_dir/mflowgen/adks || mkdir -p $build_dir/mflowgen/adks
#     # cp -rpf $build/mflowgen/adks $build_dir/mflowgen
#     adks=$build_dir/mflowgen/adks
# else
#     adks=$build/mflowgen/adks
# fi
# 
# if test -d $adks/tsmc16; then
#     echo Using existing adks $adks/tsmc16
# else
#     echo "Copying adks from '$tscm16' to '$adks'"
#     set -x; cp -rpH $tsmc16 $adks; set +x
# fi
# 
# export MFLOWGEN_PATH=$adks
# echo "Set MFLOWGEN_PATH=$MFLOWGEN_PATH"; echo ""
