#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/Tile_MemCore/
make cadence-genus-genlib
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

make pwr-aware-gls

mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/Tile_MemCore_tt.lib
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_MemCore.lef
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/Tile_MemCore.gds
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/Tile_MemCore.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.vcs.pg.v outputs/Tile_MemCore.vcs.pg.v
cp -L *-lvs/outputs/design_merged.lvs.v outputs/Tile_MemCore.lvs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/Tile_MemCore.sdf
cp -L *cadence-innovus-signoff/outputs/design.pt.sdc outputs/Tile_MemCore.pt.sdc
cp -L *cadence-innovus-signoff/outputs/design.spef.gz outputs/Tile_MemCore.spef.gz
cp -L *gen_sram_macro/outputs/sram.spi outputs/sram.spi
cp -L *gen_sram_macro/outputs/sram.v outputs/sram.v
cp -L *gen_sram_macro/outputs/sram-pwr.v outputs/sram-pwr.v
cp -L *gen_sram_macro/outputs/sram_tt.db outputs/sram_tt.db

