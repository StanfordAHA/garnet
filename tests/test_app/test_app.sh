#!/bin/bash

USE_GARNET_BRANCH=
# BRANCH=origin/CW
# USE_GARNET_BRANCH="(cd /aha/garnet; git pull; git fetch origin; git checkout $BRANCH)"

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

# VERILATOR
[ "$CAD" ] || docker exec $container /bin/bash -c "
cd /aha/garnet/tests/test_app; make setup-verilator
"

# Find local garnet home dir $GARNET, based on where this script lives
# Assume this script is $GARNET/tests/test_app/$0
function where_this_script_lives {

  local cmd="$0"    # Is script being executed or sourced?
  [ "${BASH_SOURCE[0]}" -ef "$0" ] || cmd="${BASH_SOURCE[0]}" 

  local scriptpath=`realpath $cmd`       # Full path of script e.g. "/foo/bar/baz.sh"
  local scriptdir=${scriptpath%/*}       # Script dir e.g. "/foo/bar"
  scriptdir=$(cd $scriptdir; pwd)       # Get abs path instead of rel
  [ "$scriptdir" == `pwd` ] && scriptdir="."
  echo $scriptdir
}
script_home=`where_this_script_lives`
GARNET=$(cd $script_home; cd ../..; pwd)

# Copy local garnet branch to /tmp/deleteme-garnet-$$
/bin/rm -rf /tmp/deleteme-garnet-$$; mkdir -p /tmp/deleteme-garnet-$$
cd /nobackup/steveri/github/garnet  #   script_home=...; garnet_home=... get it?
git ls-files | xargs -I{} cp -r --parents {} /tmp/deleteme-garnet-$$

# Then copy into the container
docker exec $container /bin/bash -c "rm -rf /aha/garnet"
docker cp /tmp/deleteme-garnet-$$ $container:/aha/garnet
/bin/rm -rf /tmp/deleteme-garnet-$$

# TEST
docker exec $container /bin/bash -c "
set -x
rm -f garnet/garnet.v
source /aha/bin/activate
$TOOL
# $USE_GARNET_BRANCH
# aha garnet $size --verilog --use_sim_sram --glb_tile_mem_size 128
aha garnet $size --verilog --use_sim_sram --glb_tile_mem_size 128 # does this happen TWICE??
aha map $app
aha pnr $app $size
aha test $app $DO_FP
"

# 'aha test' calls 'make sim' and 'make run' etc.
