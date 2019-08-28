#!/bin/bash

# Exit on error in any stage of any pipeline
set -eo pipefail

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true; fi

##############################################################################
echo "--- SETUP AND VERIFY ENVIRONMENT"
# (Probably could/should skip this step for buildkite)
#   - set -x; cd tapeout_16; set +x; source test/module_loads.sh; set -x

set +x
  source /cad/modules/tcl/init/bash
  module load base
  module load genesis2
set -x

set +x
  if [ "$VERBOSE" == true ];
    then bin/requirements_check.sh -v
    else bin/requirements_check.sh -q
  fi

echo ""


##############################################################################
echo "--- GENERATE GARNET VERILOG, PUT IT IN CORRECT FOLDER FOR SYNTH/PNR"

set -x
cd tapeout_16
  test/generate.sh -v
cd ..

# Move genesis_verif to its final home in the cache dir
pwd; ls -ld genesis_verif
cp garnet.v genesis_verif/garnet.sv
test -d $CACHEDIR/genesis_verif && /bin/rm -rf $CACHEDIR/genesis_verif
cp -r genesis_verif/ $CACHEDIR/genesis_verif
ls -ld $CACHEDIR/genesis_verif
  
# Same for mem*.txt
pwd; ls -l mem_cfg.txt mem_synth.txt
cp mem_cfg.txt mem_synth.txt $CACHEDIR/

# Summary
set +x
echo "+++ GEN SUMMARY"
echo "Built genesis_verif/, mem_cfg.txt, mem_synth.txt"
echo "Moved garnet.v => genesis_verif/garnet.sv"
echo "Moved genesis_verif/, mem_*.txt to cache directory $CACHEDIR"
ls -ld $CACHEDIR/{genesis_verif,mem_*.txt}
date
