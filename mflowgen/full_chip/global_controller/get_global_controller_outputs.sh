#!/bin/bash
set -eo pipefail   # Fail when/if any individual command in the script fails

mflowgen run --design $GARNET_HOME/mflowgen/global_controller/
make synopsys-dc-lib2db
if command -v calibre &> /dev/null
then
    make mentor-calibre-lvs
else
    make cadence-pegasus-lvs
fi

mkdir -p outputs

if [ -f *cadence-genus-genlib/outputs/design.lib ]; then 
  cp -L *cadence-genus-genlib/outputs/design.lib outputs/global_controller_tt.lib

elif [ -f *cadence-innovus-genlib/outputs/design.lib ]; then
  cp -L *cadence-innovus-genlib/outputs/design.lib outputs/global_controller_tt.lib
fi

cp -L *synopsys-dc-lib2db/outputs/design.db outputs/global_controller_tt.db
cp -L *cadence-innovus-signoff/outputs/design.lef outputs/global_controller.lef
cp -L *cadence-innovus-signoff/outputs/design.vcs.v outputs/global_controller.vcs.v
cp -L *cadence-innovus-signoff/outputs/design.sdf outputs/global_controller.sdf
cp -L *cadence-innovus-signoff/outputs/design-merged.gds outputs/global_controller.gds
cp -L *-lvs/outputs/design_merged.lvs.v outputs/global_controller.lvs.v

