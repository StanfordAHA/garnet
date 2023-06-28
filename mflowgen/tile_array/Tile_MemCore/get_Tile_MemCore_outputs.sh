#!/bin/bash

set -e;    # FAIL if any individual command fails

mflowgen run --design $GARNET_HOME/mflowgen/Tile_MemCore/

if [ "$WHICH_SOC" == "amber" ]; then
make synopsys-dc-lib2db
else
make synopsys-ptpx-genlibdb
fi

if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

# 6/11/2021 Deleting this line, hopefully temporarily, so as not to break master.
# See https://github.com/StanfordAHA/garnet/issues/791 .
# make pwr-aware-gls

mkdir -p outputs
if [ "$WHICH_SOC" == "amber" ]; then
cp -L *cadence-innovus-genlib/outputs/design.lib outputs/Tile_MemCore_tt.lib
cp -L *synopsys-dc-lib2db/outputs/design.db outputs/Tile_MemCore_tt.db
else
cp -L *synopsys-ptpx-genlibdb/outputs/design.lib outputs/Tile_MemCore_tt.lib
cp -L *synopsys-ptpx-genlibdb/outputs/design.db outputs/Tile_MemCore_tt.db
fi
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_MemCore.lef
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/Tile_MemCore.gds
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/Tile_MemCore.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.vcs.pg.v outputs/Tile_MemCore.vcs.pg.v
cp -L *-lvs/outputs/design_merged.lvs.v outputs/Tile_MemCore.lvs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/Tile_MemCore.sdf
cp -L *cadence-innovus-signoff/outputs/design.pt.sdc outputs/Tile_MemCore.pt.sdc
cp -L *cadence-innovus-signoff/outputs/design.spef.gz outputs/Tile_MemCore.spef.gz
cp -L *gen_sram_macro/outputs/sram.spi outputs/sram.spi
cp -L *gen_sram_macro/outputs/sram.v outputs/sram.v
cp -L *gen_sram_macro/outputs/sram_pwr.v outputs/sram_pwr.v
cp -L *gen_sram_macro/outputs/sram_tt.db outputs/sram_tt.db

