#!/bin/bash
cat $GARNET_HOME/global_buffer/rtl/global_buffer_pkg.svh >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/glb_axil_ifc.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/glb_cfg_ifc.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/glb_tile_dummy_l.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/glb_tile_dummy_r.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/global_buffer.sv >> outputs/design.v
