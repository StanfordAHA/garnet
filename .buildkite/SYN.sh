#!/bin/bash
set -x
TILE=$1
echo "--- BLOCK-LEVEL SYNTHESIS - ${TILE}"
  
# /sim/buildkite-agent/builds/r7arm-aha-3/tapeout-aha/mem
pwd; ls -l mem_cfg.txt mem_synth.txt || echo 'no mems (yet)'
cp $CACHEDIR/mem_cfg.txt .
cp $CACHEDIR/mem_synth.txt .
pwd; ls -l mem_cfg.txt mem_synth.txt || echo 'no mems (yet)'

set -x; cd tapeout_16; set +x; source test/module_loads.sh; set -x
ls -l genesis_verif || echo no gv; ls -l $CACHEDIR/genesis_verif || echo no cache
test -d genesis_verif || ln -s $CACHEDIR/genesis_verif

export VERBOSE=false
PWR_AWARE=1
nobuf='stdbuf -oL -eL'
filter=($nobuf ./test/run_synthesis.filter) # QUIET
filter=($nobuf cat)                         # VERBOSE
pwd; ls -l genesis_verif

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

