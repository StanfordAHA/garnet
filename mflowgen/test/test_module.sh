#!/bin/bash

function help {
    cat <<EOF

Usage: $0 [OPTION] <module>,<subgraph>,<subsubgraph>... --steps <step1>,<step2>...

Options:
  -v, --verbose VERBOSE mode
  -q, --quiet   QUIET mode
  -h, --help    help and examples
  --debug       DEBUG mode

  --branch <b>        only run test if in git branch <b>
  --step <s1,s2,...>       step(s) to run in the indicated (sub)graph. default = 'lvs,drc'
  --use_cache <s1,s2,...>  list of steps to copy from gold cache before running test(s)
  --update_cache <c>       update cache <c> after each step

Examples:
    $0 Tile_PE
    $0 Tile_MemCore
    $0 Tile_PE --branch 'devtile*'
    $0 --verbose Tile_PE --steps synthesis,lvs
    $0 full_chip tile_array Tile_PE --steps synthesis
    $0 full_chip tile_array Tile_PE --steps synthesis --use_cache Tile_PE,Tile_MemCore
    
EOF
}

########################################################################
# Args / switch processing
modlist=()
VERBOSE=false
build_sequence='lvs,gls'
update_cache=
while [ $# -gt 0 ] ; do
    case "$1" in
        -h|--help)    help; exit;    ;;
        -v|--verbose) VERBOSE=true;  ;;
        -q|--quiet)   VERBOSE=false; ;;
        --debug)      DEBUG=true;    ;;
        --branch*)    shift; branch_filter="$1";  ;;
        --step*)      shift; build_sequence="$1"; ;;
        --use_cache*) shift; use_cached="$1"; ;;
        --update*)    shift; update_cache="$1"; ;;

        -*)
            echo "***ERROR unrecognized arg '$1'"; help; exit; ;;
        *)
            modlist+=($1); ;;
    esac
    shift
done
        
if [ "$DEBUG"=="true" ]; then
    VERBOSE=true
fi

# Function to expand step aliases
# E.g. 'step_alias syn' returns 'synopsys-dc-synthesis'
function step_alias {
    case "$1" in

        # "synthesis" will expand to dc or genus according to what's in "make list"
        syn)       s=synthesis ;;

        init)      s=cadence-innovus-init      ;;
        cts)       s=cadence-innovus-cts       ;;
        place)     s=cadence-innovus-place     ;;
        route)     s=cadence-innovus-route     ;;
        postroute) s=cadence-innovus-postroute ;;

        gds)       s=mentor-calibre-gdsmerge ;;
        tape)      s=mentor-calibre-gdsmerge ;;
        merge)     s=mentor-calibre-gdsmerge ;;
        gdsmerge)  s=mentor-calibre-gdsmerge ;;

        lvs)       s=mentor-calibre-lvs ;;
        drc)       s=mentor-calibre-drc ;;

        *)         s="$1" ;;
    esac

    # Catch-all maybe?  Whether or not alias succeeded, can grep
    # through "make" listing to clean up the step name.
    # E.g. maybe "postroute_hold" expands here to "cadence-innovus-postroute_hold
    # Grab the *first* hit to aviod e.g. all the "debug-" aliases
    s=`make list |& egrep -- "$s"'$' | awk '{ print $NF; exit }'`

    echo $s ; # return value
}

########################################################################
# Turn build sequence into an array e.g. 'lvs,gls' => 'lvs gls'
build_sequence=`echo $build_sequence | tr ',' ' '`

if [ "$DEBUG"=="true" ]; then
    # ---
    echo "MODULES and subgraphs to build"
    for m in ${modlist[@]};           do echo "  m=$m"; done
    # ---
    echo "STEPS to take"
    for step in ${build_sequence[@]}; do echo "  $step"; done
fi

########################################################################
# Turn copy list into an array e.g. 'Tile_PE,rtl' => 'Tile_PE,rtl'
copy_list=()
if [ "$use_cached" ]; then
    copy_list=`echo $use_cached | tr ',' ' '`
    echo YES FOUND COPY LIST
    for step in ${copy_list[@]}; do
        echo $step
    done
fi

########################################################################
if [ "$branch_filter" ]; then
    echo '+++ BRANCH FILTER'
    echo ""
    echo "Note tests only work in branches that match regexp '$branch_filter'"
    if [ "$BUILDKITE_BRANCH" ]; then
        branch=${BUILDKITE_BRANCH}
        echo "It looks like we are running from within buildkite"
        echo "And it looks like we are in branch '$branch'"

    else 
        branch=`git symbolic-ref --short HEAD`
        echo "It looks like we are *not* running from within buildkite"
        echo "We appear to be in branch '$branch'"
    fi
    echo ""

    # Note DOES NOT WORK if $branch_filter is in quotes e.g. "$branch_filter" :o
    if [[ "$branch" =~ $branch_filter ]]; then
        echo "Okay that's the right branch, off we go."
    else
        # Test is disabled for this branch, emit a polite info message and leave.
        if [ "$BUILDKITE_LABEL" ]; then
            # https://buildkite.com/docs/agent/v3/cli-annotate
            cmd="buildkite-agent annotate --append"
            label="$BUILDKITE_LABEL"
        else
            cmd='cat'
            label=${modlist[0]}
        fi

        ems='!!!'
        echo "NOTE '$label' TEST DID NOT ACTUALLY RUN$ems"$'\n' | $cmd
        # echo "- Tests only work in branch '$allowed_branch'" | $cmd
        echo "- This test is disabled except for branches that match regex '$branch_filter'" | $cmd
        echo "- and we appear to be in branch '$branch'"$'\n' | $cmd
        exit 0
    fi
