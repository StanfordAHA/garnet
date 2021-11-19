#!/bin/bash
cp $GARNET_HOME/global_buffer/Makefile ./
cp $GARNET_HOME/global_buffer/sim/*.f ./
cp $GARNET_HOME/global_buffer/sim/*.sv ./
make run HEADER_FILES="inputs/header/global_buffer_param.svh inputs/header/glb.svh" DESIGN_FILES="inputs/design.v" TB_FILES="-F tb_global_buffer.f"

cp vcs.log outputs/sim.log
