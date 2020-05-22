#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Trace Clock
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 17, 2020
#------------------------------------------------------------------------------

create_generated_clock -name trace_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_cpu_gclk/Q] \
    -divide_by 2 \
    [get_ports $port_names(trace_clk)]
