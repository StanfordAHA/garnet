#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: CGRA Clocks
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 17, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# CGRA Clocks (selection using divided clocks from master_clk_0)
# ------------------------------------------------------------------------------

foreach idx $clk_div_factors {
  create_generated_clock -name cgra_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_by_${idx}] \
      -divide_by 1 \
      -add \
      -master_clock by_${idx}_mst_0_clk \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_cgra_clk/CLK_OUT]
}

## Free Running Clock
create_generated_clock -name cgra_fclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_cgra_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock cgra_by_${cgra_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_cgra_fclk/Q]

## Gated Clock
create_generated_clock -name cgra_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_cgra_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock cgra_by_${cgra_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_cgra_gclk/Q]

## CGRA Clock from global controller
create_generated_clock -name global_controller_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_cgra_gclk/Q] \
    -divide_by 1 \
    [get_pins -hier *global_controller_inst0/clk_out]
