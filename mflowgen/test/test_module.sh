#!/bin/bash

function help {
    cat <<EOF

Usage: $0 [OPTION] <module>,<subgraph>,<subsubgraph>... --steps <step1>,<step2>...

Options:
  -v, --verbose VERBOSE mode
  -q, --quiet   QUIET mode
  -h, --help    help and examples
  --debug       DEBUG mode

  --branch <b>             only run test if in garnet branch <b> (b=regex)
  --step <s1,s2,...>       step(s) to run in the indicated (sub)graph. default = 'lvs,drc'
  --use_cache <s1,s2,...>  list of steps to copy from gold cache before running test(s)
  --build_dir <d>          do the build in directory <d>

  --need_space <amt>  make sure we have at least <amt> gigabytes available (default 100)

Examples:
    $0 Tile_PE
    $0 Tile_MemCore --need_space 20G
    $0 Tile_PE --branch 'devtile*'
    $0 --verbose Tile_PE --steps synthesis,lvs
    $0 full_chip tile_array Tile_PE --steps synthesis
    $0 full_chip tile_array Tile_PE --steps synthesis --use_cache Tile_PE,Tile_MemCore
    $0 full_chip --need_space 200G --build_dir /build/gold.99
    
EOF
}

########################################################################
# Args / switch processing
modlist=()
VERBOSE=false
build_sequence='lvs,gls'
build_dir=.
need_space=100G
while [ $# -gt 0 ] ; do
    case "$1" in
        -h|--help)    help; exit;    ;;
        -v|--verbose) VERBOSE=true;  ;;
        -q|--quiet)   VERBOSE=false; ;;
        --debug)      DEBUG=true;    ;;
        --branch*)    shift; branch_filter="$1";  ;;
        --step*)      shift; build_sequence="$1"; ;;
        --use_cache*) shift; use_cached="$1"; ;;
        --build_dir)  shift; build_dir="$1"; ;;

        # Deprecated. TODO/FIXME emit a 'deprecated' message.
        --update*)    shift; build_dir="$1"; ;;

        # E.g. '--need_space' or '--want_space'
        --*_space)    shift; need_space="$1"; ;;

        # Any other 'dashed' arg
        -*)
            echo "***ERROR: unrecognized arg '$1'"; help; exit; ;;

        # Any non-dashed arg
        *)
            modlist+=($1); ;;
    esac
    shift
done
        
if [ "$DEBUG"=="true" ]; then
    VERBOSE=true
fi

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

# setup assumes script_home == GARNET_HOME/mflowgen/test/
garnet=`cd $script_home/../..; pwd`

# Oop "make rtl" (among others maybe) needs GARNET_HOME env var
export GARNET_HOME=$garnet

########################################################################
# SPACE CHECK -- generally need at least 100G for a full build
# - moved to setup-buildkite.sh

########################################################################
# Branch filter. Seldom used.
# Refuses to proceed if branch does not match regex "branch_filter"
if [ "$branch_filter" ]; then
    $garnet/mflowgen/bin/check_branch.sh "$branch_filter" || exit 13
fi

# Exit on error in any stage of any pipeline (is this a good idea?)
set -eo pipefail

# Running out of space in /tmp!!?
export TMPDIR=/sim/tmp

########################################################################
# Build environment and check requirements
# - moved to setup-buildkite.sh

########################################################################
# Make a build space for mflowgen; clone mflowgen
# - moved to setup-buildkite.sh

########################################################################
# CACHE OR NO CACHE: find your build directory
# - moved to setup-buildkite.sh

########################################################################
# ADK SETUP / CHECK
# - moved to setup-buildkite.sh

##############################################################################
# Set up the build environment
# - to skip mflowgen setup can do e.g.
#   'export TEST_MODULE_SBFLAGS='--skip_mflowgen'
echo Sourcing $garnet/mflowgen/bin/setup-buildkite.sh ...
source $garnet/mflowgen/bin/setup-buildkite.sh \
       --dir $build_dir \
       --need_space $need_space \
       $TEST_MODULE_SBFLAGS \
       || exit 13

echo "--- Building in destination dir `pwd`"


########################################################################
# Turn copy-list into an array e.g. 'Tile_PE,rtl' => 'Tile_PE,rtl'
copy_list=()
if [ "$use_cached" ]; then
    copy_list=`echo $use_cached | tr ',' ' '`
    echo "--- FOUND COPY LIST"
    for step in ${copy_list[@]}; do
        echo $step
    done
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

    # '-p' means we won't die if dir already exists
    echo "mkdir -p $modname; cd $modname"
    mkdir -p $modname; cd $modname

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
    
    # '-p' means we won't die if dir already exists
    echo "mkdir -p $dirname; cd $dirname"
    mkdir -p $dirname; cd $dirname
    
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

