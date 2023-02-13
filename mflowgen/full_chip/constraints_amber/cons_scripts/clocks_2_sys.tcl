#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Create System Clocks
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 17, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# System Clocks (selection using divided clocks from master_clk_1)
# ------------------------------------------------------------------------------

## SYSTEM CLOCK
foreach idx $clk_div_factors {
  create_generated_clock -name sys_by_${idx}_clk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_by_${idx}] \
      -divide_by 1 \
      -add \
      -master_clock by_${idx}_mst_1_clk \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT]
}

create_generated_clock -name sys_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock sys_by_${soc_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_sys_fclk/Q]

## CPU Clock
create_generated_clock -name cpu_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock sys_by_${soc_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_cpu_gclk/Q]

## DAP Clock
create_generated_clock -name dap_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock sys_by_${soc_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_dap_gclk/Q]

## DMA0 Clock
create_generated_clock -name dma0_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock sys_by_${soc_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_dma0_gclk/Q]

## DMA1 Clock
create_generated_clock -name dma1_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock sys_by_${soc_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_dma1_gclk/Q]

## SRAM Clock
create_generated_clock -name sram_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock sys_by_${soc_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_sram_gclk/Q]

## NIC Clock
create_generated_clock -name nic_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT] \
    -divide_by 1 \
    -master_clock sys_by_${soc_clk_div_factor}_clk \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_nic_gclk/Q]
