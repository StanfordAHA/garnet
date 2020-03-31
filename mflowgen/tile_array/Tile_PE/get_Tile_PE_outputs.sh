#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/Tile_PE/
make synopsys-ptpx-genlibdb
make mentor-calibre-gdsmerge
make mentor-calibre-lvs
mkdir -p outputs
cp -L *synopsys-ptpx-genlibdb/outputs/design.lib outputs/Tile_PE_tt.lib
cp -L *synopsys-ptpx-genlibdb/outputs/design.db outputs/Tile_PE.db
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_PE.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/Tile_PE.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.lvs.v outputs/Tile_PE.lvs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/Tile_PE.sdf
cp -L *mentor-calibre-gdsmerge/outputs/design_merged.gds outputs/Tile_PE.gds

