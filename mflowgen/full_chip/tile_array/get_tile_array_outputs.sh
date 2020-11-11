#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/tile_array/
make cadence-genus-genlib -j 2
if [ $multicorner = True ]; then
  make genlib-ff
fi
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi
mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/tile_array_tt.lib
if [ $multicorner = True ]; then
  cp -L *genlib-ff/outputs/design.lib outputs/tile_array_ff.lib
fi
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/tile_array.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/tile_array.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/tile_array.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/tile_array.gds
cp -L *Tile_MemCore/outputs/sram.spi outputs/tile_array.sram.spi
cp -L *-lvs/outputs/design_merged.lvs.v outputs/tile_array.lvs.v

