# ==============================================================================
# Clock Setup
# ==============================================================================
#
# The system has the following input clocks:
#   - master clock      (IN)      : used by most of the SoC
#   - dp_jtag clock     (IN)      : used by Coresight Debug Port
#   - cgra_jtag clock   (IN)      : used by CGRA JTAG
#   - TLX rev clock     (IN)      : used by reverse tlx logic
#
# The system has the following output clocks:
#   - trace clock       (OUT)     : output trace clock
#   - TLX fwd clock     (OUT)     : used by fwd tlx channel
#
# The system has the following internally generated clocks:
#   - CPU free-running clock (a.k.a system clock)
#   - CPU gated clock
#   - DAP clock
#   - SRAM clock
#   - TLX FWD clock
#   - CGRA clock
#   - DMA0 clock
#   - DMA1 clock
#   - Peripheral Interconnect clock
#   - Timer0 clock
#   - Timer1 clock
#   - UART0 clock
#   - UART1 clock
#   - Watchdog clock
#   - NIC Interconnect clock
#
# ==============================================================================

# ==============================================================================
# Input Clocks Creation
# ==============================================================================
set in_clock_names  [list   master_clock  \
                            dp_jtag_clock \
                            cgra_jtag_clock \
                            tlx_rev_clock \
                    ]

# PARAMETER: clock period
set in_clock_period(master_clock)                 ${dc_clock_period}
set in_clock_period(dp_jtag_clock)                10.0
set in_clock_period(cgra_jtag_clock)              10.0
set in_clock_period(tlx_rev_clock)                ${dc_clock_period}

# PARAMETER: clock port
set in_clock_port(master_clock)                   MASTER_CLK
set in_clock_port(dp_jtag_clock)                  DP_JTAG_TCK
set in_clock_port(cgra_jtag_clock)                CGRA_JTAG_TCK
set in_clock_port(tlx_rev_clock)                  TLX_REV_CLK

# PARAMETER: pre-cts skew estimate
set in_clock_skew(master_clock)                   0.00
set in_clock_skew(dp_jtag_clock)                  0.00
set in_clock_skew(cgra_jtag_clock)                0.00
set in_clock_skew(tlx_rev_clock)                  0.00

# PARAMETER: clock duty cycle jitter
set in_clock_jitter(master_clock)                 0.00
set in_clock_jitter(dp_jtag_clock)                0.00
set in_clock_jitter(cgra_jtag_clock)              0.00
set in_clock_jitter(tlx_rev_clock)                0.00

# PARAMETER: clock extra setup margin
set in_clock_extra_setup(master_clock)            0.00
set in_clock_extra_setup(dp_jtag_clock)           0.00
set in_clock_extra_setup(cgra_jtag_clock)         0.00
set in_clock_extra_setup(tlx_rev_clock)           0.00

# PARAMETER: clock hold setup margin
set in_clock_extra_hold(master_clock)             0.00
set in_clock_extra_hold(dp_jtag_clock)            0.00
set in_clock_extra_hold(cgra_jtag_clock)          0.00
set in_clock_extra_hold(tlx_rev_clock)            0.00

# PARAMETER: pre-cts clock maximum latency
set in_clock_max_latency(master_clock)            0.00
set in_clock_max_latency(dp_jtag_clock)           0.00
set in_clock_max_latency(cgra_jtag_clock)         0.00
set in_clock_max_latency(tlx_rev_clock)           0.00

# PARAMETER: pre-cts clock minimum latency
set in_clock_min_latency(master_clock)            0.00
set in_clock_min_latency(dp_jtag_clock)           0.00
set in_clock_min_latency(cgra_jtag_clock)         0.00
set in_clock_min_latency(tlx_rev_clock)           0.00

# PARAMETER: clock setup uncertainty
set in_clock_uncertainty_setup(master_clock)    [expr   $in_clock_skew(master_clock) + \
                                                        $in_clock_jitter(master_clock) + \
                                                        $in_clock_extra_setup(master_clock) \
                                                ]
set in_clock_uncertainty_setup(dp_jtag_clock)   [expr   $in_clock_skew(dp_jtag_clock) + \
                                                        $in_clock_jitter(dp_jtag_clock) + \
                                                        $in_clock_extra_setup(dp_jtag_clock) \
                                                ]
set in_clock_uncertainty_setup(cgra_jtag_clock) [expr   $in_clock_skew(cgra_jtag_clock) + \
                                                        $in_clock_jitter(cgra_jtag_clock) + \
                                                        $in_clock_extra_setup(cgra_jtag_clock) \
                                                ]
