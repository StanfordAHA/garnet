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

set_multicycle_path -setup -end -from [get_clocks cpu_clk] -to [get_clocks trace_clk] 2
set_multicycle_path -hold -end -from [get_clocks cpu_clk] -to [get_clocks trace_clk] 1

# Emulate delay through pad
set_clock_latency -max 1.5 [get_clocks trace_clk]
