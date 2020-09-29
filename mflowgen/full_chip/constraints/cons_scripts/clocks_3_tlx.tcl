#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: TLX Clocks
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 17, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# TLX Clocks (selection using divided clocks from master_clk_1)
# ------------------------------------------------------------------------------

## TLX FWD CLOCK
foreach idx $clk_div_factors {
  create_generated_clock -name tlx_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_by_${idx}] \
      -divide_by 1 \
      -add \
      -master_clock by_${idx}_mst_1_clk \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_tlx_clk/CLK_OUT]
}

## Free Running Clock
create_generated_clock -name tlx_fwd_fclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_tlx_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock tlx_by_4_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_tlx_fclk/Q]

## Gated Clock
create_generated_clock -name tlx_fwd_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_tlx_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock tlx_by_4_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_tlx_gclk/Q]

## TLX FWD STROBE (Forwarded Clock)
create_generated_clock -name tlx_fwd_strobe \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_tlx_gclk/Q] \
    -divide_by 1 \
    [get_ports $port_names(tlx_fwd_clk)]

# ------------------------------------------------------------------------------
# TLX Reverse Clock
# ------------------------------------------------------------------------------
create_clock -name tlx_rev_clk -period [expr ${soc_master_clk_period} * 4] \
    [get_ports $port_names(tlx_rev_clk)]
