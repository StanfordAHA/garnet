#!/bin/bash
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
build=/sim/$USER
garnet=`cd $script_home/../..; pwd`

# mflowgen
test  -d $build || mkdir $build; cd $build
test  -d $build/mflowgen || git clone https://github.com/cornell-brg/mflowgen.git
mflowgen=$build/mflowgen

# tsmc16 adk
cd $mflowgen/adks
test -d tsmc16-adk || git clone http://gitlab.r7arm-aha.localdomain/alexcarsello/tsmc16-adk.git
test -d tsmc16     || ln -s tsmc16-adk tsmc16

# Tile_PE
module=Tile_PE
if test -d $mflowgen/$module; then
    echo "oops $mflowgen/$module exists"
    echo "giving up already love ya bye-bye"
    exit 13
fi
set -x
mkdir $mflowgen/$module; cd $mflowgen/$module
../configure --design $garnet/mflowgen/Tile_PE


# Targets: run "make list" and "make status"
# make -n mentor-calibre-drc
echo 'make mentor-calibre-drc |& tee mcdrc.log'
# make -n debug-mentor-calibre-drc
echo 'make debug-mentor-calibre-drc |& tee mcdrc-debug.log'


########################################################################
########################################################################
########################################################################
echo 'make mentor-calibre-drc |& tee mcdrc.log'


# rtl:
# python: can't open file 'garnet.py': [Errno 2] No such file or directory
# cp: cannot stat ‘garnet.v’: No such file or directory
# cat: genesis_verif/*: No such file or directory

# syn .. c-synthesis
# Error: Cannot find the design 'Tile_PE' in the library 'WORK'. (LBR-0)


# make -n rtl
# rm -rf ./1-rtl
# cp -aL ../../soc/components/cgra/garnet/mflowgen/common/rtl 1-rtl || true


mkdir -p 1-rtl/outputs && \
python ../utils/letters.py -c -t rtl && \
cp -f .mflowgen/1-rtl/mflowgen-run.sh 1-rtl && \
cp -f .mflowgen/1-rtl/mflowgen-debug.sh 1-rtl 2> /dev/null || true && \
cd 1-rtl && sh mflowgen-run.sh 2>&1 | tee mflowgen-run.log && \
cd .. && \
touch -c 1-rtl/outputs/*





# Generic Targets:
# 
#  - list      -- List all steps
#  - status    -- Print build status for each step
#  - runtimes  -- Print runtimes for each step
#  - graph     -- Generate a PDF of the step dependency graph
#  - clean-all -- Remove all build directories
#  - clean-N   -- Clean target N
#  - diff-N    -- Diff target N
# 
# Targets:
# 
#  -  0 : info
#  -  1 : rtl
#  -  2 : custom-power
#  -  3 : custom-init
#  -  4 : tsmc16
#  -  5 : constraints
#  -  6 : synopsys-dc-synthesis
#  -  7 : cadence-innovus-flowsetup
#  -  8 : cadence-innovus-init
#  -  9 : cadence-innovus-power
#  - 10 : cadence-innovus-place
#  - 11 : cadence-innovus-cts
#  - 12 : cadence-innovus-postcts_hold
#  - 13 : cadence-innovus-route
#  - 14 : cadence-innovus-postroute
#  - 15 : cadence-innovus-signoff
#  - 16 : mentor-calibre-gdsmerge
#  - 17 : mentor-calibre-drc
#  - 18 : mentor-calibre-lvs
#  - 19 : cadence-innovus-debug-calibre
# 
# Debug Targets:
# 
#  - debug-6  : debug-synopsys-dc-synthesis
#  - debug-8  : debug-cadence-innovus-init
#  - debug-9  : debug-cadence-innovus-power
#  - debug-10 : debug-cadence-innovus-place
#  - debug-11 : debug-cadence-innovus-cts
#  - debug-12 : debug-cadence-innovus-postcts_hold
#  - debug-13 : debug-cadence-innovus-route
#  - debug-14 : debug-cadence-innovus-postroute
#  - debug-15 : debug-cadence-innovus-signoff
#  - debug-16 : debug-mentor-calibre-gdsmerge
#  - debug-17 : debug-mentor-calibre-drc
#  - debug-18 : debug-mentor-calibre-lvs
