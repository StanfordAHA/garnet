#!/bin/bash

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true;  shift; fi
if [ "$1" == "-q" ]; then VERBOSE=false; shift; fi

TILE=$1
echo "---  PNR FLOW FOR TILES (LAYOUT) - ${TILE}"

set -x; cd tapeout_16; set +x; source test/module_loads.sh; set -x
cp -rp $CACHEDIR/synth .  

f=Tile_${TILE}/results_syn/final_area.rpt
if ! test -f synth/$f; then
    echo "  Cannot find final_area.rpt for $TILE tile - giving up"
    exit 13
fi

export VERBOSE=false
PWR_AWARE=1
nobuf='stdbuf -oL -eL'
filter=cat                      # VERBOSE
filter=./test/run_layout.filter # QUIET
$nobuf ./run_layout.csh Tile_${TILE} $PWR_AWARE \
  | $nobuf $filter \
  || exit 13
