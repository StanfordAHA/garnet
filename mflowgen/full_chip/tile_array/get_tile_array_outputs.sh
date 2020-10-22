#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/tile_array/
make cadence-genus-genlib -j 2
make mentor-calibre-gdsmerge
make mentor-calibre-lvs
mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/tile_array_tt.lib
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/tile_array.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/tile_array.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/tile_array.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/tile_array.gds
cp -L *Tile_MemCore/outputs/sram.spi outputs/tile_array.sram.spi
cp -L *-lvs/outputs/design_merged.lvs.v outputs/tile_array.lvs.v

