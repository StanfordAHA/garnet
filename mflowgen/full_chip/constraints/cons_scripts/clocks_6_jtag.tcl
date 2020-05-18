#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: JTAG Clocks
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 17, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# DP JTAG Clock
# ------------------------------------------------------------------------------
create_clock -name dp_jtag_clk -period 20.0 [get_ports $port_names(dp_jtag_clk)]

set_multicycle_path -setup -end -from [get_clocks dp_jtag_clk] -to [get_clocks {dap_clk sys_clk cpu_clk}] 4
set_multicycle_path -hold -end -from [get_clocks dp_jtag_clk] -to [get_clocks {dap_clk sys_clk cpu_clk}] 3

# ------------------------------------------------------------------------------
# CGRA JTAG Clock
# ------------------------------------------------------------------------------
create_clock -name cgra_jtag_clk -period 20.0 [get_ports $port_names(cgra_jtag_clk)]

set_multicycle_path -setup -end -from [get_clocks cgra_jtag_clk] -to [get_clocks cgra_gclk] 4
set_multicycle_path -hold -end -from [get_clocks cgra_jtag_clk] -to [get_clocks cgra_gclk] 3

# ------------------------------------------------------------------------------
# Butterphy JTAG Clock
# ------------------------------------------------------------------------------
create_clock -name btfy_jtag_clk -period 20.0 [get_ports $port_names(btfy_jtag_clk)]
