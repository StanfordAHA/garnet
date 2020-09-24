#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_tile/
make synopsys-dc-synthesis
mkdir -p outputs

cp -L *synopsys-dc-synthesis/results/glb_tile.mapped.v outputs/
cp -L *synopsys-dc-synthesis/results/glb_tile.mapped.spef.gz outputs/
cp -L *synopsys-dc-synthesis/results/glb_tile.mapped.sdc outputs/
cp -L *synopsys-dc-synthesis/results/glb_tile.mapped.sdf outputs/
