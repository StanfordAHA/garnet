#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_tile/
make synopsys-dc-synthesis
mkdir -p outputs
cp -L *synopsys-dc-synthesis/results/glb_tile.mapped.sdf outputs/glb_tile.mapped.sdf
cp -L *synopsys-dc-synthesis/results/glb_tile.mapped.v outputs/glb_tile.mapped.v
cp -L *synopsys-dc-synthesis/results/glb_tile.spef.gz outputs/glb_tile.mapped.spef.gz
