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

# For now let's try using the collateral we generated on buildkite
CACHEDIR=/sim/buildkite-agent/builds/cache

# Copy in the latest synth info from previous passes (PE, mem synth)
# synth_src=$CACHEDIR/synth
# cp -rp $synth_src/* tapeout_16/synth/
synth_src=/sim/ajcars/aha-arm-soc-june-2019/implementation/synthesis/synth
cp -rp $synth_src/GarnetSOC_pad_frame/ tapeout_16/synth

# Navigate to garnet/tapeout_16/synth/GarnetSOC_pad_frame
# cd tapeout_16/synth/
# [ -d GarnetSOC_pad_frame ] || mkdir GarnetSOC_pad_frame
# cd GarnetSOC_pad_frame
cd tapeout_16/synth/GarnetSOC_pad_frame



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
f=top_flow_multi_vt.tcl
wrapper=/tmp/$f
echo "source -verbose ../../scripts/$f" > $wrapper
echo "exit" >> $wrapper


# PWR_AWARE=1
nobuf='stdbuf -oL -eL'
innovus -stylus -no_gui -abort_on_error -replay $wrapper || exit 13






# # (Most of this is copied from synth/README file in tapeout_sr)
# 
# # Copy in a full-chip post-synthesis netlist, see notes below
# % synth_src=$CACHEDIR/synth/
# % cp -rp $synth_src/GarnetSOC_pad_frame/ garnet/tapeout_16/synth
# 
# # Make your way to the new local synth dir
# % cd garnet/tapeout_16/synth/GarnetSOC_pad_frame/
