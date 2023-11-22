#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Create Master Clocks
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 17, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Create Master Clocks
# ------------------------------------------------------------------------------

create_clock -name master_clk -period ${cgra_master_clk_period} [get_ports $port_names(master_clk)]

# ------------------------------------------------------------------------------
# Muxed Master Clocks
# ------------------------------------------------------------------------------

create_generated_clock -name m_clk_0 \
    -source [get_ports $port_names(master_clk)] \
    -divide_by $cgra_clk_div_factor \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_master_clock_switch/CLK_OUT]


# ------------------------------------------------------------------------------
# Create Divided Clocks
# ------------------------------------------------------------------------------

set clk_div_factors   [list 1 2 4 8 16 32]

foreach idx $clk_div_factors {
  # From Master 0
  create_generated_clock -name by_${idx}_mst_0_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_master_clock_switch/CLK_OUT] \
      -divide_by ${idx} \
      -master_clock m_clk_0 \
      -add \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_by_${idx}]
}