# Little hack to get local tsmc16 libs in among the cached info
# FIXME/TODO would it work for the caller to simply include "mflowgen" in the copy_list?
if [ "$use_cached" ]; then
    if [ "$firstmod" == "full_chip" ]; then
        echo "+++ Jimmy up the adks"
        set -x; pwd
        ls -l mflowgen/adks || echo NOPE adks not connected yet
        ln -s /sim/buildkite-agent/mflowgen.master mflowgen
        ls -l mflowgen/adks
        set +x
        echo "--- Continue"
    fi
fi

# Subgraphs
subgraphs=${modlist[@]:1}
for sg in $subgraphs; do
    build_subgraph $sg
done

echo ""
echo "STEPS to take"
for step in ${build_sequence[@]}; do
    # Expand aliases e.g. "syn" -> "synopsys-dc-synthesis"
    step_alias=`make list | $garnet/mflowgen/bin/step_alias.sh $step`
    echo "  $step -> $step_alias"
done
echo ""

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
            echo "***ERROR: could not find cache dir '$gold'"; exit 13; fi
        gold=`cd $gold/*${m}; pwd`
    done
    [ "$DEBUG" ] && echo "  Found gold cache directory '$gold'"

    # Copy desired info from gold cache
    for step in ${copy_list[@]}; do
        
        # Expand aliases e.g. "syn" -> "synopsys-dc-synthesis"
        # echo "  $step -> `step_alias $step`"
        step=`make list | $garnet/mflowgen/bin/step_alias.sh $step`
    
        # NOTE if cd command fails, pwd (disastrously) defaults to current dir
        # cache=`cd $gold/*${step}; pwd` || FAIL=true
        # if [ "$FAIL" == "true" ]; then
        #     echo "***ERROR: could not find cache dir '$gold'"; exit 13
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
    # step_orig=$step; step=`step_alias $step`
    step_orig=$step; step=`make list | $garnet/mflowgen/bin/step_alias.sh $step`
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

    # Use "failfile" to signal success or failure of make command
    failfile=/tmp/test_module_failfile.$$
    test -f $failfile && /bin/rm $failfile || echo -n '' ; # remove existing failfile
    (make $step || touch $failfile) |& tee make-$step.log | $filter
    test -f $failfile && /bin/rm $failfile || echo -n '' ; # remove just-created failfile

    # If step failed, dump out some info and err out.
    if test -f $failfile; then
        /bin/rm $failfile
        echo '+++ RUNTIMES'; make runtimes
        echo '+++ FAIL'
        echo 'Looks like we failed, here are some errors maybe:'
        echo grep -i error mflowgen-run.log
        grep -i error mflowgen-run.log
        exit 13
    fi

done

echo '+++ PASS/FAIL info maybe, to make you feel good'
function PASS { return 0; }
function sumfilter { 
    grep -v 'errors: 0, warnings: 0' | awk '$2 == "echo" { next } {print}' | cut -b 1-64
}
cat -n $f | grep -i error  | sumfilter | tail | tee -a tmp.summary || PASS; echo "-----"
cat -n $f | grep    FAIL   | sumfilter | tail | tee -a tmp.summary || PASS; echo "-----"
cat -n $f | grep -i passed | sumfilter | tail | tee -a tmp.summary || PASS; echo ""


echo '+++ Kill stray docker if necessary'

# Find the name of the docker container we just built.
container=`egrep ^container-name make*.log | awk '{print $NF}'` || echo no container found

# Kill the container if it still exists, e.g. if make job crashed before cleanup.
if [ "$container" ]; then
  echo '-------------------------'
  echo 'docker before:'; docker ps
  echo '-------------------------'
  set -x
  docker kill $container || echo no containers were killed
  set +x
  echo '-------------------------'
  echo 'docker after:'; docker ps
  echo '-------------------------'
fi

echo '+++ FAIL if make job failed, duh.'
egrep '^make: .* Error 1' make*.log && exit 13 || echo 'Did not fail. Right?'


########################################################################
echo '+++ SUMMARY of what we did'
logs=`/bin/ls -t make*.log`
cat -n $logs | grep '^mkdir.*output' | sed 's/.output.*//' | sed 's/mkdir -p/  make/' \
    >> tmp.summary \
    || PASS
cat tmp.summary \
    | sort -n | awk '{$1=""}; {print}' \
    | awk '{if ($1 == "make") print; else print "   " $0;}' \
    | uniq


########################################################################
echo '+++ RUNTIMES'; make runtimes

echo ""; pwd; ls -l .stamp; cat .stamp || PASS; echo "Time now: `date`"

grep AssertionError tmp.summary && echo '------' || PASS
grep AssertionError tmp.summary && exit 13 || PASS

exit

# See test_module.sh.orig for old stuff that we might want to revive someday...
