#-----------------------------------------------------------------------------
# Synopsys Design Constraint (SDC) File
#-----------------------------------------------------------------------------
# Purpose: Non-SSI IO Constraints
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 8, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Power-On Reset
# ------------------------------------------------------------------------------
set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks master_clk] [get_ports $port_names(poreset)]
set_input_delay -add_delay -min 0.0 -clock [get_clocks master_clk] [get_ports $port_names(poreset)]

set_multicycle_path -setup -end -through [get_ports $port_names(poreset)] 5
set_multicycle_path -hold -end -through [get_ports $port_names(poreset)] 4

# ------------------------------------------------------------------------------
# DP JTAG IO
# ------------------------------------------------------------------------------
set_input_delay -max 5.0 -clock [get_clocks dp_jtag_clk] $port_names(dp_jtag_tdi)
set_input_delay -add_delay -min 0.0 -clock [get_clocks dp_jtag_clk] $port_names(dp_jtag_tdi)

set_input_delay -max 5.0 -clock [get_clocks dp_jtag_clk] $port_names(dp_jtag_tms)
set_input_delay -add_delay -min 0.0 -clock [get_clocks dp_jtag_clk] $port_names(dp_jtag_tms)

set_output_delay -max 5.0 -clock [get_clocks dp_jtag_clk] $port_names(dp_jtag_tdo)
set_output_delay -add_delay -min -0.0 -clock [get_clocks dp_jtag_clk] $port_names(dp_jtag_tdo)

set_input_delay -max 5.0 -clock [get_clocks dp_jtag_clk] $port_names(dp_jtag_reset)
set_input_delay -add_delay -min 0.0 -clock [get_clocks dp_jtag_clk] $port_names(dp_jtag_reset)

# ------------------------------------------------------------------------------
# CGRA JTAG IO
# ------------------------------------------------------------------------------
set_input_delay -max 5.0 -clock [get_clocks cgra_jtag_clk] $port_names(cgra_jtag_tdi)
set_input_delay -add_delay -min 0.0 -clock [get_clocks cgra_jtag_clk] $port_names(cgra_jtag_tdi)

set_input_delay -max 5.0 -clock [get_clocks cgra_jtag_clk] $port_names(cgra_jtag_tms)
set_input_delay -add_delay -min 0.0 -clock [get_clocks cgra_jtag_clk] $port_names(cgra_jtag_tms)

set_output_delay -max 5.0 -clock [get_clocks cgra_jtag_clk] $port_names(cgra_jtag_tdo)
set_output_delay -add_delay -min -0.0 -clock [get_clocks cgra_jtag_clk] $port_names(cgra_jtag_tdo)


# ------------------------------------------------------------------------------
# TPIU
# ------------------------------------------------------------------------------
set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(tpiu_trace_data)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(tpiu_trace_data)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(tpiu_trace_swo)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(tpiu_trace_swo)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(tpiu_trace_clk)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(tpiu_trace_clk)]

# ------------------------------------------------------------------------------
# UART
# ------------------------------------------------------------------------------
set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(uart0_rxd)]
set_input_delay -add_delay -min 0.0 -clock [get_clocks sys_clk] [get_ports $port_names(uart0_rxd)]
set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(uart0_txd)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(uart0_txd)]

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(uart1_rxd)]
set_input_delay -add_delay -min 0.0 -clock [get_clocks sys_clk] [get_ports $port_names(uart1_rxd)]
set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(uart1_txd)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(uart1_txd)]

# ------------------------------------------------------------------------------
# Pad Strength
# ------------------------------------------------------------------------------
set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp0)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp0)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp1)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp1)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp2)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp2)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp3)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp3)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp4)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp4)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp5)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp5)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp6)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp6)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp7)]
set_output_delay -add_delay -min -0.0 -clock [get_clocks sys_clk] [get_ports $port_names(out_pad_ds_grp7)]

# ------------------------------------------------------------------------------
# Loop Back
# ------------------------------------------------------------------------------
set_multicycle_path -setup -end -through [get_ports $port_names(loop_back_select)] 5
set_multicycle_path -hold -end -through [get_ports $port_names(loop_back_select)] 4

set_multicycle_path -setup -end -through [get_ports $port_names(loop_back)] 5
set_multicycle_path -hold -end -through [get_ports $port_names(loop_back)] 4

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] [get_ports $port_names(loop_back_select)]
set_input_delay -add_delay -min 0.0 -clock [get_clocks sys_clk] [get_ports $port_names(loop_back_select)]

set_output_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks sys_clk] $port_names(loop_back)
set_output_delay -add_delay -min 0.0 -clock [get_clocks sys_clk] $port_names(loop_back)
