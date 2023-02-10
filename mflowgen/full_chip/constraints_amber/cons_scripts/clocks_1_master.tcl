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

create_clock -name master_clk_0 -period ${cgra_master_clk_period} [get_ports $port_names(master_clk)]

create_clock -name master_clk_1 -period ${soc_master_clk_period} [get_pins core/ALT_MASTER_CLK]

# ------------------------------------------------------------------------------
# Muxed Master Clocks
# ------------------------------------------------------------------------------

create_generated_clock -name m_clk_0 \
    -source [get_ports $port_names(master_clk)] \
    -divide_by 1 \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_master_clock_switch/CLK_OUT]

create_generated_clock -name m_clk_1 \
    -source [get_pins core/ALT_MASTER_CLK] \
    -divide_by 1 \
    -add \
    -master_clock master_clk_1 \
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

  # From Master 1
  create_generated_clock -name by_${idx}_mst_1_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_master_clock_switch/CLK_OUT] \
      -divide_by ${idx} \
      -master_clock m_clk_1 \
      -add \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_by_${idx}]
}
