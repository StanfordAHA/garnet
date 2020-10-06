#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/glb_top/
make cadence-genus-genlib
make mentor-calibre-lvs
mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/glb_top_tt.lib
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/glb_top.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/glb_top.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/glb_top.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/glb_top.gds
cp -L *mentor-calibre-lvs/outputs/design_merged.lvs.v outputs/glb_top.lvs.v
cp -L *glb_tile/outputs/sram.spi outputs/glb_top.sram.spi

