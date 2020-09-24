#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_tile/
make cadence-genus-synthesis
mkdir -p outputs

cp -L *cadence-genus-synthesis/outputs/design.v outputs/glb_tile.syn.v
cp -L *cadence-genus-synthesis/outputs/design.sdc outputs/glb_tile.syn.sdc
cp -L *cadence-genus-synthesis/outputs/design.sdf outputs/glb_tile.syn.sdf
cp -L *cadence-genus-synthesis/outputs/design.spef outputs/glb_tile.syn.spef
cp -L *cadence-genus-synthesis/outputs/design.namemap outputs/glb_tile.syn.namemap
