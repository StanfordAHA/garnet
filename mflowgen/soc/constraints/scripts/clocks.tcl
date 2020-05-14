#-----------------------------------------------------------------------------
# Synopsys Design Constraint (SDC) File
#-----------------------------------------------------------------------------
# Purpose: Defining Design Clocks
#------------------------------------------------------------------------------
#
#
# Author   : Gedeon Nyengele
# Date     : May 9, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Clock Parameters
# ------------------------------------------------------------------------------
set master_clk_period               ${dc_clock_period}

set clock_uncertainty_setup         [expr $setup_margin +  $clock_period_jitter + $pre_cts_clock_skew_estimate]
set clock_uncertainty_hold          [expr $hold_margin]

# ------------------------------------------------------------------------------
# Create Master Clock
# ------------------------------------------------------------------------------
create_clock -name master_clk -period ${master_clk_period} \
    [get_ports $port_names(master_clk)]
set_clock_uncertainty -setup ${clock_uncertainty_setup} \
                             [get_clocks master_clk]
set_clock_uncertainty -hold ${clock_uncertainty_hold} \
                            [get_clocks master_clk]
set_clock_latency -source -fall -early [expr 0.0 - $clock_dutycycle_jitter] \
                                       [get_clocks master_clk]
set_clock_latency -source -fall -late  [expr 0.0 + $clock_dutycycle_jitter] \
                                       [get_clocks master_clk]
set_clock_latency $pre_cts_clock_latency_estimate \
                  [get_clocks master_clk]

# ------------------------------------------------------------------------------
# Create DP JTAG Clock (10 MHz)
# ------------------------------------------------------------------------------
create_clock -name dp_jtag_clk -period 100.0 \
    [get_ports $port_names(dp_jtag_clk)]
set_clock_uncertainty -setup ${clock_uncertainty_setup} \
                             [get_clocks dp_jtag_clk]
set_clock_uncertainty -hold ${clock_uncertainty_hold} \
                            [get_clocks dp_jtag_clk]
set_clock_latency -source -fall -early [expr 0.0 - $clock_dutycycle_jitter] \
                                       [get_clocks dp_jtag_clk]
set_clock_latency -source -fall -late  [expr 0.0 + $clock_dutycycle_jitter] \
                                       [get_clocks dp_jtag_clk]
set_clock_latency $pre_cts_clock_latency_estimate \
                  [get_clocks dp_jtag_clk]


# ------------------------------------------------------------------------------
# Create CGRA JTAG Clock (10 MHz)
# ------------------------------------------------------------------------------
create_clock -name cgra_jtag_clk -period 100.0 \
    [get_ports $port_names(cgra_jtag_clk)]
set_clock_uncertainty -setup ${clock_uncertainty_setup} \
                             [get_clocks cgra_jtag_clk]
set_clock_uncertainty -hold ${clock_uncertainty_hold} \
                            [get_clocks cgra_jtag_clk]
set_clock_latency -source -fall -early [expr 0.0 - $clock_dutycycle_jitter] \
                                       [get_clocks cgra_jtag_clk]
set_clock_latency -source -fall -late  [expr 0.0 + $clock_dutycycle_jitter] \
                                       [get_clocks cgra_jtag_clk]
set_clock_latency $pre_cts_clock_latency_estimate \
                  [get_clocks cgra_jtag_clk]

# ------------------------------------------------------------------------------
# Create TLX Reserse Clock
# ------------------------------------------------------------------------------
create_clock -name tlx_rev_clk -period ${dc_clock_period} \
    [get_ports $port_names(tlx_rev_clk)]
set_clock_uncertainty -setup ${clock_uncertainty_setup} \
                             [get_clocks tlx_rev_clk]
set_clock_uncertainty -hold ${clock_uncertainty_hold} \
                            [get_clocks tlx_rev_clk]
set_clock_latency -source -fall -early [expr 0.0 - $clock_dutycycle_jitter] \
                                       [get_clocks tlx_rev_clk]
set_clock_latency -source -fall -late  [expr 0.0 + $clock_dutycycle_jitter] \
                                       [get_clocks tlx_rev_clk]
set_clock_latency $pre_cts_clock_latency_estimate \
                  [get_clocks tlx_rev_clk]

# ------------------------------------------------------------------------------
# Create Design Clocks
# ------------------------------------------------------------------------------
# System Clock
create_generated_clock -name sys_clk \
    -source  [get_ports $port_names(master_clk)] \
    -divide_by 1 \
    [get_pins ${top_path}u_aha_platform_ctrl/u_clock_controller/u_clk_divider/CLK_by_1]

# All the following clocks are wires assigned from System Clock
# CPU_GCLK, DAP_GCLK, DMAx_GCLK, DMAx_FREE_GPCLK, SRAM_GCLK, NIC_GCLK,
# TIMERx_GCLK, UARTx_GCLK, WDOG_GCLK, TLX_FWD_CLK, CGRA_CLK

# ------------------------------------------------------------------------------
# Generated Clock for setting constraints on FWD source-sync interface
# ------------------------------------------------------------------------------

create_generated_clock -name Vclk_ssio \
    -source  [get_ports $port_names(master_clk)] \
    -divide_by 1 \
    [get_ports $port_names(tlx_fwd_clk)]
