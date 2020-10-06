#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/Tile_PE/
make cadence-genus-genlib
make mentor-calibre-gdsmerge
make mentor-calibre-lvs
mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/Tile_PE_tt.lib
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_PE.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/Tile_PE.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/Tile_PE.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/Tile_PE.gds
cp -L *mentor-calibre-lvs/outputs/design_merged.lvs.v outputs/Tile_PE.lvs.v

