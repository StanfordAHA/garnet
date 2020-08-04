#!/bin/bash

# SystemRDL run
make -C $GARNET_HOME/global_buffer rtl

cat $GARNET_HOME/global_buffer/rtl/global_buffer_param.svh >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/global_buffer_pkg.svh >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/axil_ifc.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/cfg_ifc.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/glb_dummy_start.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/glb_dummy_end.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/global_buffer.sv >> outputs/design.v
