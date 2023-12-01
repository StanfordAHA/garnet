#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Exceptions for SoC Clocks
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 20, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# DP Clocks and System Clocks
# ------------------------------------------------------------------------------
set_clock_groups -asynchronous -group {dp_jtag_clk} -group {dap_clk sys_clk cpu_clk}

# ------------------------------------------------------------------------------
# CGRA JTAG and Functional Clock
# ------------------------------------------------------------------------------

# original constraint
# set_clock_groups -asynchronous -group {cgra_jtag_clk} -group {cgra_gclk cgra_fclk global_controller_clk}

# TMA2 constraint
# set_clock_groups -asynchronous -group {cgra_jtag_clk} -group {cgra_gclk cgra_fclk}

# glb fix constraint
set glb_clks [get_property [get_clocks *glb_tile_gen*/gclk*] name]
set cgra_clks $glb_clks
lappend cgra_clks cgra_gclk
lappend cgra_clks cgra_fclk
lappend cgra_clks global_controller_clk
set_clock_groups -asynchronous -group {cgra_jtag_clk} -group $cgra_clks

# ------------------------------------------------------------------------------
# Trace Clock and CPU Clock
# ------------------------------------------------------------------------------

set_max_delay $trace_clkin_period -from [get_clocks cpu_clk] -to [get_clocks trace_clkin]
set_max_delay $trace_clkin_period -from [get_clocks trace_clkin] -to [get_clocks cpu_clk]

# ------------------------------------------------------------------------------
# XGCD and NIC Clock
# ------------------------------------------------------------------------------

# set xgcd_div8_clk core/u_aha_xgcd_integration/u_xgcd_wrapper_top/clk_div_8_1

# set_max_delay [expr $xgcd_design_clk_period * 8] \
#     -from [get_clocks $xgcd_div8_clk] \
#     -to [get_clocks nic_clk]

# set_max_delay [expr $xgcd_design_clk_period * 8] \
#     -from [get_clocks nic_clk] \
#     -to [get_clocks $xgcd_div8_clk]

# ------------------------------------------------------------------------------
# Clock Controller - Clock Select
# ------------------------------------------------------------------------------

# MASTER_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_master_clock_switch/SELECT]

# SYS_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/SELECT]

# TLX_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_tlx_clk/SELECT]

# CGRA_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_cgra_clk/SELECT]

# TIMER0_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_timer0_clk/SELECT]

# TIMER1_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_timer1_clk/SELECT]

# UART0_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_uart0_clk/SELECT]

# UART1_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_uart1_clk/SELECT]

# WDOG_CLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_wdog_clk/SELECT]

# DMA0_PCLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_dma0_pclk/SELECT]

# DMA1_PCLK_SELECT

set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_dma1_pclk/SELECT]

# ------------------------------------------------------------------------------
# Clock Controller - Clock Gate
# ------------------------------------------------------------------------------

# Clock Gates
set dev_names   [list cpu dap dma0 dma1 sram nic tlx cgra timer0 timer1 uart0 uart1 wdog]

foreach dev $dev_names {
  set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_${dev}_gclk/E]
}

# Clock Enables

set dev_names   [list timer0 timer1 uart0 uart1 wdog dma0 dma1]

foreach dev $dev_names {
  set_false_path -through [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_${dev}_gated_en/E]
}

# ------------------------------------------------------------------------------
# TLX Training
# ------------------------------------------------------------------------------
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_fwd/LANE0_EN]
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_fwd/LANE1_EN]
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_fwd/LANE2_EN]
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_fwd/LANE3_EN]
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_fwd/LANE4_EN]

set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_rev/LANE0_EN]
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_rev/LANE1_EN]
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_rev/LANE2_EN]
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_rev/LANE3_EN]
set_false_path -through [get_pins core/u_aha_tlx/u_aha_tlx_ctrl/u_tlx_ctrl_rev/LANE4_EN]

# ------------------------------------------------------------------------------
# Clock Selectors
# ------------------------------------------------------------------------------

# Master Clock Switch
set_false_path -through [get_pins -hier *_clk_switch_slice/SELECT_REQ]
set_false_path -through [get_pins -hier *_clk_switch_slice/OTHERS_SELECT]

# Design Clock Switches
set_false_path -through [get_pins -hier *_clk_switch/SELECT_REQ]
set_false_path -through [get_pins -hier *_clk_switch/ALT_CLK_EN1]
set_false_path -through [get_pins -hier *_clk_switch/ALT_CLK_EN2]
set_false_path -through [get_pins -hier *_clk_switch/ALT_CLK_EN3]
set_false_path -through [get_pins -hier *_clk_switch/ALT_CLK_EN4]
set_false_path -through [get_pins -hier *_clk_switch/ALT_CLK_EN5]

# ------------------------------------------------------------------------------
# LoopBack
# ------------------------------------------------------------------------------

set_false_path -to [get_ports $port_names(loop_back)]
set_false_path -from [get_ports $port_names(loop_back_select)]

# ------------------------------------------------------------------------------
# CGRA and Rest of SoC
# ------------------------------------------------------------------------------
set_clock_groups -asynchronous -group {cgra_gclk cgra_fclk} -group {nic_clk cpu_clk sys_clk dma0_clk dma1_clk sram_clk}

# ------------------------------------------------------------------------------
# TLX and Rest of SoC
# ------------------------------------------------------------------------------
set_clock_groups -asynchronous -group {tlx_rev_clk} -group {sys_clk tlx_fwd_gclk tlx_fwd_fclk cpu_clk nic_clk}
set_clock_groups -asynchronous -group {tlx_fwd_fclk tlx_fwd_gclk} -group {sys_clk nic_clk dma0_clk dma1_clk cpu_clk}

# ------------------------------------------------------------------------------
# XGCD and NIC
# ------------------------------------------------------------------------------
# set_clock_groups -asynchronous -group $xgcd_div8_clk -group {nic_clk}
