#!/usr/bin/env bash

#-----------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------
PARAMS="$PARAMS TOP_NAME=$top_name"
PARAMS="$PARAMS CGRA_WIDTH=$array_width"
PARAMS="$PARAMS AXI_ADDR_WIDTH=$axi_addr_width"
PARAMS="$PARAMS AXI_DATA_WIDTH=$axi_data_width"
PARAMS="$PARAMS GLB_TILE_MEM_SIZE=$glb_tile_mem_size"

#-----------------------------------------------------------------------
# Design
#-----------------------------------------------------------------------
# Grab all design/testbench files
for f in inputs/*.v; do
    [ -e "$f" ] || continue
    filename=$(readlink -f $f)
    RTL_FILES="$RTL_FILES -v $filename"
done

# Grab power domain netlist
RTL_FILES="$RTL_FILES -v ${GARNET_HOME}/tests/AN2D0*.sv"
RTL_FILES="$RTL_FILES -v ${GARNET_HOME}/tests/AO22D*.sv"

# Grab memory stubs
RTL_FILES="$RTL_FILES -v ${GARNET_HOME}/global_buffer/rtl/TS1*"

COMPILE_ARGS="-elaborate"

(
    set -xe;
    make -C ${GARNET_HOME}/tests/test_app clean;
    make -C ${GARNET_HOME}/tests/test_app libcgra.so;
    make -C ${GARNET_HOME}/tests/test_app compile ${PARAMS} RTL_FILES="${RTL_FILES}" COMPILE_ARGS=${COMPILE_ARGS};
    cp -r ${GARNET_HOME}/tests/test_app/xcelium.d outputs/xcelium.d;
    cp -r ${GARNET_HOME}/tests/test_app/xrun.log outputs/xrun.log;
    cp -r ${GARNET_HOME}/tests/test_app/libcgra.so outputs/libcgra.so;
)
