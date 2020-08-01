#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: IO Constraints
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 14, 2020
#------------------------------------------------------------------------------

# Don't optimize away any of our I/O cells
set_dont_touch [ get_cells ANAIOPAD* ]

set_dont_touch [ get_cells IOPAD* ]

# I/O Timing constraints
set master_clk_period     [expr ${soc_master_clk_period} * ${soc_clk_div_factor}]

# ------------------------------------------------------------------------------
# Butterphy
# ------------------------------------------------------------------------------
set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tdi)]
set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tdi)]

set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tms)]
set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tms)]

set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_reset_n)]
set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_reset_n)]

set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_ext_rstb)]
set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_ext_rstb)]

set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_ext_dump_start)]
set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_ext_dump_start)]

set_output_delay -max 4 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tdo)]
set_output_delay -min -4 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tdo)]

# ------------------------------------------------------------------------------
# TLX FWD Channel
# ------------------------------------------------------------------------------
set tlx_fwd_outputs [list $port_names(tlx_fwd_payload_valid) \
                          $port_names(tlx_fwd_payload_data_hi) \
                          $port_names(tlx_fwd_payload_data_lo) \
                          $port_names(tlx_fwd_flow_valid) \
                          $port_names(tlx_fwd_flow_data) \
                    ]

set tlx_fwd_inputs [list  $port_names(tlx_fwd_payload_ready) \
                          $port_names(tlx_fwd_flow_ready) \
                   ]

# Output Constraints
set_output_delay -max -0.500 -clock [get_clocks tlx_fwd_strobe] [get_ports $tlx_fwd_outputs]
set_output_delay -min 0.500 -clock [get_clocks tlx_fwd_strobe] [get_ports $tlx_fwd_outputs]

set_multicycle_path -setup 0 -from [get_clocks tlx_fwd_gclk] -to [get_clocks tlx_fwd_strobe]
set_multicycle_path -hold -1 -from [get_clocks tlx_fwd_gclk] -to [get_clocks tlx_fwd_strobe]

# Input constraints
set_input_delay -max [expr ${master_clk_period} * 2] -clock [get_clocks tlx_fwd_gclk] [get_ports $tlx_fwd_inputs]
set_input_delay -min 0.0 -clock [get_clocks tlx_fwd_gclk] [get_ports $tlx_fwd_inputs]

set_multicycle_path -setup -end -from [get_ports $tlx_fwd_inputs] 5
set_multicycle_path -hold -end -from [get_ports $tlx_fwd_inputs] 4

# ------------------------------------------------------------------------------
# TLX Reverse Channel
# ------------------------------------------------------------------------------

set tlx_rev_outputs [list   $port_names(tlx_rev_payload_ready) \
                            $port_names(tlx_rev_flow_ready) \
                    ]
set tls_rev_inputs  [list   $port_names(tlx_rev_payload_valid) \
                            $port_names(tlx_rev_payload_data_hi) \
                            $port_names(tlx_rev_payload_data_lo) \
                            $port_names(tlx_rev_flow_valid) \
                            $port_names(tlx_rev_flow_data) \
                    ]

# Output Constraints
set_output_delay -max  1.0 -clock [get_clocks tlx_rev_clk] [get_ports $tlx_rev_outputs]
set_output_delay -min 0.0 -clock [get_clocks tlx_rev_clk] [get_ports $tlx_rev_outputs]

set_multicycle_path -setup -end -to [get_ports $tlx_rev_outputs] 5
set_multicycle_path -hold -end -to [get_ports $tlx_rev_outputs] 4

# Input Constraints
set_input_delay -max 0.200 -clock [get_clocks tlx_rev_clk] [get_ports $tls_rev_inputs]
set_input_delay -min -0.200 -clock [get_clocks tlx_rev_clk] [get_ports $tls_rev_inputs]

# ------------------------------------------------------------------------------
# DP JTAG
# ------------------------------------------------------------------------------

