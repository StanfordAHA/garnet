#!/bin/bash
set -x
# Exit on error in any stage of any pipeline
set -eo pipefail

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true; fi

##############################################################################
echo "+++ SETUP AND VERIFY ENVIRONMENT"
# (Probably could/should skip this step for buildkite)
#   - set -x; cd tapeout_16; set +x; source test/module_loads.sh; set -x

if [ "$VERBOSE" == true ];
  then bin/requirements_check.sh -v
  else bin/requirements_check.sh -q
fi
echo ""

##############################################################################
echo "--- GENERATE GARNET VERILOG, PUT IT IN CORRECT FOLDER FOR SYNTH/PNR"
cd tapeout_16
  test/generate.sh -v
cd ..
[ -d genesis_verif ] || echo "Where is genesis_verif?"

# pwd; ls -l genesis_verif

set -x
pwd; ls -l genesis_verif

# /sim/buildkite-agent/builds/r7arm-aha-3/tapeout-aha/mem
cp garnet.v genesis_verif/garnet.sv
test -d $$CACHEDIR/genesis_verif && /bin/rm -rf $$CACHEDIR/genesis_verif
cp -r genesis_verif/ $$CACHEDIR/genesis_verif
ls $$CACHEDIR/genesis_verif
  
# /sim/buildkite-agent/builds/r7arm-aha-3/tapeout-aha/mem
pwd; ls -l mem_cfg.txt mem_synth.txt
cp mem_cfg.txt mem_synth.txt $$CACHEDIR/

echo "+++ GEN SUMMARY (TBD)"
echo "Built genesis_verif/, mem_cfg.txt, mem_synth.txt"
echo "Moved garnet.v => genesis_verif/garnet.sv"
echo "Moved genesis_verif/, mem_*.txt to cache directory $$CACHEDIR"
date
ls -ld $$CACHEDIR/{genesis_verif,mem_*.txt}
