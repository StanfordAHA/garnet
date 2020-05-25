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
# Divided Clocks
# ------------------------------------------------------------------------------
foreach idx [list 1 2 4 8 16 32] {
  set_clock_groups -asynchronous -group [get_clocks by_${idx}_mst_0_clk] -group [get_clocks by_${idx}_mst_1_clk]
}

foreach idx [list 2 4 8 16 32] {
  set_multicycle_path $idx -setup -end -from [get_clocks by_${idx}_mst_0_clk] -to [get_clocks by_1_mst_0_clk]
  set_multicycle_path [expr $idx - 1] -hold -end -from [get_clocks by_${idx}_mst_0_clk] -to [get_clocks by_1_mst_0_clk]

  set_multicycle_path $idx -setup -start -to [get_clocks by_${idx}_mst_0_clk] -from [get_clocks by_1_mst_0_clk]
  set_multicycle_path [expr $idx - 1] -hold -start -to [get_clocks by_${idx}_mst_0_clk] -from [get_clocks by_1_mst_0_clk]
}

foreach idx [list 2 4 8 16 32] {
  set_multicycle_path $idx -setup -end -from [get_clocks by_${idx}_mst_1_clk] -to [get_clocks by_1_mst_1_clk]
  set_multicycle_path [expr $idx - 1] -hold -end -from [get_clocks by_${idx}_mst_1_clk] -to [get_clocks by_1_mst_1_clk]

  set_multicycle_path $idx -setup -start -to [get_clocks by_${idx}_mst_1_clk] -from [get_clocks by_1_mst_1_clk]
  set_multicycle_path [expr $idx - 1] -hold -start -to [get_clocks by_${idx}_mst_1_clk] -from [get_clocks by_1_mst_1_clk]
}


# ------------------------------------------------------------------------------
# DP Clocks and System Clocks
# ------------------------------------------------------------------------------
set_clock_groups -asynchronous -group {dp_jtag_clk} -group {dap_clk sys_clk cpu_clk}

# ------------------------------------------------------------------------------
# CGRA JTAG and Functional Clock
# ------------------------------------------------------------------------------

set_clock_groups -asynchronous -group {cgra_jtag_clk} -group {cgra_gclk global_controller_clk}

# ------------------------------------------------------------------------------
# Trace Clock
# ------------------------------------------------------------------------------

set_multicycle_path -setup -start -from [get_clocks cpu_clk] -to [get_clocks trace_clk] 2
set_multicycle_path -hold -start -from [get_clocks cpu_clk] -to [get_clocks trace_clk] 1

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

# Master clocks
set_clock_groups -asynchronous -group {m_clk_0} -group {m_clk_1}

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
set_clock_groups -asynchronous -group {cgra_gclk cgra_fclk} -group {nic_clk cpu_clk sys_clk dma0_clk dma1_clk}

if {($cgra_master_clk_period < 2.0) && ($cgra_master_clk_period > 1.0)} {
  set_multicycle_path 2 -setup -end -from [get_clocks master_clk_0] -to [get_clocks master_clk_1]
  set_multicycle_path 1 -hold -end -from [get_clocks master_clk_0] -to [get_clocks master_clk_1]

  set_multicycle_path 2 -setup -start -to [get_clocks master_clk_0] -from [get_clocks master_clk_1]
  set_multicycle_path 1 -hold -start -to [get_clocks master_clk_0] -from [get_clocks master_clk_1]
}


# ------------------------------------------------------------------------------
# TLX and Rest of SoC
# ------------------------------------------------------------------------------
set_clock_groups -asynchronous -group {tlx_rev_clk} -group {sys_clk tlx_fwd_gclk tlx_fwd_fclk cpu_clk nic_clk}
set_clock_groups -asynchronous -group {tlx_fwd_fclk tlx_fwd_gclk} -group {sys_clk nic_clk dma0_clk dma1_clk cpu_clk}
