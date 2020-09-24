#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_tile/
make cadence-genus-synthesis
mkdir -p outputs

cp -L *cadence-genus-synthesis/results/glb_tile.mapped.v outputs/
cp -L *cadence-genus-synthesis/results/glb_tile.mapped.spef.gz outputs/
cp -L *cadence-genus-synthesis/results/glb_tile.mapped.sdc outputs/
cp -L *cadence-genus-synthesis/results/glb_tile.mapped.sdf outputs/
