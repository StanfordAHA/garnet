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
set_dont_touch [ get_cells IOPAD* ]
set_dont_touch [ get_cells corner* ]
set_dont_touch [ get_cells ring_terminator* ]

# I/O Timing constraints
set master_clk_period     $soc_master_clk_period

# ------------------------------------------------------------------------------
# Butterphy
# ------------------------------------------------------------------------------
#set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tdi)]
#set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tdi)]
#
#set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tms)]
#set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tms)]
#
#set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_reset_n)]
#set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_reset_n)]
#
#set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_ext_rstb)]
#set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_ext_rstb)]
#
#set_input_delay -max 12 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_ext_dump_start)]
#set_input_delay -min 1.0 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_ext_dump_start)]
#
#set_output_delay -max 4 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tdo)]
#set_output_delay -min -4 -clock [get_clocks btfy_jtag_clk] [get_ports $port_names(btfy_jtag_tdo)]

# ------------------------------------------------------------------------------
# TLX FWD Channel
# ------------------------------------------------------------------------------
set tlx_fwd_outputs [list $port_names(tlx_fwd_payload_valid) \
                          $port_names(tlx_fwd_payload_data_hi) \
                          $port_names(tlx_fwd_payload_data_lo) \
                          $port_names(tlx_fwd_flow_valid) \
                          $port_names(tlx_fwd_flow_data) \
                    ]


# Output Constraints
set_output_delay -max [expr -0.500*1000] -clock [get_clocks tlx_fwd_strobe] [get_ports $tlx_fwd_outputs]
set_output_delay -min [expr 0.500*1000] -clock [get_clocks tlx_fwd_strobe] [get_ports $tlx_fwd_outputs]

set_multicycle_path -setup 0 -from [get_clocks tlx_fwd_gclk] -to [get_clocks tlx_fwd_strobe]
set_multicycle_path -hold -1 -from [get_clocks tlx_fwd_gclk] -to [get_clocks tlx_fwd_strobe]


# ------------------------------------------------------------------------------
# TLX Reverse Channel
# ------------------------------------------------------------------------------

set tls_rev_inputs  [list   $port_names(tlx_rev_payload_valid) \
                            $port_names(tlx_rev_payload_data_hi) \
                            $port_names(tlx_rev_payload_data_lo) \
                            $port_names(tlx_rev_flow_valid) \
                            $port_names(tlx_rev_flow_data) \
                    ]

# Input Constraints
set_input_delay -max [expr 0.200*1000] -clock [get_clocks tlx_rev_clk] [get_ports $tls_rev_inputs]
set_input_delay -min [expr -0.200*1000] -clock [get_clocks tlx_rev_clk] [get_ports $tls_rev_inputs]

# ------------------------------------------------------------------------------
# DP JTAG
# ------------------------------------------------------------------------------

set_input_delay -max [expr 12*1000] -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tdi)]
set_input_delay -min [expr 1.0*1000] -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tdi)]

set_input_delay -max [expr 12*1000] -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tms)]
set_input_delay -min [expr 1.0*1000] -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tms)]

set_input_delay -max [expr 12*1000] -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_reset_n)]
set_input_delay -min [expr 1.0*1000] -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_reset_n)]

set_output_delay -max [expr 4*1000] -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tdo)]
set_output_delay -min [expr -4*1000] -clock [get_clocks dp_jtag_clk] [get_ports $port_names(dp_jtag_tdo)]

# ------------------------------------------------------------------------------
# CGRA JTAG
# ------------------------------------------------------------------------------

set_input_delay -max [expr 12*1000] -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tdi)]
set_input_delay -min [expr 1.0*1000] -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tdi)]

set_input_delay -max [expr 12*1000] -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tms)]
set_input_delay -min [expr 1.0*1000] -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tms)]

set_input_delay -max [expr 12*1000] -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_reset_n)]
set_input_delay -min [expr 1.0*1000] -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_reset_n)]

set_output_delay -max [expr 4*1000] -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tdo)]
set_output_delay -min [expr -4*1000] -clock [get_clocks cgra_jtag_clk] [get_ports $port_names(cgra_jtag_tdo)]


# ------------------------------------------------------------------------------
# Trace Port
# ------------------------------------------------------------------------------

set_false_path -to [get_ports $port_names(trace_swo)]

# ------------------------------------------------------------------------------
# UART Ports
# ------------------------------------------------------------------------------

# UART0
set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks uart0_gclk] \
    [get_ports $port_names(uart0_rxd)]
set_input_delay -min [expr ${master_clk_period} * 0.3] -clock [get_clocks uart0_gclk] \
    [get_ports $port_names(uart0_rxd)]

set_output_delay -max [expr 0.3*1000] -clock [get_clocks uart0_gclk] [get_ports $port_names(uart0_txd)]
set_output_delay -min [expr -0.3*1000] -clock [get_clocks uart0_gclk] [get_ports $port_names(uart0_txd)]

set_multicycle_path -setup -end -from [get_ports $port_names(uart0_rxd)] 20
set_multicycle_path -hold -end -from [get_ports $port_names(uart0_rxd)] 19

set_multicycle_path -setup -end -to [get_ports $port_names(uart0_txd)] 20
set_multicycle_path -hold -end -to [get_ports $port_names(uart0_txd)] 19

# UART1
set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks uart1_gclk] \
    [get_ports $port_names(uart1_rxd)]
set_input_delay -min [expr ${master_clk_period} * 0.3] -clock [get_clocks uart1_gclk] \
    [get_ports $port_names(uart1_rxd)]

set_output_delay -max [expr 0.3*1000] -clock [get_clocks uart1_gclk] [get_ports $port_names(uart1_txd)]
set_output_delay -min [expr -0.3*1000] -clock [get_clocks uart1_gclk] [get_ports $port_names(uart1_txd)]

set_multicycle_path -setup -end -from [get_ports $port_names(uart1_rxd)] 20
set_multicycle_path -hold -end -from [get_ports $port_names(uart1_rxd)] 19

set_multicycle_path -setup -end -to [get_ports $port_names(uart1_txd)] 20
set_multicycle_path -hold -end -to [get_ports $port_names(uart1_txd)] 19



# ------------------------------------------------------------------------------
# Power-on Reset
# ------------------------------------------------------------------------------

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks master_clk] [get_ports $port_names(poreset_n)]
set_input_delay -min [expr ${master_clk_period} * 0.3] -clock [get_clocks master_clk] [get_ports $port_names(poreset_n)]

set_multicycle_path -setup -end -from [get_ports $port_names(poreset_n)] 4
set_multicycle_path -hold -end -from [get_ports $port_names(poreset_n)] 3