set in_clock_uncertainty_setup(tlx_rev_clock)   [expr   $in_clock_skew(tlx_rev_clock) + \
                                                        $in_clock_jitter(tlx_rev_clock) + \
                                                        $in_clock_extra_setup(tlx_rev_clock) \
                                                ]
# PARAMETER: clock hold uncertainty
set in_clock_uncertainty_hold(master_clock)     [expr   $in_clock_jitter(master_clock) + \
                                                        $in_clock_extra_hold(master_clock) \
                                                ]
set in_clock_uncertainty_hold(dp_jtag_clock)    [expr   $in_clock_jitter(dp_jtag_clock) + \
                                                        $in_clock_extra_hold(dp_jtag_clock) \
                                                ]
set in_clock_uncertainty_hold(cgra_jtag_clock)  [expr   $in_clock_jitter(cgra_jtag_clock) + \
                                                        $in_clock_extra_hold(cgra_jtag_clock) \
                                                ]
set in_clock_uncertainty_hold(tlx_rev_clock)    [expr   $in_clock_jitter(tlx_rev_clock) + \
                                                        $in_clock_extra_hold(tlx_rev_clock) \
                                                ]
# Clock Creation
foreach clock_name $in_clock_names {
  create_clock -name $clock_name -period $in_clock_period($clock_name) \
    [get_ports $in_clock_port($clock_name)]
  set_clock_latency -max $in_clock_max_latency($clock_name) [get_clocks $clock_name]
  set_clock_latency -min $in_clock_min_latency($clock_name) [get_clocks $clock_name]
  set_clock_uncertainty -setup $in_clock_uncertainty_setup($clock_name) [get_clocks $clock_name]
  set_clock_uncertainty -hold $in_clock_uncertainty_hold($clock_name) [get_clocks $clock_name]
}

# ==============================================================================
# Internally Generated Clocks Creation
# ==============================================================================
set gen_clock_names       [list   cpu_fclk  \
                                  cpu_gclk  \
                                  dap_clk   \
                                  sram_clk  \
                                  tlx_clk   \
                                  cgra_clk  \
                                  dma0_clk  \
                                  dma1_clk  \
                                  periph_clk  \
                                  timer0_clk  \
                                  timer1_clk  \
                                  uart0_clk   \
                                  uart1_clk   \
                                  wdog_clk  \
                                  nic_clk   \
                          ]

# PARAMETER: clock division factor
set gen_clock_div_factor(cpu_fclk)              1
set gen_clock_div_factor(cpu_gclk)              1
set gen_clock_div_factor(dap_clk)               1
set gen_clock_div_factor(sram_clk)              1
set gen_clock_div_factor(tlx_clk)               1
set gen_clock_div_factor(cgra_clk)              1
set gen_clock_div_factor(dma0_clk)              1
set gen_clock_div_factor(dma1_clk)              1
set gen_clock_div_factor(periph_clk)            1
set gen_clock_div_factor(timer0_clk)            1
set gen_clock_div_factor(timer1_clk)            1
set gen_clock_div_factor(uart0_clk)             1
set gen_clock_div_factor(uart1_clk)             1
set gen_clock_div_factor(wdog_clk)              1
set gen_clock_div_factor(nic_clk)               1

# PARAMETER: clock pins
set gen_clock_pin(cpu_fclk)                     CPU_FCLK
set gen_clock_pin(cpu_gclk)                     CPU_GCLK
set gen_clock_pin(dap_clk)                      DAP_CLK
set gen_clock_pin(sram_clk)                     SRAM_CLK
set gen_clock_pin(tlx_clk)                      TLX_CLK
set gen_clock_pin(cgra_clk)                     CGRA_CLK
set gen_clock_pin(dma0_clk)                     DMA0_CLK
set gen_clock_pin(dma1_clk)                     DMA1_CLK
set gen_clock_pin(periph_clk)                   PERIPH_CLK
set gen_clock_pin(timer0_clk)                   TIMER0_CLK
set gen_clock_pin(timer1_clk)                   TIMER1_CLK
set gen_clock_pin(uart0_clk)                    UART0_CLK
set gen_clock_pin(uart1_clk)                    UART1_CLK
set gen_clock_pin(wdog_clk)                     WDOG_CLK
set gen_clock_pin(nic_clk)                      NIC_CLK

