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

# Function to expand step aliases
# E.g. 'step_alias syn' returns 'synopsys-dc-synthesis' or 'cadence-genus-synthesis' as appropriate
function step_alias {
    case "$1" in
        # This is probably dangerous; init is heavily overloaded
        init)      s=cadence-innovus-init      ;;

        # "synthesis" will expand to dc or genus according to what's
        # in "make list" (see below). Same for gdsmerge etc.
        syn)       s=synthesis ;;
        gds)       s=gdsmerge ;;
        tape)      s=gdsmerge ;;
        merge)     s=gdsmerge ;;
        *)         s="$1" ;;
    esac

    # 1. First, look for exact match
    ntries=1
    s1=`make list |& egrep -- " $s"'$' | awk '{ print $NF; exit }'`

    # Then look for alias that expands to synopsys/cadence/mentor tool
    # Uses *first* pattern match found in "make list" to expand e.g.
    # "synthesis" => "synopsys-dc-synthesis" or "cadence-genus-synthesis"
    if ! [ "$s1" ]; then
        ntries=2
        p=' synopsys| cadence| mentor'
        s1=`make list |& egrep "$p" | egrep -- "$s"'$' | awk '{ print $NF; exit }'`
    fi

    # Then look for alias that expands to anything that kinda matches
    if ! [ "$s1" ]; then
        ntries=3
        s1=`make list |& egrep -- "$s"'$' | awk '{ print $NF; exit }'`
    fi

    DBG=""
    if [ "$DBG" ] ; then echo '---'; echo "FINAL '$s' -> '$s1' (after $ntries tries)"; fi

    # Note: returns null ("") if no alias found
    echo $s1; # return value = $s1
    return

    # UNIT TESTS for step_alias fn, cut'n'paste
    test_steps="syn init cts place route postroute gds tape merge gdsmerge lvs drc"
    test_steps="constraints MemCore PE rtl synthesis custom-dc-postcompile tsmc16 synthesis foooo"
    for s in $test_steps; do echo "'$s' ==> '`step_alias $s`'"; done
    for s in $test_steps; do step_alias $s; done
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
# Turn copy-list into an array e.g. 'Tile_PE,rtl' => 'Tile_PE,rtl'
copy_list=()
if [ "$use_cached" ]; then
    copy_list=`echo $use_cached | tr ',' ' '`
    echo "--- FOUND COPY LIST"
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
source $garnet/mflowgen/bin/setup-buildkite.sh \
       --dir $build_dir \
       --need_space $need_space \
       || exit 13

##############################################################################

echo "--- Building in destination dir `pwd`"


##################################################################
# HIERARCHICAL BUILD AND RUN
echo "--- HIERARCHICAL BUILD AND RUN"
if [ "$DEBUG" ]; then
    echo firstmod=${modlist[0]}; echo subgraphs=\(${modlist[@]:1}\)
fi

function build_module {
    modname="$1"; # E.g. "full_chip"
    echo "--- ...BUILD MODULE '$modname'"

    echo "mkdir $modname; cd $modname"
    mkdir $modname; cd $modname

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

echo ""
echo "STEPS to take"
for step in ${build_sequence[@]}; do
    echo "  $step -> `step_alias $step`"
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
cat -n make*.log | grep -i error  | tail | tee -a tmp.summary || PASS; echo "-----"
cat -n make*.log | grep    FAIL   | tail | tee -a tmp.summary || PASS; echo "-----"
cat -n make*.log | grep -i passed | tail | tee -a tmp.summary || PASS; echo ""

########################################################################
echo '+++ SUMMARY of what we did'
f=`/bin/ls -t make*.log`
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

# See test_module.sh.orig for old stuff that we might want to revive someday...
