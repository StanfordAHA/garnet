#!/bin/bash
mflowgen run --design $GARNET_HOME/mflowgen/global_controller/
make synopsys-dc-lib2db
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

mkdir -p outputs
cp -L *cadence-genus-genlib/outputs/design.lib outputs/global_controller_tt.lib
cp -L *synopsys-dc-lib2db/outputs/design.db outputs/global_controller_tt.db
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/global_controller.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/global_controller.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/global_controller.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/global_controller.gds
cp -L *-lvs/outputs/design_merged.lvs.v outputs/global_controller.lvs.v