set_input_delay -max 12 -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tdi)]
set_input_delay -min 1.0 -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tdi)]

set_input_delay -max 12 -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tms)]
set_input_delay -min 1.0 -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tms)]

set_input_delay -max 12 -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_reset_n)]
set_input_delay -min 1.0 -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_reset_n)]

set_output_delay -max 4 -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tdo)]
set_output_delay -min -4 -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tdo)]

# ------------------------------------------------------------------------------
# CGRA JTAG
# ------------------------------------------------------------------------------

set_input_delay -max 12 -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tdi)]
set_input_delay -min 1.0 -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tdi)]

set_input_delay -max 12 -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tms)]
set_input_delay -min 1.0 -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tms)]

set_input_delay -max 12 -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_reset_n)]
set_input_delay -min 1.0 -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_reset_n)]

set_output_delay -max 4 -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tdo)]
set_output_delay -min -4 -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tdo)]


# ------------------------------------------------------------------------------
# Trace Port
# ------------------------------------------------------------------------------

set trace_ports [list $port_names(trace_data) $port_names(trace_swo)]

set_output_delay -max -0.500 -clock [get_clocks trace_clk] [get_ports $trace_ports]
set_output_delay -min 0.500 -clock [get_clocks trace_clk] [get_ports $trace_ports]

set_multicycle_path -setup 0 -from [get_clocks cpu_clk] -to [get_clocks trace_clk]
set_multicycle_path -hold -1 -from [get_clocks cpu_clk] -to [get_clocks trace_clk]

# ------------------------------------------------------------------------------
# UART Ports
# ------------------------------------------------------------------------------

# UART0
set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks uart0_gclk] \
    [get_ports $port_names(uart0_rxd)]
set_input_delay -min [expr ${master_clk_period} * 0.3] -clock [get_clocks uart0_gclk] \
    [get_ports $port_names(uart0_rxd)]

set_output_delay -max 0.3 -clock [get_clocks uart0_gclk] [get_ports $port_names(uart0_txd)]
set_output_delay -min -0.3 -clock [get_clocks uart0_gclk] [get_ports $port_names(uart0_txd)]

set_multicycle_path -setup -end -from [get_ports $port_names(uart0_rxd)] 20
set_multicycle_path -hold -end -from [get_ports $port_names(uart0_rxd)] 19

set_multicycle_path -setup -end -to [get_ports $port_names(uart0_txd)] 20
set_multicycle_path -hold -end -to [get_ports $port_names(uart0_txd)] 19

# UART1
set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks uart1_gclk] \
    [get_ports $port_names(uart1_rxd)]
set_input_delay -min [expr ${master_clk_period} * 0.3] -clock [get_clocks uart1_gclk] \
    [get_ports $port_names(uart1_rxd)]

set_output_delay -max 0.3 -clock [get_clocks uart1_gclk] [get_ports $port_names(uart1_txd)]
set_output_delay -min -0.3 -clock [get_clocks uart1_gclk] [get_ports $port_names(uart1_txd)]

set_multicycle_path -setup -end -from [get_ports $port_names(uart1_rxd)] 20
set_multicycle_path -hold -end -from [get_ports $port_names(uart1_rxd)] 19

set_multicycle_path -setup -end -to [get_ports $port_names(uart1_txd)] 20
set_multicycle_path -hold -end -to [get_ports $port_names(uart1_txd)] 19



# ------------------------------------------------------------------------------
# Power-on Reset
# ------------------------------------------------------------------------------

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks master_clk_1] [get_ports $port_names(poreset_n)]
set_input_delay -min [expr ${master_clk_period} * 0.3] -clock [get_clocks master_clk_1] [get_ports $port_names(poreset_n)]

set_multicycle_path -setup -end -from [get_ports $port_names(poreset_n)] 4
set_multicycle_path -hold -end -from [get_ports $port_names(poreset_n)] 3
