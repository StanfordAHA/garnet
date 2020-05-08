#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/Tile_MemCore/
make synopsys-ptpx-genlibdb
make mentor-calibre-gdsmerge
make mentor-calibre-lvs
mkdir -p outputs
cp -L *synopsys-ptpx-genlibdb/outputs/design.lib outputs/Tile_MemCore_tt.lib
cp -L *synopsys-ptpx-genlibdb/outputs/design.db outputs/Tile_MemCore.db
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_MemCore.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/Tile_MemCore.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/Tile_MemCore.sdf
cp -L *mentor-calibre-gdsmerge/outputs/design_merged.gds outputs/Tile_MemCore.gds
cp -L *mentor-calibre-lvs/outputs/design_merged.lvs.v outputs/Tile_MemCore.lvs.v
cp -L *gen_sram_macro/outputs/sram.spi outputs/sram.spi

