#!/usr/bin/env bash

#-----------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------
# get placement file
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------
# Design
#-----------------------------------------------------------------------
# Grab all design/testbench files
ln -s inputs/xcelium.d xcelium.d
for app in $(echo $cgra_apps | sed "s/,/ /g")
do
    set -xe;
    # TODO: add application directory to mflowgen
    xrun -R  -sv_lib inputs/libcgra.so +APP0=inputs/meta/${app};
    cp xrun.log outputs/xrun.${app}.log;
done
