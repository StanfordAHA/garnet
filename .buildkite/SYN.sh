#!/bin/bash

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true;  shift; fi
if [ "$1" == "-q" ]; then VERBOSE=false; shift; fi

TILE=$1; shift
echo "--- BLOCK-LEVEL SYNTHESIS - ${TILE}"
  


# Need mem_synth.txt and/or mem_cfg.txt in top-level dir
pwd; ls -l mem_cfg.txt mem_synth.txt >& /dev/null || echo 'no mems (yet)'
cp $CACHEDIR/mem_cfg.txt .
cp $CACHEDIR/mem_synth.txt .
pwd; ls -l mem_cfg.txt mem_synth.txt || echo 'oops where are the mems'

cd tapeout_16
set +x; source test/module_loads.sh


# Symlink to pre-existing verilog files in the cache
ls -l genesis_verif || echo no gv
ls -l $CACHEDIR/genesis_verif || echo no cache
test -d genesis_verif || ln -s $CACHEDIR/genesis_verif


PWR_AWARE=1
nobuf='stdbuf -oL -eL'

if [ "$VERBOSE" == true ];
  then filter=($nobuf cat)                         # VERBOSE
  else filter=($nobuf ./test/run_synthesis.filter) # QUIET
fi
# pwd; ls -l genesis_verif

$nobuf ./run_synthesis.csh Tile_${TILE} ${PWR_AWARE} \
  | ${filter[*]} \
  || exit 13
pwd
ls synth/Tile_${TILE}/results_syn/final_area.rpt
# /sim/buildkite-agent/builds/r7arm-aha-2/tapeout-aha/mem/tapeout_16
cp -rp synth/ $CACHEDIR
ls $CACHEDIR/
ls $CACHEDIR/synth
ls $CACHEDIR/synth/Tile_${TILE}/results_syn/final_area.rpt

