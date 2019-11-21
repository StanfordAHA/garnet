#!/bin/bash

echo "+++DRC: Under construction."


# Exit on error in any stage of any pipeline
set -eo pipefail

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true;  shift; fi
if [ "$1" == "-q" ]; then VERBOSE=false; shift; fi
TILE=$1

##############################################################################
echo "--- SETUP AND VERIFY ENVIRONMENT"
# (Probably could/should skip this step for buildkite)
#   - set -x; cd tapeout_16; set +x; source test/module_loads.sh; set -x

# Don't echo all the "module load" nonsense that gets sourced and sub-sourced...
set +x
  # Copied from automated-power branch
  source .buildkite/setup.sh

  # Set up for to run calibre
  module load icadv/12.30.712
  module load calibre/2019.1
set -x

# This wasn't really designed for Calibre / DRC / LVS
# set +x
#   if [ "$VERBOSE" == true ];
#     then bin/requirements_check.sh -v
#     else bin/requirements_check.sh -q
#   fi
# 
# echo ""

# Copied from garnet/tapeout_16/drc/README.txt
# $TILE is either "PE" or "MemCore"
# E.g. CACHEDIR=/sim/buildkite-agent/builds/cache

########################################################################
echo "--- DRC - ${TILE}"
set -x

top=Tile_$TILE
gds=$CACHEDIR/synth/$top/pnr.gds
drc=`pwd`/tapeout_16/drc/drc.sh

for f in $gds $drc; do ls -l $f || exit 13; done


$drc $gds $top -nofullchip -noantenna |& tee drc.log \
  | grep -v "Results = 0"

# $lvs $gds $vlg $top |& tee lvs.log \
#   | sed 's/^--- /-- /' \
#   | sed -n '/^.unning/p; /LVS REPORT/p; /^LVS complete/,$p'


# Summary
set +x
echo "+++ SUMMARY"

date
if ! grep 'Failing checks' drc.log ; then
    echo 'hooray looks like drc succeeded'
else
    echo "OOPS looks like DRC failed :("
    echo "cat failing_summary*"
    cat failing_summary*
    exit 13
fi


# 
# 
# 
# 
# 
# 
# 
# 
# ##############################################################################
# echo "--- GENERATE GARNET VERILOG, PUT IT IN CORRECT FOLDER FOR SYNTH/PNR"
# 
# set -x
# cd tapeout_16
#   test/generate.sh -v $LITTLE
# cd ..
# 
# # Move genesis_verif to its final home in the cache dir
# pwd; ls -ld genesis_verif
# cp garnet.v genesis_verif/garnet.sv
# test -d $CACHEDIR/genesis_verif && /bin/rm -rf $CACHEDIR/genesis_verif
# cp -r genesis_verif/ $CACHEDIR/genesis_verif
# ls -ld $CACHEDIR/genesis_verif
#   
# # Same for mem*.txt
# pwd; ls -l mem_cfg.txt mem_synth.txt
# cp mem_cfg.txt mem_synth.txt $CACHEDIR/
# 
# # Summary
# set +x
# echo "+++ SUMMARY"
# echo "Built genesis_verif/, mem_cfg.txt, mem_synth.txt"
# echo "Moved garnet.v => genesis_verif/garnet.sv"
# echo "Moved genesis_verif/, mem_*.txt to cache directory $CACHEDIR"
# date
# ls -ld $CACHEDIR/{genesis_verif,mem_*.txt}
# 