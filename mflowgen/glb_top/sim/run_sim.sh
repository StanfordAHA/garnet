#!/bin/bash
RTL="inputs/design.v inputs/glb_tile.v"
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
    ${RTL} \
    -F ${TB_FILELIST}

ln -s ../xrun.log outputs/sim_glb.log
