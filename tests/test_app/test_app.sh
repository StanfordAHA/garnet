#!/bin/bash
# Compare: diff garnet/tests/test_app/test_app.sh Genesis2/test/copy_of_garnet_tests_test_app.sh

# Use '--fail' test failure path (for debugging)
[ "$1" == "--fail" ] && TEST_FAILURE_PATH=true
[ "$1" == "--fail" ] && shift

# Uncomment for reusable container (for debugging)
# REUSE_CONTAINER=True

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

# Unpack the args
# commit=$1; shift  # See Genesis2/test/copy_of_garnet_tests_test_app.sh

# More args e.g. '4x2' => '--width 4 --height 2'
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

########################################################################
# Two ways to form groups in github workflow action logs:
#   echo "::group::Colon group"; echo "foo"; echo "::endgroup::"
#   echo "##[group]Hash group";  echo "bar"; echo "##[endgroup]"
#
# But unless you use subterfuge (below), the echo command itself can trigger a group :(

function GROUP    { sleep 1; printf "%s%s[group]%s\n"  "#" "#" "$1"; sleep 1; }
function ENDGROUP { sleep 1; printf "%s%s[endgroup]\n" "#" "#";      sleep 1; }

########################################################################
# DOCKER image and container
GROUP "DOCKER image and container"
image=stanfordaha/garnet:latest
docker pull $image
container=DELETEME-$USER-apptest-$$
[ "$REUSE_CONTAINER" ] && container=deleteme-steveri-testapp-dev
# Note for verilator CAD="" else CAD="-v /cad:/cad"
# Note this will err if reusing container, but that's okay maybe.
docker run -id --name $container --rm $CAD $image bash || echo okay


########################################################################
# TRAPPER KILLER: Trap and kill docker container on exit ('--rm' no workee, but why?)
function cleanup { set -x; docker kill $container; }
[ "$REUSE_CONTAINER" ] || trap cleanup EXIT
# echo "##[endgroup]"
# set +x; sleep 1; echo "##[endgroup]"; sleep 1; set -x
set +x; ENDGROUP

########################################################################
GROUP "UPDATE docker w local garnet"

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
cd $script_home/../..; pwd

# Copy local garnet branch to /tmp/deleteme-garnet-$$
/bin/rm -rf /tmp/deleteme-garnet-$$; mkdir -p /tmp/deleteme-garnet-$$
git ls-files | xargs -I{} cp -r --parents {} /tmp/deleteme-garnet-$$

# Then copy into the container
docker exec $container /bin/bash -c "rm -rf /aha/garnet"
docker cp /tmp/deleteme-garnet-$$ $container:/aha/garnet
/bin/rm -rf /tmp/deleteme-garnet-$$
# echo "##[endgroup]"
# set +x; echo "##[endgroup]"; set -x
set +x; ENDGROUP

########################################################################
# VERILATOR - prepare to install verilator if needed

if [ "$CAD" ]; then
    make_verilator='echo Using vcs, no need for verilator'
else
    make_verilator="(set -x; /aha/garnet/tests/install-verilator.sh) || exit 13"
fi
GROUP "VERILATOR PREP: make_verilator='$make_verilator'"
ENDGROUP


########################################################################
# TEST
# size='--width 4 --height 2'
docker exec $container /bin/bash -c "
  echo \#\#[group]SETUP
  rm -f garnet/garnet.v
  source /aha/bin/activate
  $TOOL
  (cd /aha/garnet; make clean)  # In case of e.g. CONTAINER_REUSE
  echo \#\#[endgroup]

  # Note (echo \#\# ...) gives much better result than (echo '##...') 
  echo \#\#[group]aha garnet $size --verilog --use_sim_sram --glb_tile_mem_size 128
  aha garnet $size --verilog --use_sim_sram --glb_tile_mem_size 128 || exit 13
  echo \#\#[endgroup]

  echo \#\#[group]aha map $app
  aha map $app || exit 13
  echo \#\#[endgroup]

  echo \#\#[group]aha pnr $app $size
  aha pnr $app $size || exit 13
  echo \#\#[endgroup]

  echo \#\#[group]INSTALL verilator5
  $make_verilator || exit 13
  echo \#\#[endgroup]

  # 'aha test' calls 'make sim' and 'make run' etc.
  echo \#\#[group]aha test $app $DO_FP
  aha test $app $DO_FP || exit 13
  echo \#\#[endgroup]
"