fi

# Exit on error in any stage of any pipeline (is this a good idea?)
set -eo pipefail

# Running out of space in /tmp!!?
export TMPDIR=/sim/tmp

# Colons is stupids, define "PASS" to use instead
PASS=:
function PASS { return 0; }

########################################################################
# Find GARNET_HOME
function where_this_script_lives {
  # Where this script lives
  scriptpath=$0      # E.g. "build_tarfile.sh" or "foo/bar/build_tarfile.sh"
  scriptdir=${0%/*}  # E.g. "build_tarfile.sh" or "foo/bar"
  if test "$scriptdir" == "$scriptpath"; then scriptdir="."; fi
  # scriptdir=`cd $scriptdir; pwd`
  (cd $scriptdir; pwd)
}
script_home=`where_this_script_lives`

# setup assumes this script lives in garnet/mflowgen/test/
garnet=`cd $script_home/../..; pwd`

# Oop "make rtl" (among others maybe) needs GARNET_HOME env var
export GARNET_HOME=$garnet


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

if [ "$USER" == "buildkite-agent" ]; then
    echo "--- ENVIRONMENT"; echo ""

    venv=/usr/local/venv_garnet
    if test -d $venv; then
        echo "USE PRE-BUILT PYTHON VIRTUAL ENVIRONMENT"
        source $venv/bin/activate
    else
        echo "CANNOT FIND PRE-BUILT PYTHON VIRTUAL ENVIRONMENT"
        echo "- building a new one from scratch"
        # JOBDIR should be per-buildstep environment e.g.
        # /sim/buildkite-agent/builds/bigjobs-1/tapeout-aha/
        JOBDIR=$BUILDKITE_BUILD_CHECKOUT_PATH
        pushd $JOBDIR
          /usr/local/bin/python3 -m venv venv ;# Builds "$JOBDIR/venv" maybe
          source $JOBDIR/venv/bin/activate
        popd
    fi

    check_pyversions
    # pip install -r $garnet/requirements.txt
    # Biting the bullet; also, it's the right thing to do I guess
    pip install -U -r $garnet/requirements.txt
fi

# Lots of useful things in /usr/local/bin. coreir for instance ("type"=="which")
# echo ""; type coreir
export PATH="$PATH:/usr/local/bin"; hash -r
# type coreir; echo ""

# Set up paths for innovus, genus, dc etc.
# source $garnet/.buildkite/setup.sh
# source $garnet/.buildkite/setup-calibre.sh
# Use the new stuff
source $garnet/mflowgen/setup-garnet.sh

# Recheck python/pip versions b/c CAD modules can muck them up :(
check_pyversions

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
# Make a build space for mflowgen; clone mflowgen
echo "--- CLONE *AND INSTALL* MFLOWGEN REPO"
[ "$VERBOSE" == "true" ] && (echo ""; echo "--- pwd="`pwd`; echo "")
if [ "$USER" == "buildkite-agent" ]; then
    build=$garnet/mflowgen/test
else
    build=/sim/$USER
fi

# CLONE
test  -d $build || mkdir $build; cd $build
test  -d $build/mflowgen || git clone https://github.com/cornell-brg/mflowgen.git
mflowgen=$build/mflowgen

# INSTALL
pushd $mflowgen
  TOP=$PWD; pip install -e .; which mflowgen; pip list | grep mflowgen
popd
echo ""

########################################################################
# ADK SETUP / CHECK

echo "--- ADK SETUP / CHECK"
if [ "$USER" == "buildkite-agent" ]; then
    pushd $mflowgen/adks

    # Check out official adk repo?
    #   test -d tsmc16-adk || git clone http://gitlab.r7arm-aha.localdomain/alexcarsello/tsmc16-adk.git
    # Yeah, no, that ain't gonna fly. gitlab repo requires username/pwd permissions and junk
    # Instead, let's just use a cached copy
    # cached_adk=/sim/steveri/mflowgen/adks/tsmc16-adk
    cached_adk=/sim/steveri/mflowgen/adks/tsmc16
    echo copying adk from ${cached_adk}
    ls -l ${cached_adk}

    # Symlink to steveri no good. Apparently need permission to "touch" adk files(??)
    # test -e tsmc16 || ln -s ${cached_adk} tsmc16
    if test -e tsmc16; then
        echo WARNING destroying and replacing existing adk/tsmc16
        set -x; /bin/rm -rf tsmc16; set +x
    fi
    echo COPYING IN A FRESH ADK
    set -x; cp -rpH ${cached_adk} .; set +x
    popd
fi
export MFLOWGEN_PATH=$mflowgen/adks
echo "Set MFLOWGEN_PATH=$MFLOWGEN_PATH"; echo ""

# Optionally update cache with adk info
if [ "$update_cache" ]; then
    gold="$update_cache"
    echo "--- SAVE ADK to cache '$gold'"
    test -d $gold || mkdir $gold
    test -d $gold/mflowgen || mkdir $gold/mflowgen
    echo cp -rpf $build/mflowgen/adks $gold/mflowgen
    cp -rpf $build/mflowgen/adks $gold/mflowgen
    ls -l $gold/mflowgen/adks || PASS
fi

##################################################################
# HIERARCHICAL BUILD AND RUN
echo "--- HIERARCHICAL BUILD AND RUN"
if [ "$DEBUG" ]; then
    echo firstmod=${modlist[0]}; echo subgraphs=\(${modlist[@]:1}\)
fi

function build_module {
    modname="$1"; # E.g. "full_chip"
    echo "--- ...BUILD MODULE '$modname'"

    if [ "$update_cache" ]; then
        # Build and run from requested target cache directory
        gold="$update_cache"; # E.g. gold="/sim/buildkite-agent/gold.13"
        # test -d $gold/$modname || mkdir $gold/$modname
        # or could use mkdir -p maybe?
        echo "mkdir -p $gold/$modname; ln -s $gold/$modname; cd $modname"
        mkdir -p $gold/$modname; ln -s $gold/$modname; cd $modname
    else
        # Run from default buildkite build directory as usual
        echo "mkdir $modname; cd $modname"
        mkdir $modname; cd $modname
    fi
    echo "mflowgen run --design $garnet/mflowgen/$modname"
    mflowgen run --design $garnet/mflowgen/$modname
}
function build_subgraph {
    modname="$1" ; # E.g. "Tile_PE"

    # Find appropriate directory name for subgraph e.g. "14-tile_array"
    # We're looking for a "make list" line that matches modname e.g.
    # " -   1 : Tile_PE"
    # In which case we build a prefix "1-" so as to build subdir "1-Tile_PE"
    set -x; make list | awk '$NF == "'$modname'" {print}'; set +x
    modpfx=`make list | awk '$NF == "'$modname'" {print $2 "-"}'`
    dirname=$modpfx$modname; # E.g. "1-Tile_PE"
    echo "--- ...BUILD SUBGRAPH '$dirname'"
    
    echo "mkdir $dirname; cd $dirname"
    mkdir $dirname; cd $dirname
    
    echo "mflowgen run --design $garnet/mflowgen/$modname"
    mflowgen run --design $garnet/mflowgen/$modname
}

# FIXME where does this belong?
[ "$MFLOWGEN_PATH" ] || echo "WARNING MFLOWGEN_PATH var not set."
    
# First mod in list is the primary module; rest are subgraphs. Right?
# Also: in general, first mod should be "full_chip" but not currently enforced.
# E.g. modlist=(full_chip tile_array Tile_PE)

# Top level
firstmod=${modlist[0]}
build_module $firstmod

# Subgraphs
subgraphs=${modlist[@]:1}
for sg in $subgraphs; do
    build_subgraph $sg
    echo sg=$sg
done

echo "STEPS to take"
for step in ${build_sequence[@]}; do
    echo "  $step -> `step_alias $step`"
done

##############################################################################
# Copy pre-built steps from (gold) cache, if requested via '--use_cached'
if [ "$copy_list" ]; then 
    echo "+++ ......SETUP context from gold cache (`date +'%a %H:%M'`)"

    # Build the path to the gold cache
    gold=/sim/buildkite-agent/gold
    for m in ${modlist[@]}; do 
        ls $gold/*${m} >& /dev/null || echo FAIL
        ls $gold/*${m} >& /dev/null || FAIL=true
        if [ "$FAIL" == "true" ]; then
            echo "***ERROR could not find cache dir '$gold'"; exit 13; fi
        gold=`cd $gold/*${m}; pwd`
    done
    [ "$DEBUG" ] && echo "  Found gold cache directory '$gold'"

    # Copy desired info from gold cache
    for step in ${copy_list[@]}; do
        
        # Expand aliases e.g. "syn" -> "synopsys-dc-synthesis"
        # echo "  $step -> `step_alias $step`"
        step=`step_alias $step`
    
#         set -x
#         if ! test -d $cache; then 
#             echo "WARNING Could not find cache for step '${step'"
#             echo "Will try and go on without it..."
#             continue
#         fi

        # NOTE if cd command fails, pwd (disastrously) defaults to current dir
        # cache=`cd $gold/*${step}; pwd` || FAIL=true
        # if [ "$FAIL" == "true" ]; then
        #     echo "***ERROR could not find cache dir '$gold'"; exit 13
        # fi

        cache=`cd $gold/*${step}` || FAIL=true
        if [ "$FAIL" == "true" ]; then
            echo "WARNING Could not find cache for step '${step}'"
            echo "Will try and go on without it..."
            continue
        fi

        cache=`cd $gold/*${step}; pwd`
        echo "    cp -rpf $cache ."
        cp -rpf $cache .
    done
fi

# Not ready for prime time, save for next go-round
# # TEST
# # for step in -route route rdl timing-signoff; do
# #     echo "FOOOO  '$step' -> '`step_alias $step`'"
# 
# ##############################################################################
# # Copy pre-built steps from (gold) cache, if requested via '--use_cached'
# if [ "$copy_list" ]; then 
#     stash_dir=/sim/buildkite-agent/stash/2020-0806-mflowgen-stash-8b4ada
#     mflowgen stash link --path $stash_dir; echo ''
# 
#     # Copy desired info from gold cache
#     for step in ${copy_list[@]}; do
# 
#         # Expand aliases e.g. "syn" -> "synopsys-dc-synthesis"
#         echo "  $step -> `step_alias $step`"
#         step=`step_alias $step`
# 
#         echo "+++ FOO Nothing up my sleeve. Is this your step?"
#         echo ""
#         set -x; make list | egrep "$step"'$' | awk '{ print $NR }'; set +x
#         echo ""
# 
#         stash_path=`echo $firstmod ${modlist[@]}` ; # E.g. 'full_chip tile_array'
# 
#         # E.g. "- 495f05 [ 2020-0807 ] buildkite-agent Tile_MemCore -- full_chip tile_array Tile_MemCore"
#         # mflowgen stash list --all | egrep "${stashpath}.*${step}\$" || echo ''
#         hash=`mflowgen stash list --all | egrep "${stashpath}.*${step}\$" | awk '{print $2}' || echo ''`
# 
#         # The hash is yellow. Yellow.
#         # That means instead of 495f05 I get '\033]0;%s@%s:%s\007'
#         # God damn it.
# 
#         # Thanks stackoverflow
#         echo -n "Fetching step '$step'..."
#         hash=`echo $hash | sed "s,\x1B\[[0-9;]*[a-zA-Z],,g"`
#         echo mflowgen stash pull --hash $hash
#         mflowgen stash pull --hash $hash || echo ''
#         echo '---'
#     done
# fi

########################################################################
# Run the makefiles for each step requested via '--step'

function PASS { return 0; }
touch .stamp; # Breaks if don't do this before final step; I forget why...? Chris knows...
for step in ${build_sequence[@]}; do

    # Expand aliases e.g. "syn" -> "synopsys-dc-synthesis"
    step_orig=$step; step=`step_alias $step`
    echo "================================================================"
    echo "    Ready to do step $step_orig -> $step"
    # [ "$DEBUG" ] && echo "    $step_orig -> $step"

    echo "+++ ......TODO list for step $step (`date +'%a %H:%M'`)"
    make -n $step > /dev/null || PASS ; # Get error messages, if any, maybe.
    make -n $step | grep 'mkdir.*output' | sed 's/.output.*//' | sed 's/mkdir -p/  make/' || PASS

    echo "--- ......MAKE $step (`date +'%a %H:%M'`)"

    # Use filters to make buildkite log more readable/useful
    test -f $script_home/filters/$step.awk \
        && filter="gawk -f $script_home/filters/$step.awk" \
            || filter="cat"

    # Try a thing with this "touch" command
    failfile=/tmp/test_module_failfile.$$
    test -f $failfile && /bin/rm $failfile || echo -n ''
    (make $step || touch $failfile) |& tee make-$step.log | $filter
    # if [ "$FAIL" ]; then
    if test -f $failfile; then
        /bin/rm $failfile
        echo '+++ RUNTIMES'; make runtimes
        echo '+++ FAIL'
        echo 'Looks like we failed, here are some errors maybe:'
        echo grep -i error mflowgen-run.log
        grep -i error mflowgen-run.log
        exit 13
    fi

# Don't need this no more. maybe. if all goes well. then i promis i'll delete it
#     # Optionally update (gold) cache after each step
#     if [ "$update_cache" ]; then
#         gold="$update_cache"; # E.g. gold="/sim/buildkite-agent/gold.13"
#         echo "+++ SAVE RESULTS so far to cache '$gold'"
#         test -d $gold || mkdir $gold
#         set -x
#         cp -rpf $build/full_chip $gold
#         set +x
#         ls -l $gold/full_chip || PASS
#     fi
    
done

##############################################################################
# FIXME/TODO Use this code to implement a caching mechanism e.g. '--update_cache' or something
# # $mflowgen is e.g. "/sim/buildkite-agent/builds/bigjobs-1/tapeout-aha/mflowgen/mflowgen/test/mflowgen"
# # But we want:
# # ls -ld /sim/buildkite-agent/builds/bigjobs-1/tapeout-aha/mflowgen/mflowgen/test/mflowgen/adks
# # ls -ld /sim/buildkite-agent/builds/bigjobs-1/tapeout-aha/mflowgen/mflowgen/test/full_chip
# # And we think that
# # build=/sim/buildkite-agent/builds/bigjobs-1/tapeout-aha/mflowgen/mflowgen/test
# 
# final_module=${modlist[-1]}
# 
# set -x
# echo '+++ TEMPORARY hack to save results in gold cache'
# if [ "$final_module" == "tile_array" ]; then
#   gold=/sim/buildkite-agent/gold.$$
#   test -d $gold || mkdir $gold
#   test -d $gold/mflowgen || mkdir $gold/mflowgen
# 
#   a=$build/mflowgen/adks; ls -ld $a
#   fc=$build/full_chip;    ls -ld $fc
# 
#   cp -rpf $build/mflowgen/adks $gold/mflowgen
#   cp -rpf $build/full_chip $gold
# fi
##############################################################################

echo '+++ PASS/FAIL info maybe, to make you feel good'
function PASS { return 0; }
cat -n make*.log | grep -i error  | tail | tee -a tmp.summary || PASS; echo "-----"
cat -n make*.log | grep    FAIL   | tail | tee -a tmp.summary || PASS; echo "-----"
cat -n make*.log | grep -i passed | tail | tee -a tmp.summary || PASS; echo ""

########################################################################
echo '+++ SUMMARY of what we did'
f=make.log
cat -n $f | grep 'mkdir.*output' | sed 's/.output.*//' | sed 's/mkdir -p/  make/' \
    >> tmp.summary \
    || PASS
cat tmp.summary

########################################################################
echo '+++ RUNTIMES'; make runtimes

echo ""; pwd; ls -l .stamp; cat .stamp || PASS; echo "Time now: `date`"

grep AssertionError tmp.summary && echo '------' || PASS
grep AssertionError tmp.summary && exit 13 || PASS

exit

# ##############################################################################
# ##############################################################################
# ##############################################################################
# # OLD STUFF, much of which we will want to reuse eventually...
# # So DON'T DELETE (yet)
# 
# exit_unless_verbose="exit 13"
# # Don't want this no more
# # [ "VERBOSE" == "true" ] && \
# #     exit_unless_verbose="echo ERROR but continue anyway"
# 
# module=${modlist[0]}
# 
# # test_module.sh full_chip tile_array Tile_PE
# # scp kiwi:/nobackup/steveri/github/garnet/mflowgen/test/test_module.sh .
# 
# ##############################################################################
# # Don't write over existing module
# if test -d $mflowgen/$module; then
#     echo "oops $mflowgen/$module exists already, not gonna write over that"
#     echo "giving up now love ya bye-bye"
#     exit 13
# fi
# 
# # e.g. module=Tile_PE or Tile_MemCore
# echo ""; set -x
# mkdir $mflowgen/$module; cd $mflowgen/$module
# ../configure --design $garnet/mflowgen/$module
# set +x; echo ""
# 
# # Targets: run "make list" and "make status"
# # make list
# #
# # echo "make mentor-calibre-drc \
# #   |& tee mcdrc.log \
# #   | gawk -f $script_home/filter.awk"
# 
# # ########################################################################
# # # Makefile assumes "python" means "python3" :(
# # # Note requirements_check.sh (above) not sufficient to fix this :(
# # # Python check
# # echo "--- PYTHON=PYTHON3 FIX"
# # v=`python -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
# # echo "Found python version $v -- should be at least 3007"
# # if [ $v -lt 3007 ] ; then
# #   echo ""
# #   echo "WARNING found python version $v -- should be 3007"
# #   echo "WARNING I will try and fix it for you with my horrible hackiness"
# #   # On arm7 machine it's in /usr/local/bin, that's just how it is
# #   echo "ln -s bin/python /usr/local/bin/python3"
# #   test -d bin || mkdir bin
# #   (cd bin; ln -s /usr/local/bin/python3 python)
# #   export PATH=`pwd`/bin:"$PATH"
# #   hash -r
# #   v=`python -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
# #   echo "Found python version $v -- should be at least 3007"
# #   if [ $v -lt 3007 ] ; then
# #     echo ""; echo 'ERROR could not fix python sorry!!!'
# #   fi
# #   echo
# # fi
# # echo ""
# 
# 
# set -x
# which python; which python3
# set +x
# 
# 
# 
# if [ "$USER" != "buildkite-agent" ]; then
#     # # Prime the pump w/req-chk results
#     cat $tmpfile.reqchk > mcdrc.log; /bin/rm $tmpfile.reqchk
#     echo "----------------------------------------" >> mcdrc.log
# fi
# 
# 
# FILTER="gawk -f $script_home/rtl-filter.awk"
# [ "$VERBOSE" == "true" ] && FILTER="cat"
# 
# # echo VERBOSE=$VERBOSE
# # echo FILTER=$FILTER
# 
# nobuf='stdbuf -oL -eL'
# 
# # FIXME use mymake below in place of various "make" sequences
# function mymake {
#     make_flags=$1; target=$2; log=$3
#     unset FAIL
#     nobuf='stdbuf -oL -eL'
#     # make mentor-calibre-drc < /dev/null
#     echo make $make_flags $target
#     make $make_flags $target < /dev/null \
#         |& $nobuf tee -a ${log} \
#         |  $nobuf gawk -f $script_home/post-rtl-filter.awk \
#         || FAIL=1
#     if [ "$FAIL" ]; then
#         echo ""
#         sed -n '/^====* FAILURES/,$p' $log
#         $exit_unless_verbose
#     fi
#     unset FAIL
# }
# 
# # So. BECAUSE makefile fails silently (and maybe some other good
# # reasons as well), we now do (at least) two stages of build.
# # "make rtl" fails frequently, so that's where we'll put the
# # first break point
# #
# echo "--- MAKE RTL"
# make_flags=""
# [ "$VERBOSE" == "true" ] && make_flags="--ignore-errors"
# mymake "$make_flags" rtl mcdrc.log|| $exit_unless_verbose
# 
# if [ ! -e *rtl/outputs/design.v ] ; then
#     echo ""; echo ""; echo ""
#     echo "***ERROR Cannot find design.v, make-rtl musta failed"
#     echo ""; echo ""; echo ""
#     $exit_unless_verbose
# else
#     echo ""
#     echo Built verilog file *rtl/outputs/design.v
#     ls -l *rtl/outputs/design.v
#     echo ""
# fi
# 
# # For pad_frame, want to check bump connections and FAIL if problems
# if [ "$module" == "pad_frame" ] ; then
#   echo "--- MAKE SYNTHESIS"
#   make_flags="--ignore-errors"
#   target="synopsys-dc-synthesis"
#   mymake "$make_flags" $target make-syn.log || $exit_unless_verbose
# 
#   echo "--- MAKE INIT"
#   make_flags=""
#   [ "$VERBOSE" == "true" ] && make_flags="--ignore-errors"
#   target="cadence-innovus-init"
#   echo "exit_unless_verbose='$exit_unless_verbose'"
#   mymake "$make_flags" $target make-init.log || $exit_unless_verbose
# 
#   # Check for errors
#   log=make-init.log
#   echo ""
# 
#   grep '^\*\*ERROR' $log
#   echo '"not on Grid" errors okay (for now anyway) I guess'
#   # grep '^\*\*ERROR' $log | grep -vi 'not on grid' ; # This throws an error when second grep succeeds!
#   n_errors=`grep '^\*\*ERROR' $log | grep -vi 'not on Grid' | wc -l` || $PASS
#   echo "Found $n_errors non-'not on grid' errors"
#   test "$n_errors" -gt 0 && echo "That's-a no good! Bye-bye."
#   test "$n_errors" -gt 0 && exit 13
#   # exit
# fi
# 
# # Trying something new
# ########################################################################
# # New tests, for now trying on Tile_PE and Tile_MemCore only
# # TODO: pwr-aware-gls should be run only if pwr_aware flag is 1
# if [ "$module" == "Tile_PE" ] ; then
# 
# #     echo "--- DEBUG TIME"
# #     set -x
# #     pwd
# #     ls conf* || echo not there yet
# #     set +x
# # 
# #     echo "--- MAKE LVS"
# #     make mentor-calibre-lvs
# # 
# #     echo "--- MAKE GLS"
# #     make pwr-aware-gls
# 
#     for step in $build_sequence; do
#         echo "--- MAKE $step"
#         [ "$step" == "synthesis" ] && step="synopsys-dc-synthesis"
#         make $step || exit 13
#     done
#     exit 0
# fi
# 
# if [ "$module" == "Tile_MemCore" ] ; then
# 
# #     echo "--- MAKE LVS"
# #     make mentor-calibre-lvs
# # 
# #     echo "--- MAKE GLS"
# #     make pwr-aware-gls
# 
#     for step in $build_sequence; do
#         echo "--- MAKE $step"
#         [ "$step" == "synthesis" ] && step="synopsys-dc-synthesis"
#         make $step || exit 13
#     done
#     exit 0
# fi
# 
# ########################################################################
# 
# echo "--- MAKE DRC"
# make_flags=''
# [ "$VERBOSE" == "true" ] && make_flags="--ignore-errors"
# if [ "$module" == "pad_frame" ] ; then
#     target=init-drc
#     # FIXME Temporary? ignore-errors hack to get past dc synthesis assertion errors.
#     make_flags='--ignore-errors'
# elif [ "$module" == "icovl" ] ; then
#     target=drc-icovl
#     # FIXME Temporary? ignore-errors hack to get past dc synthesis assertion errors.
#     make_flags='--ignore-errors'
# else
#     target=mentor-calibre-drc
# fi
# 
# unset FAIL
# nobuf='stdbuf -oL -eL'
# # make mentor-calibre-drc < /dev/null
# log=mcdrc.log
# echo make $make_flags $target
# make $make_flags $target < /dev/null \
#   |& $nobuf tee -a ${log} \
#   |  $nobuf gawk -f $script_home/post-rtl-filter.awk \
#   || FAIL=1
# 
# # Display pytest failures in detail
# # =================================== FAILURES ===========...
# # ___________________________________ test_2_ ____________...
# # mflowgen-check-postconditions.py:24: in test_2_
# if [ "$FAIL" ]; then
#     echo ""
#     sed -n '/^====* FAILURES/,$p' $log
#     $exit_unless_verbose
# fi
# unset FAIL
# 
# # Error summary. Note makefile often fails silently :(
# echo "+++ ERRORS"
# echo ""
# echo "First twelve errors:"
# grep -i error ${log} | grep -v "Message Sum" | head -n 12 || echo "-"
# 
# echo "Last four errors:"
# grep -i error ${log} | grep -v "Message Sum" | tail -n 4 || echo "-"
# echo ""
# 
# # Did we get the desired result?
# unset FAIL
# ls -l */drc.summary > /dev/null || FAIL=1
# if [ "$FAIL" ]; then
#     echo ""; echo ""; echo ""
#     echo "Cannot find drc.summary file. Looks like we FAILED."
#     echo ""; echo ""; echo ""
#     echo "tail ${log}"
#     tail -100 ${log} | egrep -v '^touch' | tail -8
#     $exit_unless_verbose
# fi
# # echo status=$?
# echo "DRC SUMMARY FILE IS HERE:"
# echo `pwd`/*/drc.summary
# 
# echo ""; echo ""; echo ""
# echo "FINAL RESULT"
# echo "------------------------------------------------------------------------"
# 
# # Given a file containing final DRC results in this format:
# # CELL Tile_PE ................................ TOTAL Result Count = 4
# #     RULECHECK OPTION.COD_CHECK:WARNING ...... TOTAL Result Count = 1
# #     RULECHECK M3.S.2 ........................ TOTAL Result Count = 1
# #     RULECHECK M5.S.5 ........................ TOTAL Result Count = 1
# # --------------------------------------------------------------------
# # Print the results to a temp file prefixed by summary e.g.
# # "2 error(s), 1 warning(s)"; return name of temp file
# function drc_result_summary {
#     # Print results to temp file 1
#     f=$1; i=$2
#     tmpfile=/tmp/tmp.test_pe.$USER.$$.$i; # echo $tmpfile
#     # tmpfile=`mktemp -u /tmp/test_module.XXX`
#     sed -n '/^CELL/,/^--- SUMMARY/p' $f | grep -v SUMM > $tmpfile.1
# 
#     # Print summary to temp file 0
#     n_checks=`  grep   RULECHECK        $tmpfile.1 | wc -l`
#     n_warnings=`egrep 'RULECHECK.*WARN' $tmpfile.1 | wc -l`
#     n_errors=`  expr $n_checks - $n_warnings`
#     echo "$n_errors error(s), $n_warnings warning(s)" > $tmpfile.0
# 
#     # Assemble and delete intermediate temp files
#     cat $tmpfile.0 $tmpfile.1 > $tmpfile
#     rm  $tmpfile.0 $tmpfile.1
#     echo $tmpfile
# }
# 
# 
# # Expected result
# res1=`drc_result_summary $script_home/expected_result/$module exp`
# echo -n "--- EXPECTED "; cat $res1
# n_errors_expected=`awk 'NF=1{print $1; exit}' $res1`
# echo ""
# 
# # Actual result
# res2=`drc_result_summary */drc.summary got`
# echo -n "--- GOT..... "; cat $res2
# n_errors_got=`awk 'NF=1{print $1; exit}' $res2`
# echo ""
# 
# # Diff
# echo "+++ Expected $n_errors_expected errors, got $n_errors_got errors"
# 
# ########################################################################
# # PASS or FAIL?
# if [ $n_errors_got -le $n_errors_expected ]; then
#     rm $res1 $res2
#     echo "GOOD ENOUGH"
#     echo PASS; exit 0
# else
#     # Need the '||' below or it fails too soon :(
#     diff $res1 $res2 | head -40 || echo "-----"
#     rm $res1 $res2
# 
#     # echo "TOO MANY ERRORS"
#     # echo FAIL; $exit_unless_verbose
# 
#     # New plan: always pass if we get this far
#     echo "NEW ERRORS but that's okay we always pass now if we get this far"
#     echo PASS; exit 0
# fi
# 
# 
# # OLD environment build
# # if [ "$USER" == "buildkite-agent" ]; then
# #     echo "--- REQUIREMENTS"
# # 
# #     # /var/lib/buildkite-agent/env/bin/python3 -> python
# #     # /var/lib/buildkite-agent/env/bin/python -> /usr/local/bin/python3.7
# # 
# #     USE_GLOBAL_VENV=false
# #     if [ "$USE_GLOBAL_VENV" == "true" ]; then
# #         # Don't have to do this every time
# #         # ./env/bin/python3 --version
# #         # ./env/bin/python3 -m virtualenv env
# #         source $HOME/env/bin/activate; # (HOME=/var/lib/buildkite-agent)
# #     else
# #         echo ""; echo "NEW PER-STEP PYTHON VIRTUAL ENVIRONMENTS"
# #         # JOBDIR should be per-buildstep environment e.g.
# #         # /sim/buildkite-agent/builds/bigjobs-1/tapeout-aha/
# #         JOBDIR=$BUILDKITE_BUILD_CHECKOUT_PATH
# #         pushd $JOBDIR
# #           /usr/local/bin/python3 -m virtualenv env ;# Builds "$JOBDIR/env" maybe
# #           source $JOBDIR/env/bin/activate
# #         popd
# #     fi
# #     echo ""
# #     echo PYTHON ENVIRONMENT:
# #     for e in python python3 pip3; do which $e || echo -n ''; done
# #     echo ""
# #     pip3 install -r $garnet/requirements.txt
# # fi
# # 
# # THIS IS NOW PART OF REQUIREMENTS_CHECK.SH
# # # Check for memory compiler license
# # if [ "$module" == "Tile_MemCore" ] ; then
# #     if [ ! -e ~/.flexlmrc ]; then
# #         cat <<EOF
# # ***ERROR I see no license file ~/.flexlmrc
# # You may not be able to run e.g. memory compiler
# # You may want to do e.g. "cp ~ajcars/.flexlmrc ~"
# # EOF
# #     else
# #         echo ""
# #         echo FOUND FLEXLMRC FILE
# #         ls -l ~/.flexlmrc
# #         cat ~/.flexlmrc
# #         echo ""
# #     fi
# # fi
# # 
# # # Lots of useful things in /usr/local/bin. coreir for instance ("type"=="which")
# # # echo ""; type coreir
# # export PATH="$PATH:/usr/local/bin"; hash -r
# # # type coreir; echo ""
# # 
# # # Set up paths for innovus, genus, dc etc.
# # source $garnet/.buildkite/setup.sh
# # source $garnet/.buildkite/setup-calibre.sh
# # 
# # # OA_HOME weirdness
# # echo "--- UNSET OA_HOME"
# # echo ""
# # echo "buildkite (but not arm7 (???)) errs if OA_HOME is set"
# # echo "BEFORE: OA_HOME=$OA_HOME"
# # echo "unset OA_HOME"
# # unset OA_HOME
# # echo "AFTER:  OA_HOME=$OA_HOME"
# # echo ""
# # 
# # # Oop "make rtl" (among others maybe) needs GARNET_HOME env var
# # export GARNET_HOME=$garnet
# 
# # OLD - check failed to find the targeted bug...
# #     # Quick check of adk goodness maybe
# #     iocells_bk=./tsmc16/stdview/iocells.lef
# #     iocells_sr=/sim/steveri/mflowgen/adks/tsmc16/stdview/iocells.lef
# #     pwd
# #     ls -l $iocells_bk $iocells_sr
# #     if diff $iocells_bk $iocells_sr; then
# #         echo YESSSSS maybe we got the right adk finally
# #         echo 'note btw this is the "right" one in that this is the one that is supposed to fail...'
# #     else
# #         echo NOOOOOO looks like we continue to screw up with the adks
# #         exit 13
# #     fi
# #     set +x

##############################################################################
##############################################################################
##############################################################################
# OLD / DELETABLE
# None? There's no none.
#     if [ "$step" == "none" ]; then 
#         echo '--- DONE (for now)'
#         echo pre-exit pwd=`pwd`
#         exit
#     fi
#     if [ "$step" == "copy" ]; then 
#         echo "--- ......SETUP context from gold cache (`date +'%a %H:%M'`)"
#         gold=/sim/buildkite-agent/gold
# 
#         echo cp -rpf $gold/full_chip/*tile_array/0-Tile_MemCore .
#         cp -rpf $gold/full_chip/*tile_array/0-Tile_MemCore .
#         
#         echo cp -rpf $gold/full_chip/*tile_array/1-Tile_PE .
#         cp -rpf $gold/full_chip/*tile_array/1-Tile_PE .
#         
#         # If stop copying here, still takes an hour
#         # What if we copy more stuff?
# 
# #             2-constraints \
# #             3-custom-cts-overrides \
# #             4-custom-init \
# #             5-custom-lvs-rules \
# #             9-rtl \
# #             11-tsmc16 \
# #             12-synopsys-dc-synthesis \
# # 
# 
#         for f in \
#             2-constraints \
#             9-rtl \
#             11-tsmc16 \
#             12-synopsys-dc-synthesis \
#         ; do
#             echo cp -rpf $gold/full_chip/*tile_array/$f .
#             cp -rpf $gold/full_chip/*tile_array/$f .
#         done
#         echo "+++ ......TODO list (`date +'%a %H:%M'`)"
#         make -n cadence-innovus-init | grep 'mkdir.*output' | sed 's/.output.*//' | sed 's/^/  /'
# 
#         # Maybe do this again?
#         touch .stamp; # Breaks if don't do this before final step; I forget why...? Chris knows...
#         make -n cadence-innovus-init | grep 'mkdir.*output' | sed 's/.output.*//'
# 
# 
#         continue
#     fi

    
