#!/bin/bash

set -e;    # FAIL if any individual command fails

mflowgen run --design $GARNET_HOME/mflowgen/Tile_PE/
make synopsys-dc-lib2db
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

make pwr-aware-gls

mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/Tile_PE_tt.lib
cp -L *synopsys-dc-lib2db/outputs/design.db outputs/Tile_PE_tt.db
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/Tile_PE.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/Tile_PE.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/Tile_PE.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/Tile_PE.gds
cp -L *-lvs/outputs/design_merged.lvs.v outputs/Tile_PE.lvs.v
cp -L *cadence-innovus-signoff/outputs/design.vcs.pg.v outputs/Tile_PE.vcs.pg.v
cp -L *cadence-innovus-signoff/outputs/design.pt.sdc outputs/Tile_PE.pt.sdc
cp -L *cadence-innovus-signoff/outputs/design.spef.gz outputs/Tile_PE.spef.gz
