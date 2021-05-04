#!/bin/bash

# Set up environment to run a buildkite test in the indicated directory.
# Examples:
#     source setup-buildkite.sh --dir /build/gold.100/full_chip
#     source setup-buildkite.sh --dir /build/gold.100/full_chip --need_space 30G

# Setup script "source setup-buildkite.sh --dir <d>" does the following:
#   - if unset yet, sets GARNET_HOME to wherever the setup script lives
#   - checks dir <d> for sufficient disk space;
#   - sets TMPDIR to /sim/tmp
#   - sets python env BUT ONLY if you're running as buildkite-agent
#   - source garnet-setup.sh for CAD paths
#   - finds or creates requested build directory
#   - makes local link to mflowgen repo "/sim/buildkite-agent/mflowgen"
#   - makes local copy of adk


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

# Default is to use pre-built RTL from docker,
# so no need for elaborate garnet python env
PIP_INSTALL_REQUIREMENTS=false

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

        --pip_install_requirements) shift; PIP_INSTALL_REQUIREMENTS=true; ;;

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

# If server dies and reboots, agent can lose access to file system(!)
if expr $build_dir : /build > /dev/null; then
  if ! test -d /build; then
      echo "**ERROR: Cannot find dir '/build'; may need to restart buildkite agent(s)"
      return 13 || exit 13
  fi
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

    # Can skip requirements if using prebuilt RTL (--pip_install_requirements)
    if [ "$PIP_INSTALL_REQUIREMENTS" == "true" ]; then
        pip install -U --exists-action s -r $garnet/requirements.txt
    else
        echo "INFO Not building RTL from scratch, so no need for requirements.txt"
    fi
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
echo Sourcing $garnet/mflowgen/setup-garnet.sh ...
source $garnet/mflowgen/setup-garnet.sh

##############################################################################
# Recheck python/pip versions b/c CAD modules can muck them up :(
echo Recheck python/pip versions
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


########################################################################
# MFLOWGEN: Use a single common mflowgen for all builds of a given branch
# 
# Mar 2102 - Added option to use a different mflowgen branch when/if desired

mflowgen_branch=master
echo "--- INSTALL LATEST MFLOWGEN using branch '$mflowgen_branch'"

mflowgen=/sim/buildkite-agent/mflowgen
if [ "$mflowbranch" != "master" ]; then
    mflowgen=/sim/buildkite-agent/mflowgen.$mflowgen_branch
fi

# Mar 2102 - Without a per-build mflowgen clone, cannot guarantee
# persistence of non-master branch through to end of run.  The cost
# of making local mflowgen clones is currently about 200M build.

# Build repo if not exists yet
if ! test -e $mflowgen; then
    git clone -b $mflowgen_branch \
        -- https://github.com/mflowgen/mflowgen.git $mflowgen
fi

echo "Install mflowgen using repo in dir '$mflowgen'"
pushd $mflowgen
  git checkout $mflowgen_branch; git pull
  TOP=$PWD; pip install -e .; which mflowgen; pip list | grep mflowgen
popd

echo ""


########################################################################
# NEW ADK SETUP --- see far below for old setup
########################################################################
echo "--- ADK SETUP / CHECK"

echo 'COPY LATEST ADK TO MFLOWGEN REPO'

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

########################################################################
# TCLSH VERSION CHECK
########################################################################
# 
# tclsh version must be >= 8.5!  Because of e.g.
#    "delay_best" in $vars(delay_corners)
# in flowgen-setup/setup.tcl
# 
# For reference, I can see these versions in my various open windows
#   kiwi/stever:  tclsh v8.6 (/usr/bin/tclsh)
#   r7arm/agent:  tclsh v8.5 (/usr/bin/tclsh)
#   r7arm/stever: tclsh v8.4 (/cad/mentor/2019.1/aoi_cal_2019.1_18.11/bin/tclsh
# 
# An example path that breaks tclsh:
#   % source $garnet/.buildkite/setup-calibre.sh
#   % which tclsh => 'tclsh is /cad/mentor/2019.1/aoi_cal_2019.1_18.11/bin/tclsh'
#   % echo 'puts $tcl_version; exit 0' | tclsh => 8.4
# 
echo "--- TCLSH VERSION CHECK (must be >= 8.5)"

# Uncomment to reset tclsh for testing
# unset -f tclsh; source $garnet/.buildkite/setup-calibre.sh
tclsh_version=`echo 'puts $tcl_version; exit 0' | tclsh`
echo "  "`type tclsh`", version $tclsh_version"
if (( $(echo "$tclsh_version >= 8.5" | bc -l) )); then
    echo '  Good enough!'
else
    echo ""
    echo "**WARNING tclsh version should be >= 8.5!"
    echo "I will try and fix it for you"
    echo ""
    FIXED=
    # Lowest impact solution is maybe to give tclsh its own little directory
    TBIN=~/bin-tclsh-fix
    export PATH=${TBIN}:${PATH}
    tclsh_version=`echo 'puts $tcl_version; exit 0' | tclsh`
    if (( $(echo "$tclsh_version >= 8.5" | bc -l) )); then
        echo "  - FIXED! Found good $TBIN/tclsh"
        ls -l $TBIN/tclsh
        FIXED=true
    else
        echo "  - ${TBIN}/tclsh no good; looking for a new one"
        test -d $TBIN && /bin/rm -rf $TBIN; mkdir -p $TBIN
        for d in $( echo $PATH | sed 's/:/ /g' ); do 
            if test -x $d/tclsh; then
                tclsh_version=`echo 'puts $tcl_version; exit 0' | $d/tclsh`
                echo -n "  Found tclsh v$tclsh_version: $d/tclsh"
                if (( $(echo "$tclsh_version < 8.5" | bc -l) )); then
                    echo "  - no good"
                else
                    # Clever! But...functions don't survive into called scripts :(
                    # eval 'function tclsh { '$d/tclsh' $* ; }'

                    # So add it to ~/bin I guess
                    echo '  - GOOD! Adding to ~/bin'
                    (cd $TBIN; ln -s $d/tclsh; ls -l)
                    FIXED=true
                    break
                fi
            fi
        done
    fi
    if [ ! $FIXED ]; then
        echo "**ERROR could not find tclsh with version >= 8.5!"
        return 13 || exit 13
    fi
    echo ""
    echo "  "`type tclsh`", version $tclsh_version"
fi
echo ""
