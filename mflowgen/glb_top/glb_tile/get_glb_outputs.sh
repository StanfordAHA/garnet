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
cp -L *-lvs/outputs/design_merged.lvs.v outputs/glb_tile.lvs.v
cp -L *gen_sram_macro/outputs/sram.spi outputs/sram.spi

