#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_tile/
make cadence-genus-genlib
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/glb_tile_tt.lib
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/glb_tile.lef
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/glb_tile.gds
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/glb_tile.sdf
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/glb_tile.vcs.v
cp -L *-lvs/outputs/design_merged.lvs.v outputs/glb_tile.lvs.v
cp -L *gen_sram_macro/outputs/sram.spi outputs/glb_tile_sram.spi
cp -L *gen_sram_macro/outputs/sram.v outputs/glb_tile_sram.v
cp -L *gen_sram_macro/outputs/sram-pwr.v outputs/glb_tile_sram_pwr.v
cp -L *gen_sram_macro/outputs/sram_tt.db outputs/glb_tile_sram_tt.db
cp -L *gen_sram_macro/outputs/sram_tt.lib outputs/glb_tile_sram_tt.lib
cp -L *gen_sram_macro/outputs/sram_ff.lib outputs/glb_tile_sram_ff.lib
