#!/bin/bash

# It's bad news if Zach left his pathname in the spice file
# It causes problems during LVS (and maybe DRC as well)
echo "+++ CHECK SPICE FILE FOR ZAMYERS PATHS AND SUCH"

# This seems to work, just to delete all the includes.
# I think it's because we box the dragonphy, and it doesn't look for them?

# Example of what we don't want to see in the spice file:
#   .INCLUDE "/sim/zamyers/dragonphy2/build/mflowgen3/31-mentor-calibre-lvs/./inputs/adk/devices.cdl" 
#   .INCLUDE "/sim/zamyers/dragonphy2/build/mflowgen3/31-mentor-calibre-lvs/./inputs/adk/iocells.cdl" 
#   .INCLUDE "/sim/zamyers/dragonphy2/build/mflowgen3/31-mentor-calibre-lvs/./inputs/adk/stdcells-lvt.cdl" 
#   .INCLUDE "/sim/zamyers/dragonphy2/build/mflowgen3/31-mentor-calibre-lvs/./inputs/adk/stdcells-pm.cdl" 

spice=outputs/dragonphy_top.spi
echo "  egrep '^.INCLUDE' $spice"
if ! egrep '^.INCLUDE' $spice; then
    echo "  No zamyers or other spurious INCLUDE paths in spice file. Good!"
    echo ''
    # EVERYTHING OKAY exit without error
    exit 0
fi

# EVERYTHING NOT OKAY try and fix it
echo '---'
echo 'WARNING found zamyers paths in spice file'
echo 'I will try and fix this for you'
set -x
mv $spice ${spice}.orig
egrep -v '^.INCLUDE' ${spice}.orig > $spice


