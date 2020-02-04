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
garnet=`cd $script_home/../..; pwd`

# Check requirements for python, coreir, magma etc.
(cd $garnet; $garnet/bin/requirements_check.sh) || exit 13

# Lots of useful things in /usr/local/bin. coreir for instance ("type"=="which")
echo ""; type coreir
export PATH="$PATH:/usr/local/bin"; hash -r
type coreir; echo ""

# Set up paths for innovus, genus, dc etc.
echo "1. OA_HOME=$OA_HOME"
source $garnet/.buildkite/setup.sh
echo "2. OA_HOME=$OA_HOME"
source $garnet/.buildkite/setup-calibre.sh
echo "3. OA_HOME=$OA_HOME"
# 
echo "buildkite (but not arm7 (???)) errs if OA_HOME is set"
echo "unset OA_HOME"
unset OA_HOME
echo "4. OA_HOME=$OA_HOME"

# Oop "make rtl" needs GARNET_HOME env var
export GARNET_HOME=$garnet

# Make a build space for mflowgen; clone mflowgen
echo ""; echo pwd=`pwd`; echo ""
if [ "$USER" == "buildkite-agent" ]; then
    build=$garnet/mflowgen/test
else
    build=/sim/$USER
fi
test  -d $build || mkdir $build; cd $build
test  -d $build/mflowgen || git clone https://github.com/cornell-brg/mflowgen.git
mflowgen=$build/mflowgen
echo ""

# tsmc16 adk
# Yeah, this ain't gonna fly.
# gitlab repo requires username/pwd permissions and junk
# 
# test -d tsmc16-adk || git clone http://gitlab.r7arm-aha.localdomain/alexcarsello/tsmc16-adk.git
# test -d tsmc16     || ln -s tsmc16-adk tsmc16
# 
# Instead, let's just use a cached copy
cd $mflowgen/adks
cached_adk=/sim/steveri/mflowgen/adks/tsmc16-adk
# 
# Symlink to steveri no good. Apparently need permission to "touch" adk files(??)
# test -e tsmc16 || ln -s ${cached_adk} tsmc16
test -e tsmc16 || cp -rp ${cached_adk} tsmc16


# Tile_PE
module=Tile_PE
if test -d $mflowgen/$module; then
    echo "oops $mflowgen/$module exists"
    echo "giving up already love ya bye-bye"
    exit 13
fi

set -x
echo ""
mkdir $mflowgen/$module; cd $mflowgen/$module
../configure --design $garnet/mflowgen/Tile_PE
echo ""
set +x

# Targets: run "make list" and "make status"
# make list
# 
# echo "make mentor-calibre-drc \
#   |& tee mcdrc.log \
#   | gawk -f $script_home/filter.awk"


########################################################################
# Makefile assumes "python" means "python3" :(
# Python check
v=`python -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
echo "Found python version $v -- should be at least 3007"
if [ $v -lt 3007 ] ; then
  echo ""
  echo "WARNING found python version $v -- should be 3007"
  echo "WARNING I will try and fix it for you with my horrible hackiness"
  # On arm7 machine it's in /usr/local/bin, that's just how it is
  echo "ln -s bin/python /usr/local/bin/python3"
  test -d bin || mkdir bin
  (cd bin; ln -s /usr/local/bin/python3 python)
  export PATH=`pwd`/bin:"$PATH"
  hash -r
  v=`python -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
  echo "Found python version $v -- should be at least 3007"
  if [ $v -lt 3007 ] ; then
    echo ""; echo "ERROR could not fix python sorry!!!"
  fi
  echo
fi
echo ""

# Seems to work better if OA_HOME not set(?)
# echo "Hey look OA_HOME=$OA_HOME"
nobuf='stdbuf -oL -eL'
make mentor-calibre-drc < /dev/null \
  |& $nobuf tee mcdrc.log \
  |  $nobuf gawk -f $script_home/filter.awk

# Detailed per-cell result
# CELL Tile_PE ................................................ TOTAL Result Count = 248 (248)
#     RULECHECK OPTION.COD_CHECK:WARNING ...................... TOTAL Result Count = 1   (1)
#     RULECHECK IO_CONNECT_CORE_NET_VOLTAGE_IS_CORE:WARNING ... TOTAL Result Count = 1   (1)
#     RULECHECK G.4:M2 ........................................ TOTAL Result Count = 164 (164)
#     RULECHECK M2.W.4.1 ...................................... TOTAL Result Count = 82  (82)
# ----------------------------------------------------------------------------------
echo ""; sed -n '/^CELL/,/^--- SUMMARY/p' */drc.summary \
  | grep -v SUMM

echo DONE



########################################################################
########################################################################
########################################################################
# NOTES
# 
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
