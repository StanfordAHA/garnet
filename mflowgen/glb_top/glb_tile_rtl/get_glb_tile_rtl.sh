#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_tile/
make rtl
mkdir -p outputs
cp -L *rtl/outputs/design.v outputs/glb_tile.v
