#!/usr/bin/env bash

#-----------------------------------------------------------------------
# Design
#-----------------------------------------------------------------------
# Grab all design/testbench files
ln -s inputs/xcelium.d xcelium.d
if [ $waveform = "True" ]; then
    VCD_FLAG="+VCD_ON"
fi

for app in $(echo $cgra_apps | sed "s/,/ /g")
do
    set -xe;
    xrun -R  -sv_lib inputs/libcgra.so +APP0=inputs/meta/${app} $VCD_FLAG;
    cp xrun.log outputs/xrun.${app}.log;
done
