#!/bin/bash

# default is "not amber"
[ "$WHICH_SOC" ] || WHICH_SOC=default

mflowgen run --design $GARNET_HOME/mflowgen/tile_array/

if [ "$WHICH_SOC" == "amber" ]; then
    make synopsys-dc-lib2db -j 2
else
    make synopsys-ptpx-genlibdb -j 2
fi

if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi
mkdir -p outputs

if [ "$WHICH_SOC" == "amber" ]; then
    if [ -f *cadence-genus-genlib/outputs/design.lib ]; then 
      cp -L *cadence-genus-genlib/outputs/design.lib outputs/tile_array_tt.lib
    elif [ -f *cadence-innovus-genlib/outputs/design.lib ]; then
      cp -L *cadence-innovus-genlib/outputs/design.lib outputs/tile_array_tt.lib
    fi
    cp -L *synopsys-dc-lib2db/outputs/design.db outputs/tile_array_tt.db
else
    cp -L *synopsys-ptpx-genlibdb/outputs/design.db outputs/tile_array_tt.db
    cp -L *synopsys-ptpx-genlibdb/outputs/design.lib outputs/tile_array_tt.lib
fi

cp -L *cadence-innovus-signoff/outputs/design.lef outputs/tile_array.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/tile_array.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/tile_array.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/tile_array.gds
cp -L *-lvs/outputs/design_merged.lvs.v outputs/tile_array.lvs.v
cp -L *Tile_MemCore/outputs/sram.spi outputs/tile_array.sram.spi
cp -L *Tile_MemCore/outputs/sram.v outputs/tile_array.sram.v
cp -L *Tile_MemCore/outputs/sram_pwr.v outputs/tile_array.sram.pwr.v
cp -L *Tile_MemCore/outputs/sram_tt.db outputs/tile_array.sram_tt.db


