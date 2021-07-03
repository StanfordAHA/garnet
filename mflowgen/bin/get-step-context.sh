#!/bin/bash

# Usage: $0 <refdir> <step>
# 
# Using ref/cached/gold build in <refdir>, find and link to the
# context needed for a given target <step> node in an mflowgen build graph.
# 
# E.g. for cadence-innovus-postroute_hold we might link link these two
# steps from <refdir> into current (build) dir
# 
#     ln -s 23-cadence-innovus-flowsetup <refdir>/23-cadence-innovus-postroute
#     ln -s 31-cadence-innovus-postroute <refdir>/30-cadence-innovus-postroute
# 
# Example usage to e.g. run standalone step "cadence-innovus-postroute_hold"
# in $RUNDIR using cached information in refdir "/build/gold":
# 
#     #1. Build the design framework
#     mflowgen run --design $GARNET_HOME/mflowgen/full_chip
#
#     #2. Build (link to) standalone context for the build
#     get-step-context.sh /build/gold cadence-innovus-postroute_hold
# 
#     #3. Execute target step "postroute_hold"
#     make cadence-innovus-postroute_hold

REF=$1
target_step=$2
# target_step=cadence-innovus-postroute_hold

echo "--- BEGIN $0 $*" | sed "s,$GARNET_HOME,\$GARNET_HOME,"
echo "  where GARNET_HOME=$GARNET_HOME"
echo "+++ STANDALONE TEST RIG SETUP - build symlinks to steps in $REF/full_chip";

function find_dependences {
    # Example:
    #    find_dependences cadence-innovus-postroute_hold
    # 
    # Returns:
    #      cadence-innovus-postroute
    #      cadence-innovus-flowsetup
    # 
    # Notes:
    #   - Ignores adk steps because it's better to redo those from scratch.
    #   - Must run in a valid mflowgen design dir i.e. one with a '.mflowgen' subdir.
    #   - Could do "test -e .mflowgen || ERROR"

    stepname="$1"
    stepnum=$(make list |& awk '$NF == "'$stepname'" {print $2; exit}')
    # echo "FOUND $stepnum $stepname"

    # Note for some reason it ignores adk dependences.
    # Seems to work anyway I guess?
    make info-$stepnum |& grep -v warning | sed 's/|//g' \
         | awk '$NF ~ /^[0-9]/ {print $NF}; /^Parameters/{exit}' \
         | sed "/$stepname\$/,\$d" \
         | egrep -v 'freepdk|tsmc' \
         | sed 's/^[0-9]*[-]//'
}

# Find-dependences came up with this:

echo ""; echo "DEPENDENCES (virgin awk script): "
find_dependences cadence-innovus-postroute_hold

########################################################################
########################################################################
########################################################################
echo ""; echo "DEPENDENCES (chad python script): "

function find_dependences_py {
    # Find all dependent steps leading to indicated target step
    # 
    # Example:
    #    find_dependences cadence-innovus-postroute_hold
    # 
    # Returns the list
    #   31-cadence-innovus-postroute
    #   23-cadence-innovus-flowsetup
    #
    # Ignores adk steps because it's better to redo those from scratch.
    # 
    # Must run in a valid mflowgen design dir i.e. one with a '.mflowgen' subdir.
    # Could do "test -e .mflowgen || ERROR"
    target_step=${1}
    # TEST: target_step="cadence-innovus-postroute_hold"

    DBG=0
    pyfile=deleteme.pyfile.$$
    # Want e.g. stepdir = "32-cadence-innovus-postroute_hold"
    stepdir=$(/bin/ls .mflowgen | egrep "^[0-9]*-${target_step}")

    # Build and execute a python script
    # cat << ....EOF | sed 's/        //' > $pyfile
    cat << ....EOF | sed 's/        //' | python3 | sed 's/^[0-9]*[-]//'
        # 1. Read date from config yaml file
        import yaml; DBG=${DBG}
        config_file=".mflowgen/${stepdir}/configure.yml"
        if DBG: print(f"config file = '{config_file}'\n\n")
        with open(config_file, 'r') as f: data = yaml.safe_load(f)
        if DBG: print(data)

        # 2. Find and print input edges; ignore adk edges
        need_steps={}
        ei = data['edges_i']
        if DBG: print("Dependences found:")
        for edge_name in ei:
            filename = ei[edge_name][0]['f']    ; # E.g. "design.checkpoint" or "adk"
            stepname = ei[edge_name][0]['step'] ; # E.g. "23-cadence-innovus-flowsetup"
            # print(f"Step Found dependence {qf:30} in step '{stepname}/outputs'")
            if DBG: print(f"STEP {stepname:30} FILE {filename:30}")

            # Dunno if this is important, but I'd like to know when/if it happens...
            assert filename == edge_name, "Edge name != filename...why?"

            if filename != "adk": need_steps[stepname]=True;
        if DBG: print("")
        for s in need_steps: print(s)
        exit()
....EOF

#     python3 < $pyfile | sed 's/^[0-9]*[-]//'
#     /bin/rm ${pyfile}
    #    return $(python3 < $pyfile; /bin/rm $pyfile)
}


find_dependences_py cadence-innovus-postroute_hold


echo ""
echo ""
########################################################################
########################################################################
########################################################################

