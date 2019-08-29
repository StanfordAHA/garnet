#!/bin/bash

# Exit on error from any pipe stage of any command
set -eo pipefail

echo "--- MODULE LOAD REQUIREMENTS"
echo ""
set +x; source tapeout_16/test/module_loads.sh

# For debugging; echo each command before executing it
set -x

# (From tapeout_16/README in 'tapeout' branch
# P&R Flow for Top:
#     Navigate to garnet/tapeout_16/synth/GarnetSOC_pad_frame
#     Type innovus -stylus to open the Innovus tool
#     Type source ../../scripts/top_flow_multi_vt.tcl


# Copy in the latest synth info from previous passes (PE, mem synth)
synth_src=$CACHEDIR/synth
cp -rp $synth_src/* tapeout_16/synth/

# Navigate to garnet/tapeout_16/synth/GarnetSOC_pad_frame
cd tapeout_16/synth/
mkdir GarnetSOC_pad_frame
cd    GarnetSOC_pad_frame

set -x

########################################################################
# Type innovus -stylus to open the Innovus tool
# Type source ../../scripts/top_flow_multi_vt.tcl

# echo tcl commands as they execute; also, quit when done (!)
s=../../scripts/top_flow_multi_vt.tcl
set wrapper=/tmp/top_flow_multi_vt.tcl
echo "source -verbose $s" > $wrapper
echo "exit" >> $wrapper
set s=$wrapper

# PWR_AWARE=1
nobuf='stdbuf -oL -eL'
innovus -stylus -no_gui -abort_on_error -replay $s || exit 13






# # (Most of this is copied from synth/README file in tapeout_sr)
# 
# # Copy in a full-chip post-synthesis netlist, see notes below
# % synth_src=$CACHEDIR/synth/
# % cp -rp $synth_src/GarnetSOC_pad_frame/ garnet/tapeout_16/synth
# 
# # Make your way to the new local synth dir
# % cd garnet/tapeout_16/synth/GarnetSOC_pad_frame/
