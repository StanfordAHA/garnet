#!/bin/bash

# Description: Builds RTL for a 4x2 amber grid, compares to reference build.

# Usage (default is "--local"):
#    $0 --docker  # Use gen_rtl.sh to build design.v from inside a container
#    $0 --local   # Generate design.v locally i.e. maybe we're already in a container

# Prep:
# docker cp ~/tmpdir/test_amber_rtl_build/ $container:/aha/garnet/tests

# Then, in docker:
#     cd /aha/garnet
#     tests/test_amber_rtl_build/amber-rtl-build-check.sh |& tee amber-build.log

# I am e.g. /aha/garnet/tests/test_amber_rtl_build/amber-rtl-build-check.sh
# Ref file is e.g. /aha/garnet/tests/test_amber_rtl_build/ref/garnet-4x2.v

# Do this inside docker:

set -x
# width=32  # slow 32x16
width=4   # quick 4x2
height=$((width/2))

# Assumes script is $GARNET_HOME/tests/test_amber_rtl_build/amber-rtl-build-check.sh
scriptpath=$0
scriptpath=`readlink $scriptpath || echo $scriptpath`  # Full path of script dir
scriptdir=${scriptpath%/*}  # E.g. "build_tarfile.sh" or "foo/bar"


if [ "$1" == "--docker" ]; then

    export array_width=$width
    export array_height=$height

    export glb_tile_mem_size=256
    export num_glb_tiles=16
    export pipeline_config_interval=8
    export interconnect_only=False
    export glb_only=False
    export soc_only=False
    export PWR_AWARE=True
    export use_container=True

    # export use_local_garnet=True
    export use_local_garnet=False # for now

    export save_verilog_to_tmpdir=False
    export rtl_docker_image=default

    export WHICH_SOC=amber

    export GARNET_HOME=`cd $scriptdir/../..; pwd`
    echo "--- Found GARNET_HOME=$GARNET_HOME"

    # gen_rtl.sh copies final design.v to "./outputs" subdirectory
    mkdir -p outputs

#     # Die if aha already exists
#     test -e aha && echo "ERROR aha already exists, will not overwrite it"
#     test -e aha && exit 13

    # Build outputs/design.v, move to .
    $GARNET_HOME/mflowgen/common/rtl/gen_rtl.sh
    mv outputs/design.v .

else
    flags="--width $width --height $((width/2)) --pipeline_config_interval 8 -v --glb_tile_mem_size 256"
    echo $flags

    # Prep/clean
    cd /aha
    rm -rf garnet/genesis_verif
    rm -f  garnet/garnet.v

    # Build new rtl
    export WHICH_SOC='amber'
    source /aha/bin/activate; # Set up the build environment
    aha garnet $flags

    # Assemble final design.v
    cd /aha/garnet
    cp garnet.v genesis_verif/garnet.v
    cat genesis_verif/* > design.v
    cat global_buffer/systemRDL/output/glb_pio.sv >> design.v
    cat global_buffer/systemRDL/output/glb_jrdl_decode.sv >> design.v
    cat global_buffer/systemRDL/output/glb_jrdl_logic.sv >> design.v
    cat global_controller/systemRDL/output/*.sv >> design.v
fi

# For better or worse: I put this in gen_rtl.sh
# Hack it up! FIXME should use same mechanism as onyx...define AO/AN_CELL
# Also see: garnet/mflowgen/common/rtl/gen_rtl.sh, gemstone/tests/common/rtl/{AN_CELL.sv,AO_CELL.sv}
cat design.v \
    | sed 's/AN_CELL inst/AN2D0BWP16P90 inst/' \
    | sed 's/AO_CELL inst/AO22D0BWP16P90 inst/' \
          > /tmp/tmp.v
mv -f /tmp/tmp.v design.v


# # Compare to ref
# scriptpath=$0
# scriptpath=`readlink $scriptpath || echo $scriptpath`  # Full path of script dir
# scriptdir=${scriptpath%/*}  # E.g. "build_tarfile.sh" or "foo/bar"

ref=$scriptdir/ref/garnet-4x2.v

# Below, need 'sed s/unq...' to handle the case where both designs are
# exactly the same but different "unq" suffixes e.g.
#     < Register_unq3 Register_inst0 (
#     > Register_unq2 Register_inst0 (

echo "--- Compare result to reference build"
f1=design.v
f2=$ref
function vcompare { sort $1 | sed 's/,$//' | sed 's/unq[0-9*]/unq/' ;}

echo "How many diffs?"
diff -I Date <(vcompare $f1) <(vcompare $f2) | wc -l

printf "\nTop 40 diffs:\n"
diff -I Date <(vcompare $f1) <(vcompare $f2) | head -40
