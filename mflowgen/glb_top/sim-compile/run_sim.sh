#!/bin/bash
cp $GARNET_HOME/global_buffer/Makefile ./
cp -r $GARNET_HOME/global_buffer/sim ./

CLK_PERIOD=${sim_clock_period}ns

(
    set -x;
    CLK_PERIOD=$CLK_PERIOD \
    HEADER_FILES="inputs/header/global_buffer_param.svh inputs/header/glb.svh" \
    DESIGN_FILES="inputs/design.v" \
    TB_FILES="-F sim/tb_global_buffer.f" \
    TOOL=$tool \
    make compile
)

if [ $tool = "XCELIUM" ]; then
  cp ./xrun.log ./outputs/sim.log
elif [ $tool = "VCS" ]; then
  cp ./vcs.log ./outputs/sim.log
fi

cd outputs

if [ $tool = "XCELIUM" ]; then
  ln -s ../xcelium.d
elif [ $tool = "VCS" ]; then
  ln -s ../simv.daidir
  ln -s ../simv
fi

