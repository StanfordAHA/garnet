#!/bin/bash

cmd=$0
cmd=amber-rtl-build-check.sh

function HELP { cat <<EOF

DESCRIPTION: Builds RTL for a 4x2 amber grid, compares to reference build.

USAGE (default is "--local"):
   $cmd --docker  # Use gen_rtl.sh to build design.v from inside a container
   $cmd --local   # Generate design.v locally i.e. maybe we're already in a container

EXAMPLE test from outside docker
   cd /tmp/scratch        # (optional)
   $cmd --docker && echo PASS || echo FAIL

EXAMPLE test from inside docker
    # Fire up a docker container
    image=stanfordaha/garnet:latest
    container=deleteme
    docker pull \$image
    docker run -id --name \$container --rm -v /cad:/cad \$image bash

    # Run the test using garnet master branch
    function dexec { docker exec \$container /bin/bash -c "\$*"; }
    dexec "cd /aha/garnet && git checkout master && git pull"
    dexec "/aha/garnet/tests/test_amber_rtl_build/amber-rtl-build-check.sh --local"

    # OR run the test using local copy of repo
    GARNET_HOME=/nobackup/steveri/github/garnet    
    function dexec { docker exec \$container /bin/bash -c "\$*"; }
    docker exec $container /bin/bash -c "rm -rf /aha/garnet"
    git clone $GARNET_HOME /tmp/garnet
    docker cp /tmp/garnet $container:/aha/garnet
    /bin/rm -rf /tmp/garnet
EOF
}

[ "$1" == "--help" ] && HELP && exit

# Always debug (for now)
# Use "-v" as first arg if want extra debug info
# [ "$1" == "-v" ] && shift && set -x

# width=32  # slow 32x16
width=4     # quick 4x2
height=$((width/2))

# E.g. if script is "$GARNET_HOME/tests/test_amber_rtl_build/amber-rtl-build-check.sh"
# then scriptdir is "$GARNET_HOME/tests/test_amber_rtl_build"
scriptpath=$0
scriptpath=`readlink $scriptpath || echo $scriptpath`  # Full path of script dir
scriptdir=${scriptpath%/*}  # E.g. "build_tarfile.sh" or "foo/bar"

echo '--- RTL test BEGIN' `date`

if [ "$1" == "--docker" ]; then

    # Use gen_rtl.sh to build a docker environment and use that to build the RTL
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

    # Build a docker environment and use that to build RTL "outputs/design.v"
    # (gen_rtl.sh copies final design.v to "./outputs" subdirectory)
    mkdir -p outputs
    $GARNET_HOME/mflowgen/common/rtl/gen_rtl.sh
    mv outputs/design.v .

else
    # RTL-build flags
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

    # For better or worse: I put this in gen_rtl.sh
    # Hack it up! FIXME should use same mechanism as onyx...define AO/AN_CELL
    # Also see: garnet/mflowgen/common/rtl/gen_rtl.sh, gemstone/tests/common/rtl/{AN_CELL.sv,AO_CELL.sv}
    cat design.v \
        | sed 's/AN_CELL inst/AN2D0BWP16P90 inst/' \
        | sed 's/AO_CELL inst/AO22D0BWP16P90 inst/' \
              > /tmp/tmp.v
    mv -f /tmp/tmp.v design.v
fi

printf "\n"
echo "+++ Compare result to reference build"
ref=$scriptdir/ref/garnet-4x2.v
f1=design.v; f2=$ref

# Need 'sed s/unq...' to handle the case where both designs are
# exactly the same but different "unq" suffixes e.g.
#     < Register_unq3 Register_inst0 (
#     > Register_unq2 Register_inst0 (
function vcompare { sort $1 | sed 's/,$//' | sed 's/unq[0-9*]/unq/'; }

ndiffs=`diff -I Date <(vcompare $f1) <(vcompare $f2) | wc -l`

if [ "$ndiffs" != "0" ]; then

    # ------------------------------------------------------------------------
    # TEST FAILED

    printf "Test FAILED with $ndiffs diffs\n\n"
    printf "Top 40 diffs:"
    diff -I Date <(vcompare $f1) <(vcompare $f2) | head -40
    exit 13
fi

echo "Test PASSED"



