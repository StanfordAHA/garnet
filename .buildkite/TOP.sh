#!/bin/bash

# Exit on error from any pipe stage of any command
set -eo pipefail

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true;  shift; fi
if [ "$1" == "-q" ]; then VERBOSE=false; shift; fi


########################################################################
echo "--- MODULE LOAD REQUIREMENTS"
echo ""
set +x; source tapeout_16/test/module_loads.sh


##############################################################################
# ?????

set -x
cd pad_frame; create_pad_frame.sh; cd ..







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














# echo "--- MODULE LOAD REQUIREMENTS"
# echo ""
# set +x; source tapeout_16/test/module_loads.sh

# For debugging; echo each command before executing it
set -x

# (From tapeout_16/README in 'tapeout' branch
# P&R Flow for Top:
#     Navigate to garnet/tapeout_16/synth/GarnetSOC_pad_frame
#     Type innovus -stylus to open the Innovus tool
#     Type source ../../scripts/top_flow_multi_vt.tcl

# # For now let's try using the collateral we generated on buildkite
# CACHEDIR=/sim/buildkite-agent/builds/cache
# 
# # (if buildkite) Copy cached collateral from synthesis step
# if [ "$BUILDKITE" ]; then
#   # Copy cached collateral from synthesis step
#   echo "cp -rp $CACHEDIR/synth ."
#   cp -rp $CACHEDIR/synth/* tapeout16_synth/
# fi

# Copy in the latest synth info from previous passes (PE, mem synth)
# synth_src=$CACHEDIR/synth
# cp -rp $synth_src/* tapeout_16/synth/
synth_src=/sim/ajcars/aha-arm-soc-june-2019/implementation/synthesis/synth
cp -rp $synth_src/GarnetSOC_pad_frame/ synth/

# Navigate to garnet/tapeout_16/synth/GarnetSOC_pad_frame
# cd tapeout_16/synth/
# [ -d GarnetSOC_pad_frame ] || mkdir GarnetSOC_pad_frame
# cd GarnetSOC_pad_frame
cd synth/GarnetSOC_pad_frame



##############################################################################
# **ERROR: (TCLCMD-989): cannot open SDC file
#   'results_syn/syn_out._default_constraint_mode_.sdc'...
# **ERROR: (IMPSE-110): File '../../scripts/viewDefinition_multi_vt.tcl'
#   line 1: 1.
# 
# Need...? Garnet synthesis info I guess...? ???
# synth_Garnet=/sim/ajcars/garnet/tapeout_16/synth/Garnet
# cp -rp $synth_Garnet/* .
# Nope! Copy GarnetSOC_pad_frame, see above


##############################################################################
# **ERROR: ...  Can not open file '../Tile_PE/pnr.lib' for library set
# **ERROR: ...  Can not open file '../Tile_MemCore/pnr.lib' for library set
# **ERROR: ...  File '../../scripts/viewDefinition_multi_vt.tcl' line 3
#
# (Oops forgot to save layout collateral to cache dir) - SOLVED maybe


########################################################################
# Type innovus -stylus to open the Innovus tool
# Type source ../../scripts/top_flow_multi_vt.tcl

set -x
# echo tcl commands as they execute; also, quit when done (!)
tmpdir=`mktemp -d tmpdir.XXX`
f=top_flow_multi_vt.tcl
wrapper=$tmpdir/$f
echo "source -verbose ../../scripts/$f" > $wrapper
echo "redirect pnr.clocks {report_clocks}" >> $wrapper
echo "exit" >> $wrapper


# PWR_AWARE=1
nobuf='stdbuf -oL -eL'

# innovus -stylus -no_gui -abort_on_error -replay $wrapper || exit 13

if [ "$VERBOSE" == true ];
  then filter=($nobuf cat)                          # VERBOSE
  else filter=($nobuf ../../test/run_layout.filter) # QUIET
fi

$nobuf innovus -stylus -no_gui -abort_on_error -replay $wrapper \
  | ${filter[*]} \
  || exit 13

/bin/rm -rf $tmpdir
set +x
echo 'Done!'

mod=GarnetSOC_pad_frame

set +x
echo "+++ PNR SUMMARY - "
echo ""
echo 'grep "DRC violations"  synth/$mod/innovus.logv | tail -n 1'
echo 'grep "Message Summary" synth/$mod/innovus.logv | tail -n 1'
echo ""
grep "DRC violations"  synth/${mod}/innovus.logv | tail -n 1
grep "Message Summary" synth/${mod}/innovus.logv | tail -n 1
echo ""
echo "CLOCK"
pwd
ls  synth/$mod/pnr.clocks
cat synth/$mod/pnr.clocks \
  | sed -n '/Descriptions/,$p' | sed -n '4,$p'









# # (Most of this is copied from synth/README file in tapeout_sr)
# 
# # Copy in a full-chip post-synthesis netlist, see notes below
# % synth_src=$CACHEDIR/synth/
# % cp -rp $synth_src/GarnetSOC_pad_frame/ garnet/tapeout_16/synth
# 
# # Make your way to the new local synth dir
# % cd garnet/tapeout_16/synth/GarnetSOC_pad_frame/
