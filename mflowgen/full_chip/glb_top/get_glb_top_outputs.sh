#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_top/
make synopsys-dc-lib2db
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

mkdir -p outputs
cp -L *cadence-innovus-genlib/outputs/design.lib outputs/glb_top_tt.lib
cp -L *synopsys-dc-lib2db/outputs/design.db outputs/glb_top_tt.db
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/glb_top.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/glb_top.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/glb_top.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/glb_top.gds
cp -L *-lvs/outputs/design_merged.lvs.v outputs/glb_top.lvs.v
cp -L *glb_tile/outputs/glb_tile_sram.spi outputs/glb_top.sram.spi
cp -L *glb_tile/outputs/glb_tile_sram.v outputs/glb_top.sram.v
cp -L *glb_tile/outputs/glb_tile_sram_pwr.v outputs/glb_top.sram.pwr.v
cp -L *glb_tile/outputs/glb_tile_sram_tt.db outputs/glb_top.sram_tt.db

