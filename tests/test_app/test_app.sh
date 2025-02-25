#!/bin/bash

HELP="
  DESCRIPTION:
    Launch a docker container and run the indicated app.

  USAGE:
    $0 [ --vcs ] [ --fp ] <width>x<height> <app>

  EXAMPLE(S):
    $0 4x2 apps/pointwise
    $0 --vcs 4x2 apps/pointwise     # Default is verilator
    $0 --fp  4x2 tests/fp_pointwise
"
if [ "$1" == "--help" ]; then echo "$HELP"; exit; fi

# ARGS e.g. '4x2' => '--width 4 --height 2'
DO_FP=;  if [ "$1" == "--fp"  ]; then shift; DO_FP="--dense-fp"; fi
DO_VCS=; if [ "$1" == "--vcs" ]; then shift; DO_VCS=True; fi
size=`echo $1 | awk -Fx '{printf("--width %s --height %s", $1, $2)}'`
app=$2

# FOR VERILATOR
CAD=
TOOL='export TOOL=VERILATOR'

# FOR VCS
if [ "$DO_VCS" ]; then
    CAD='-v /cad:/cad'
    TOOL='. /cad/modules/tcl/init/bash; module load base; module load vcs'
fi

# DOCKER image and container
set -x
image=stanfordaha/garnet:latest
docker pull $image
container=DELETEME-$USER-apptest-$$
docker run -id --name $container --rm $CAD $image bash

# TRAPPER KILLER: Trap and kill docker container on exit ('--rm' no workee, but why?)
function cleanup { set -x; docker kill $container; }
trap cleanup EXIT

# BLUUUGH
if [ "$COPY_CW" ]; then
    for f in /nobackup/steveri/github/Genesis2/test/CW*.v; do
        docker cp $f $container:/aha/garnet/tests/test_app
    done
    docker exec $container /bin/bash -c "ls -l /aha/garnet/CW*"
fi

# VERILATOR
[ "$CAD" ] || docker exec $container /bin/bash -c "
cd /aha/garnet/tests/test_app; make setup-verilator
"


# TEST
docker exec $container /bin/bash -c "
set -x
rm -f garnet/garnet.v
source /aha/bin/activate
$TOOL
$USE_GARNET_BRANCH
# aha garnet $size --verilog --use_sim_sram --glb_tile_mem_size 128
aha garnet $size --verilog --use_sim_sram --glb_tile_mem_size 128 # does this happen TWICE??
aha map $app
aha pnr $app $size
aha test $app $DO_FP
"
