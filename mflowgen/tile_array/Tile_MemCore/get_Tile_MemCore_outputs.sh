#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/Tile_MemCore/
make mentor-calibre-gdsmerge
make cadence-genus-genlib
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/Tile_MemCore_tt.lib
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_MemCore.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/Tile_MemCore.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/Tile_MemCore.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/Tile_MemCore.gds
cp -L *-lvs/outputs/design_merged.lvs.v outputs/Tile_MemCore.lvs.v
cp -L *gen_sram_macro/outputs/sram.spi outputs/sram.spi

