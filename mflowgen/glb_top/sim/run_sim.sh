#!/bin/bash
GLB_SRC="inputs/design.v"
GLB_TILE_SRC="inputs/glb_tile.v"
SRAM_SRC="${GARNET_HOME}/global_buffer/rtl/TS1N16FFCLLSBLVTC2048X64M8SW.sv"
TB_FILELIST="${GARNET_HOME}/global_buffer/sim/tb_global_buffer.filelist"

# SystemRDL run
xrun \
    -64bit \
    -sv \
    -sysv \
    -l xrun.log \
    -notimingchecks \
    -access +r \
    -covoverwrite \
    -top top \
    -timescale 100ps/1ps \
    +loadpli1=debpli:deb_PLIPtr \
    -initmem0 \
    -initreg0 \
    +access+rw \
    +maxdelays \
    +define+DEBUG \
    ${GLB_SRC} \
    -v ${GLB_TILE_SRC} \
    -v ${SRAM_SRC} \
    -F ${TB_FILELIST}

ln -s ../xrun.log outputs/sim.log