# Who's the chad now?
function find_dependences_awk2 {

    # Example:
    #    find_dependences cadence-innovus-postroute_hold
    # 
    # Returns:
    #      cadence-innovus-postroute
    #      cadence-innovus-flowsetup
    # 
    # Notes:
    #   - Ignores adk steps because it's better to redo those from scratch.
    #   - Must run in a valid mflowgen design dir i.e. one with a '.mflowgen' subdir.
    #   - Could do "test -e .mflowgen || ERROR"

    target_step=${1} ; # E.g. "rtl"
    stepdir=$(/bin/ls .mflowgen | egrep "^[0-9]*-${target_step}") ; # E.g. "11-rtl"
    config_file=".mflowgen/${stepdir}/configure.yml"

    # Look in config.yml to find this:
    #     edges_i:
    #       adk:
    #       - f: adk
    #         step: 7-freepdk-45nm
    #       design.checkpoint:
    #       - f: design.checkpoint
    #         step: 31-cadence-innovus-postroute
    #       innovus-foundation-flow:
    #       - f: innovus-foundation-flow
    #         step: 23-cadence-innovus-flowsetup
    # 
    # And then use that to print this:
    #     cadence-innovus-postroute
    #     cadence-innovus-flowsetup

    (cat $config_file; echo "xxx") | sed -n '/^edges_i/,/^[^ ]/p' \
    | awk '
        $(NF-1) == "f:" { f = $NF }
        f == "adk" { next }
        $1 == "step:" { print $2 }' \
    | sed 's/^[0-9]*[-]//'

echo ""; echo "DEPENDENCES (mega-chad awk script): "
find_dependences_py_awk2 cadence-innovus-postroute_hold
echo ""
echo ""


DBG=
for step in cadence-innovus-postroute cadence-innovus-flowsetup; do

    [ "$DBG" ] && echo Processing step $step

    # Find name of step in local dir; bug out if exists already
    [ "$DBG" ] && (make list |& egrep ": $step\$")
    stepnum=$(make list |& egrep ": $step\$" | awk '{print $2}')
    local_step=$stepnum-$step
    [ "$DBG" ] && (echo "Want local step $local_step"; echo '')
    if test -e $local_step; then
        echo "Looks like '$local_step' exists already"
        echo "Doing nothing for '$local_step'"
        continue
    fi

    # Find name of step in ref dir
    stepnum=$(cd $REF/full_chip; make list |& egrep ": $step\$" | awk '{print $2}')
    ref_step=$REF/full_chip/$stepnum-$step
    [ "$DBG" ] && echo "Found ref step $ref_step"
    if ! test -d $ref_step; then
        echo "hm look like $ref_step don't exist after all..."
        exit 13
    fi

    # Need '.prebuilt' to make it work for some reason...
    [ "$DBG" ] && echo "touch <refdir>/<step>/.prebuilt"
    touch $ref_step/.prebuilt

    # Link local to ref
    [ "$DBG" ] && echo "ln -s $ref_step $local_step"
    ln -s $ref_step $local_step
    echo "$local_step => $ref_step"
    [ "$DBG" ] && echo ''

done

echo "+++ READY TO BUILD STANDALONE $target_step"
echo "make -n ${target_step}"
make -n ${target_step} \
  |& egrep "^mkdir.*output" | sed "s/output.*//" | egrep -v ^Make


exit
########################################################################
########################################################################
########################################################################
# To run locally on kiwi can do this:
do_this=OFF
if [ "$do_this" == "ON" ]; then

    # 1. Set up run and ref dirs
    T=/tmp/get-step-context; cd $T
    REFDIR=/build/gold; RUNDIR=$T/full_chip

    # 2. Set up to execute target step in $RUNDIR
    export GARNET_HOME=/nobackup/steveri/github/garnet
    sbk=$GARNET_HOME/mflowgen/bin/setup-buildkite.sh
    source $sbk --dir $RUNDIR |& tee log | less

    # 3. Jimmy up a fake tsmc16 library
    (cd /tmp/steveri/mflowgen.master/adks; ln -s freepdk-45nm tsmc16)

    # 4. Build the design framework
    mflowgen run --design $GARNET_HOME/mflowgen/full_chip

    ### >>> GOOD TO HERE <<< ###

    # 3. Build standalone context and execute target step "postroute_hold"
    mflowgen/bin/get-step-context.sh $REFDIR
    make cadence-innovus-postroute_hold
fi

exit
########################################################################
# Buildkite on arm machine should be able to do this:
do_this=OFF
if [ "$do_this" == "ON" ]; then

    # 1. Set up run and ref dirs
    T=/tmp/get-step-context; cd $T
    REFDIR=/build/gold; RUNDIR=$T/full_chip

    # 2. Set up to execute target step in $RUNDIR
    export GARNET_HOME=/sim/steveri/soc/components/cgra/garnet
    sbk=$GARNET_HOME/mflowgen/bin/setup-buildkite.sh
    source $sbk --dir $RUNDIR |& tee log | less

    # 3. No need to jimmy up a fake tsmc16 library
    # (cd /tmp/steveri/mflowgen.master/adks; ln -s freepdk-45nm tsmc16)

    # 4. Build the design framework
    mflowgen run --design $GARNET_HOME/mflowgen/full_chip

    ### >>> GOOD TO HERE <<< ###

    # 3. Build standalone context and execute target step "postroute_hold"
    mflowgen/bin/get-step-context.sh $REFDIR
    make cadence-innovus-postroute_hold
fi

