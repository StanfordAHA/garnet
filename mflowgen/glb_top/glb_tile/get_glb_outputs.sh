#!/bin/bash
../../configure --design $GARNET_HOME/mflowgen/glb_tile/
make synopsys-ptpx-genlibdb
mkdir -p outputs
cp -L *synopsys-ptpx-genlibdb/outputs/design.lib outputs/glb_tile_tt.lib
cp -L *synopsys-ptpx-genlibdb/outputs/design.db outputs/glb_tile.db
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/glb_tile.lef
cp -L *cadence-innovus-signoff/outputs/design.gds.gz outputs/glb_tile.gds.gz

