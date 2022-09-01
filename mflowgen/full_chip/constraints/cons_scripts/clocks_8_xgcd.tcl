#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: XGCD External Clock
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 17, 2020
#------------------------------------------------------------------------------

# XGCD Input External Clock
create_clock -name xgcd_ext_clk -period $xgcd_ext_clk_period \
    [get_ports $port_names(xgcd_ext_clk)]

# XGCD Bus Clock (DIV8 Clock)
create_clock -name xgcd_div8_clk -period [expr $xgcd_design_clk_period * 8] \
    [get_pins core/u_aha_xgcd_integration/u_xgcd_wrapper_top/clk_div_8]

# XGCD Virtual Clock for Output Constraints
create_clock -name Vxgcd_clk -period [expr $xgcd_design_clk_period * 8]
