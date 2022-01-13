#!/bin/bash
cp $GARNET_HOME/global_buffer/Makefile ./
cp -r $GARNET_HOME/global_buffer/sim ./
cp -r $GARNET_HOME/global_buffer/gls ./

# FIXME: PM standard cells should be removed!
if [ $PWR_AWARE = "True" ]; then
  NETLIST_FILES="inputs/adk/stdcells-pwr.v inputs/adk/stdcells-pm-pwr.v inputs/glb_tile_sram_pwr.v inputs/glb_tile.vcs.pg.v inputs/design.vcs.pg.v"
else
  NETLIST_FILES="inputs/glb_tile_sram.v inputs/adk/stdcells.v inputs/adk/stdcells-pm.v inputs/glb_tile.vcs.v inputs/design.vcs.v"
fi

if [ $sdf = "True" ]; then
  SDF=1
else
  SDF=0
fi

(
    set -x;
    SDF=$SDF \
    HEADER_FILES="inputs/header/global_buffer_param.svh inputs/header/glb.svh" \
    NETLIST_FILES=$NETLIST_FILES \
    TB_FILES="-F sim/tb_global_buffer.f" \
    NUM_GLB_TILES=$num_glb_tiles \
    GLB_TOP_SDF="inputs/design.sdf" \
    GLB_TILE_SDF="inputs/glb_tile.sdf" \
    TOOL=$tool \
    make compile-gls
)

cd outputs

if [ $tool = "XCELIUM" ]; then
  cp ../xrun.log ./sim.log
elif [ $tool = "VCS" ]; then
  cp ../vcs.log ./sim.log
fi

if [ $tool = "XCELIUM" ]; then
  ln -s ../xcelium.d
elif [ $tool = "VCS" ]; then
  ln -s ../simv.daidir
  ln -s ../simv
fi

