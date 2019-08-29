#!/bin/bash

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true;  shift; fi
if [ "$1" == "-q" ]; then VERBOSE=false; shift; fi

TILE=$1

########################################################################
echo "--- GET REQUIRED COLLATERAL FROM CACHE"

# Go to tapeout dir, source required modules
set -x
echo 'cd tapeout_16'
cd tapeout_16

if [ "$BUILDKITE" ]; then
  # Copy cached collateral from synthesis step
  echo "cp -rp $CACHEDIR/synth ."
  cp -rp $CACHEDIR/synth .
fi

# Quick check to see if we got the (at least one) necessary file
f=Tile_${TILE}/results_syn/final_area.rpt
if ! test -f synth/$f; then
    echo "  Cannot find final_area.rpt for $TILE tile - giving up"
    exit 13
fi

########################################################################
echo "--- MODULE LOAD REQUIREMENTS"
echo ""
set +x; source test/module_loads.sh


########################################################################
echo "--- PNR FLOW FOR TILES (LAYOUT) - ${TILE}"
echo ""
set -x
export VERBOSE=false
PWR_AWARE=1
nobuf='stdbuf -oL -eL'
filter=cat                      # VERBOSE
filter=./test/run_layout.filter # QUIET
$nobuf ./run_layout.csh Tile_${TILE} $PWR_AWARE \
  | $nobuf $filter \
  || exit 13

set +x
echo 'Done!'


# #####Streamout is finished!
# *** Message Summary: 12683 warning(s), 1 error(s)

# + find /sim/buildkite-agent/builds/cache
# + grep pnr.lib
# + echo 'no pnr.lib (yet)'
# no pnr.lib (yet)
# + cp -rp synth/ /sim/buildkite-agent/builds/cache
# + find /sim/buildkite-agent/builds/cache
# + grep pnr.lib
# /sim/buildkite-agent/builds/cache/synth/Tile_PE/pnr.lib
# + set +x
# PNR SUMMARY


set +x
echo ""
echo "+++ CLEANUP"
echo "Copy results to cache directory"
echo "Need pnr.lib, probably other things as well..."
find $CACHEDIR | grep pnr.lib || echo "no pnr.lib in cache dir (yet)"
echo ""
echo "  cp -rp synth/ $CACHEDIR"
echo ""
cp -rp synth/ $CACHEDIR
find $CACHEDIR | grep pnr.lib || echo "no pnr.lib in cache dir OH NO"
echo ""


set +x
echo "+++ PNR SUMMARY"
echo ""
echo 'grep "DRC violations" synth/Tile_${TILE}/innovus.logv | tail -n 1'
echo 'grep "Message Summary" synth/Tile_${TILE}/innovus.logv | tail -n 1'
echo ""
grep "DRC violations"  synth/Tile_${TILE}/innovus.logv | tail -n 1
grep "Message Summary" synth/Tile_${TILE}/innovus.logv | tail -n 1
echo ""
echo "CLOCK"
pwd
ls synth/Tile_${TILE}/pnr.clocks
cat synth/Tile_${TILE}/pnr.clocks \
  | sed -n '/Descriptions/,$p' | sed -n '4,$p'

#  |-------+--------+--------------+--------+-------+-------+------------|
#  | Clock | Source |     View     | Period |  Lead | Trail | Gen | Prop |
#  |  Name |        |              |        |       |       |            |
#  |-------+--------+--------------+--------+-------+-------+-----+------|
#  |  clk  |  clk   | ss_0p72_125c |  2.300 | 0.000 | 1.150 |  n  |   n  |
#  |  clk  |  clk   |  ff_0p88_0c  |  2.300 | 0.000 | 1.150 |  n  |   n  |
#  |  clk  |  clk   | ss_0p72_m40c |  2.300 | 0.000 | 1.150 |  n  |   n  |
#  +---------------------------------------------------------------------+

