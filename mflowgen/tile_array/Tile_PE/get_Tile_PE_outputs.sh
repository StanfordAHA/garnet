#!/bin/bash
../../configure --design $GARNET_HOME/mflowgen/Tile_PE/
make synopsys-ptpx-genlibdb
make mentor-calibre-gdsmerge
make mentor-calibre-lvs
mkdir -p outputs
cp -L *synopsys-ptpx-genlibdb/outputs/design.lib outputs/Tile_PE_tt.lib
cp -L *synopsys-ptpx-genlibdb/outputs/design.db outputs/Tile_PE.db
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_PE.lef
cp -L *mentor-calibre-gdsmerge/outputs/design_merged.gds outputs/Tile_PE.gds
cp -L *mentor-calibre-lvs/outputs/design.spi outputs/Tile_PE.spi

