#-----------------------------------------------------------------------------
# Synopsys Design Constraint (SDC) File
#-----------------------------------------------------------------------------
# Purpose: Source-Sync Interface Constraints
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 8, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# TLX FWD
# ------------------------------------------------------------------------------

# Outputs (data changes within 200ps of negative clock edge and is captured at rising edge)

set_output_delay -max [expr ${master_clk_period} * 0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_payload_tvalid)]
set_output_delay -add_delay -min [expr ${master_clk_period} * -0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_payload_tvalid)]

set_output_delay -max [expr ${master_clk_period} * 0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_payload_tdata_lo)]
set_output_delay -add_delay -min [expr ${master_clk_period} * -0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_payload_tdata_lo)]

set_output_delay -max [expr ${master_clk_period} * 0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_payload_tdata_hi)]
set_output_delay -add_delay -min [expr ${master_clk_period} * -0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_payload_tdata_hi)]

set_output_delay -max [expr ${master_clk_period} * 0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_flow_tvalid)]
set_output_delay -add_delay -min [expr ${master_clk_period} * -0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_flow_tvalid)]

set_output_delay -max [expr ${master_clk_period} * 0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_flow_tdata)]
set_output_delay -add_delay -min [expr ${master_clk_period} * -0.2] -clock_fall -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_flow_tdata)]

# Inputs
set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_payload_tready)]
set_input_delay -add_delay -min [expr ${master_clk_period} * 0.4] -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_payload_tready)]

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_flow_tready)]
set_input_delay -add_delay -min [expr ${master_clk_period} * 0.4] -clock [get_clocks Vclk_ssio] [get_ports $port_names(tlx_fwd_flow_tready)]

# ------------------------------------------------------------------------------
# TLX REV
# ------------------------------------------------------------------------------

# Outputs
set_output_delay -max [expr ${master_clk_period} * 0.2] -clock_fall -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_payload_tready)]
set_output_delay -add_delay -min [expr ${master_clk_period} * -0.2] -clock_fall -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_payload_tready)]

set_output_delay -max [expr ${master_clk_period} * 0.2] -clock_fall -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_flow_tready)]
set_output_delay -add_delay -min [expr ${master_clk_period} * -0.2] -clock_fall -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_flow_tready)]

# Inputs
set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_payload_tvalid)]
set_input_delay -add_delay -min [expr ${master_clk_period} * 0.4] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_payload_tvalid)]

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_payload_tdata_lo)]
set_input_delay -add_delay -min [expr ${master_clk_period} * 0.4] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_payload_tdata_lo)]

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_payload_tdata_hi)]
set_input_delay -add_delay -min [expr ${master_clk_period} * 0.4] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_payload_tdata_hi)]

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_flow_tvalid)]
set_input_delay -add_delay -min [expr ${master_clk_period} * 0.4] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_flow_tvalid)]

set_input_delay -max [expr ${master_clk_period} * 0.6] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_flow_tdata)]
set_input_delay -add_delay -min [expr ${master_clk_period} * 0.4] -clock [get_clocks tlx_rev_clk] [get_ports $port_names(tlx_rev_flow_tdata)]