# Create clocks
foreach clock_name $gen_clock_names {
  create_generated_clock -name $clock_name \
    -source [get_ports MASTER_CLK] \
    -divide_by $gen_clock_div_factor($clock_name) \
    [get_pins -hierarchical *u_platform_ctrl/$gen_clock_pin($clock_name)]
}

# ==============================================================================
# Output Clocks Creation
# ==============================================================================
set out_clock_names       [list   trace_clock_o  \
                                  tlx_fwd_clock_o \
                          ]

# PARAMETER: clock source
set out_clock_sources(trace_clock_o)            cpu_gclk;
set out_clock_sources(tlx_fwd_clock_o)          tlx_clk;

# PARAMETER: clock division factor
set out_clock_div_factor(trace_clock_o)         1
set out_clock_div_factor(tlx_fwd_clock_o)       1

# PARAMETER: clock port
set out_clock_port(trace_clock_o)               TPIU_TRACE_CLK
set out_clock_port(tlx_fwd_clock_o)             TLX_FWD_CLK

# Create clocks
foreach clock_name $out_clock_names {
  create_generated_clock -name $clock_name \
    -source [get_ports $out_clock_port($clock_name)] \
    -divide_by $out_clock_div_factor($clock_name) \
    [get_ports $out_clock_port($clock_name)]
}

# ==============================================================================
# False Paths
# ==============================================================================

# Loopback should not be timed
set_false_path -through [get_ports LOOP_BACK]

# TLX Reverse
set tlx_reverse_false_paths       [list   master_clock  \
                                          dp_jtag_clock \
                                          cgra_jtag_clock   \
                                          cpu_fclk \
                                          cpu_gclk \
                                          dap_clk \
                                          sram_clk \
                                          tlx_clk \
                                          cgra_clk \
                                          dma0_clk \
                                          dma1_clk \
                                          periph_clk \
                                          timer0_clk \
                                          timer1_clk \
                                          uart0_clk \
                                          uart1_clk \
                                          wdog_clk \
                                          nic_clk \
                                  ]

foreach async_clock $tlx_reverse_false_paths {
  set_false_path -from [get_clocks tlx_rev_clock] -to [get_clocks $async_clock]
  set_false_path -from [get_clocks $async_clock] -to [get_clocks tlx_rev_clock]
}

# DP_JTAG
set dp_jtag_false_paths           [list   master_clock  \
                                          cgra_jtag_clock   \
                                          cpu_fclk \
                                          cpu_gclk \
                                          dap_clk \
                                          sram_clk \
                                          tlx_clk \
                                          cgra_clk \
                                          dma0_clk \
                                          dma1_clk \
                                          periph_clk \
                                          timer0_clk \
                                          timer1_clk \
                                          uart0_clk \
                                          uart1_clk \
                                          wdog_clk \
                                          nic_clk \
                                  ]

foreach async_clock $dp_jtag_false_paths {
  set_false_path -from [get_clocks dp_jtag_clock] -to [get_clocks $async_clock]
  set_false_path -from [get_clocks $async_clock] -to [get_clocks dp_jtag_clock]
}

# CGRA_JTAG
set cgra_jtag_false_paths         [list   master_clock  \
                                          cpu_fclk \
                                          cpu_gclk \
                                          dap_clk \
                                          sram_clk \
                                          tlx_clk \
                                          cgra_clk \
                                          dma0_clk \
                                          dma1_clk \
                                          periph_clk \
                                          timer0_clk \
                                          timer1_clk \
                                          uart0_clk \
                                          uart1_clk \
                                          wdog_clk \
                                          nic_clk \
                                  ]

foreach async_clock $cgra_jtag_false_paths {
  set_false_path -from [get_clocks cgra_jtag_clock] -to [get_clocks $async_clock]
  set_false_path -from [get_clocks $async_clock] -to [get_clocks cgra_jtag_clock]
}

# ==============================================================================
# Design Environment
# ==============================================================================
# This constraint sets the load capacitance in picofarads of the
# output pins of your design.

set_load -pin_load $ADK_TYPICAL_ON_CHIP_LOAD [all_outputs]

# This constraint sets the input drive strength of the input pins of
# your design. We specifiy a specific standard cell which models what
# would be driving the inputs. This should usually be a small inverter
# which is reasonable if another block of on-chip logic is driving
# your inputs.

set_driving_cell -no_design_rule \
  -lib_cell $ADK_DRIVING_CELL [all_inputs]

# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name
