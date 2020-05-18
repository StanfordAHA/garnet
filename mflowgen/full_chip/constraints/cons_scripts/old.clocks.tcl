#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Clocks
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 14, 2020
#------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Clock Parameters
# ------------------------------------------------------------------------------
set   cgra_master_clock_period        ${dc_clock_period}
set   soc_master_clock_period         1.0

# Allowed clock division factors are 1, 2, 4, 8, 16, 32
set   cgra_clock_div_factor           1
set   soc_clock_div_factor            2


# ------------------------------------------------------------------------------
# Create Source Clocks
# ------------------------------------------------------------------------------

# External Master Clock
create_clock -name cgra_master_clk -period ${cgra_master_clock_period} \
    [get_ports $port_names(master_clk)]

# Internal Alternate Master Clock
create_clock -name soc_master_clk -period ${soc_master_clock_period} \
    [get_pins core/ALT_MASTER_CLK]

# Relax boundary between these two master clocks
set   master_clk_ratio  [expr ${cgra_master_clock_period} / ${soc_master_clock_period}]
if { ${master_clk_ratio} >= 2 } {
  set_multicycle_path -setup 2 -end -from [get_clocks cgra_master_clk] -to [get_clocks soc_master_clk]
  set_multicycle_path -hold 1 -end -from [get_clocks cgra_master_clk] -to [get_clocks soc_master_clk]
}

# ------------------------------------------------------------------------------
# Create Design Master Clock
# ------------------------------------------------------------------------------
# Normally these two clocks are logically exclusive, but I am using them to
# separately constrain the SoC and CGRA paths.

create_generated_clock -name master_clk_gen_cgra \
    -source [get_ports $port_names(master_clk)] \
    -divide_by 1 \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_master_clock_switch/CLK_OUT]

create_generated_clock -name master_clk_gen_soc \
    -source [get_pins core/ALT_MASTER_CLK]\
    -divide_by 1 \
    -add \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_master_clock_switch/CLK_OUT]


# ------------------------------------------------------------------------------
# Create Divided Clocks
# ------------------------------------------------------------------------------

foreach idx [list 1 2 4 8 16 32] {
  create_generated_clock -name by${idx}_clk_cgra  \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_IN] \
      -divide_by ${idx} \
      -master_clock master_clk_gen_cgra \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_by_${idx}]

  create_generated_clock -name by${idx}_clk_soc  \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_IN] \
      -divide_by ${idx} \
      -master_clock master_clk_gen_soc \
      -add \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div/CLK_by_${idx}]
}

# ------------------------------------------------------------------------------
# Create Generated Free Clocks
# ------------------------------------------------------------------------------

create_generated_clock -name sys_clk_free \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_by_${soc_clock_div_factor}] \
    -divide_by 1 \
    -master_clock by${soc_clock_div_factor}_clk_soc \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_sys_clk/CLK_OUT]

# TLX FWD Clock
create_generated_clock -name tlx_fwd_clk_free \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_tlx_clk/CLK_by_${soc_clock_div_factor}] \
    -divide_by 1 \
    -master_clock by${soc_clock_div_factor}_clk_soc \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_tlx_clk/CLK_OUT]

# CGRA Clock
create_generated_clock -name cgra_clk_free \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_cgra_clk/CLK_by_${cgra_clock_div_factor}] \
    -divide_by 1 \
    -master_clock by${cgra_clock_div_factor}_clk_cgra \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_cgra_clk/CLK_OUT]

# ------------------------------------------------------------------------------
# Create Gated Clocks
# ------------------------------------------------------------------------------

# System Clocks
set dev_names   [list cpu dap dma0 dma1 sram nic]

foreach name $dev_names {
  create_generated_clock -name ${name}_gclk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_${name}_gclk/CP] \
      -divide_by 1 \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_${name}_gclk/Q]
}


# TLX FWD
create_generated_clock -name tlx_fwd_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_tlx_gclk/CP] \
    -divide_by 1 \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_tlx_gclk/Q]


# CGRA
create_generated_clock -name cgra_gclk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_cgra_gclk/CP] \
    -divide_by 1 \
    [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_cgra_gclk/Q]

# ------------------------------------------------------------------------------
# Peripheral Clock Sources
# ------------------------------------------------------------------------------
foreach idx [list 1 2 4 8 16 32] {
  create_generated_clock -name periph_by_${idx} \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div_from_sysclk/CLK_IN] \
      -divide_by 1 \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_div_from_sysclk/CLK_by_${idx}]
}

# ------------------------------------------------------------------------------
# Peripheral Free-running Clocks
# ------------------------------------------------------------------------------

set periph_names [list timer0 timer1 uart0 uart1 wdog]

foreach name $periph_names {
  create_generated_clock -name periph_${name}_pclk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_${name}_clk/CLK_by_1] \
      -divide_by 1 \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_${name}_clk/CLK_OUT]
}

foreach name [list dma0 dma1] {
  create_generated_clock -name periph_${name}_pclk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_${name}_pclk/CLK_by_1] \
      -divide_by 1 \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_clk_selector_${name}_pclk/CLK_OUT]
}

# ------------------------------------------------------------------------------
# Peripheral Gated Clocks
# ------------------------------------------------------------------------------
set periph_names [list timer0 timer1 uart0 uart1 wdog]

foreach name $periph_names {
  create_generated_clock -name periph_${name}_gpclk \
      -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_${name}_gclk/CP] \
      -divide_by 1 \
      [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_${name}_gclk/Q]
}


# ------------------------------------------------------------------------------
# TLX Reverse Clock
# ------------------------------------------------------------------------------
create_clock -name tlx_rev_clk -period [expr ${soc_master_clock_period} * ${soc_clock_div_factor}] \
    [get_ports $port_names(tlx_rev_clk)]

# ------------------------------------------------------------------------------
# DP JTAG Clock
# ------------------------------------------------------------------------------
create_clock -name dp_jtag_clk -period 20.0 [get_ports $port_names(dp_jtag_clk)]

set_multicycle_path -setup -end -from [get_clocks dp_jtag_clk] -to [get_clocks {dap_gclk sys_clk_free cpu_gclk}] 4
set_multicycle_path -hold -end -from [get_clocks dp_jtag_clk] -to [get_clocks {dap_gclk sys_clk_free cpu_gclk}] 3

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

# ------------------------------------------------------------------------------
# TLX FWD Channel Strobe
# ------------------------------------------------------------------------------

# For constraining outputs
create_generated_clock -name tlx_fwd_strobe \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_tlx_gclk/Q] \
    -divide_by 1 \
    -invert \
    [get_ports $port_names(tlx_fwd_clk)]

# Emulate delay through pad
set_clock_latency -max 1.5 [get_clocks tlx_fwd_strobe]

# ------------------------------------------------------------------------------
# Trace Clock
# ------------------------------------------------------------------------------
create_generated_clock -name trace_clk \
    -source [get_pins core/u_aha_platform_ctrl/u_clock_controller/u_cpu_gclk/Q] \
    -divide_by 2 \
    [get_ports $port_names(trace_clk)]

set_multicycle_path -setup -end -from [get_clocks cpu_gclk] -to [get_clocks trace_clk] 2
set_multicycle_path -hold -end -from [get_clocks cpu_gclk] -to [get_clocks trace_clk] 1

# Emulate delay through pad
set_clock_latency -max 1.5 [get_clocks trace_clk]
