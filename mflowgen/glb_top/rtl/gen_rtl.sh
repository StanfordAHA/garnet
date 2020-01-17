#!/bin/bash
cat $GARNET_HOME/global_buffer/rtl/global_buffer_pkg.sv >> outputs/design.v
cat $GARNET_HOME/global_buffer/rtl/global_buffer.sv >> outputs/design.v
