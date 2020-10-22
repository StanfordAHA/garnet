#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/Tile_PE/
make cadence-genus-genlib
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/Tile_PE_tt.lib
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_PE.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/Tile_PE.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/Tile_PE.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/Tile_PE.gds
cp -L *-lvs/outputs/design_merged.lvs.v outputs/Tile_PE.lvs.v

