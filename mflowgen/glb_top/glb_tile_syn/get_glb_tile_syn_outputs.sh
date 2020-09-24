#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_tile/
make cadence-genus-synthesis
mkdir -p outputs

cp -L *cadence-genus-synthesis/output/design.v outputs/glb_tile.syn.v
cp -L *cadence-genus-synthesis/output/design.sdc outputs/glb_tile.syn.sdc
cp -L *cadence-genus-synthesis/output/design.namemap outputs/glb_tile.syn.namemap
