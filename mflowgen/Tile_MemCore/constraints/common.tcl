#=========================================================================
# Design Constraints File
#=========================================================================

# This constraint sets the target clock period for the chip in
# nanoseconds. Note that the first parameter is the name of the clock
# signal in your verlog design. If you called it something different than
# clk you will need to change this. You should set this constraint
# carefully. If the period is unrealistically small then the tools will
# spend forever trying to meet timing and ultimately fail. If the period
# is too large the tools will have no trouble but you will get a very
# conservative implementation.

set clock_net  clk
set clock_name ideal_clock

create_clock -name ${clock_name} \
             -period ${clock_period} \
             [get_ports ${clock_net}]

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

# Now rip this driving cell off of our passthrough signals
# We are going to use an input/output slew and tighten a bit
remove_driving_cell [get_ports stall]
remove_driving_cell config_config_data*
remove_driving_cell config_config_addr*
remove_driving_cell config_read*
remove_driving_cell config_write*
remove_driving_cell [get_ports read_config_data_in]
remove_driving_cell reset

# Make all signals limit their fanout
set_max_fanout 20 $design_name
# Make all signals meet good slew
# set_input_delay constraints for input ports
set_max_transition 0.120 $design_name

# Constrain INPUTS
# - make this non-zero to avoid hold buffers on input-registered designs
set i_delay [expr 0.2 * ${clock_period}]
set_input_delay -clock ${clock_name} ${i_delay} [all_inputs]
# Pass through should have no input delay
set pt_i_delay [expr 0.8 * ${clock_period}]
set_input_delay -clock ${clock_name} ${pt_i_delay} stall
set_input_delay -clock ${clock_name} ${pt_i_delay} config_config_data*
set_input_delay -clock ${clock_name} ${pt_i_delay} config_config_addr*
set_input_delay -clock ${clock_name} ${pt_i_delay} config_read*
set_input_delay -clock ${clock_name} ${pt_i_delay} config_write*
set_input_delay -clock ${clock_name} ${pt_i_delay} read_config_data_in
set_input_delay -clock ${clock_name} ${pt_i_delay} reset

# Constrain OUTPUTS
# set_output_delay constraints for output ports
# 100ps for margin?
set o_delay [expr 0.0 * ${clock_period}]
set_output_delay -clock ${clock_name} ${o_delay} [all_outputs]

# Set timing on pass through clock
# Set clock min delay and max delay
set clock_min_delay 0
set clock_max_delay 0.05

# Min and max delay a little more than our clock
set min_w_in [expr ${clock_max_delay} + ${pt_i_delay} + ${o_delay}]
#set min_w_in [expr $clock_max_delay]
set_min_delay -to config_out_config_addr* ${min_w_in}
set_min_delay -to config_out_config_data* ${min_w_in}
set_min_delay -to config_out_read* ${min_w_in}
set_min_delay -to config_out_write* ${min_w_in}
set_min_delay -to stall_out ${min_w_in}
set_min_delay -from read_config_data_in -to read_config_data ${min_w_in}
set_min_delay -from reset -to reset_out ${min_w_in}

# Pass through (not clock) timing margin
set alt_passthru_margin 0.03
set alt_passthru_max [expr ${min_w_in} + ${alt_passthru_margin}]
set_max_delay -to config_out_config_addr* ${alt_passthru_max}
set_max_delay -to config_out_config_data* ${alt_passthru_max}
set_max_delay -to config_out_read* ${alt_passthru_max}
set_max_delay -to config_out_write* ${alt_passthru_max}
set_max_delay -to stall_out ${alt_passthru_max}
set_max_delay -from reset -to reset_out ${alt_passthru_max}
# This doesn't need to be as tight
set rd_cfg_margin 0.300
set_max_delay -from read_config_data_in -to read_config_data [expr ${rd_cfg_margin} + ${pt_i_delay} + ${o_delay}]

# Relax config_addr -> read_config_data path
set_multicycle_path 2 -from [get_ports config_config_addr*] -to [get_ports read_config_data] -setup
set_multicycle_path 1 -from [get_ports config_config_addr*] -to [get_ports read_config_data] -hold

# 5fF approx load
set mark_approx_cap 0.025
set_load ${mark_approx_cap} config_out_config_addr*
set_load ${mark_approx_cap} config_out_config_data*
set_load ${mark_approx_cap} config_out_read* 
set_load ${mark_approx_cap} config_out_write*
set_load ${mark_approx_cap} stall_out*
set_load ${mark_approx_cap} read_config_data
set_load ${mark_approx_cap} reset_out

# Set max transition on these outputs as well
set max_trans_passthru .020
set_max_transition ${max_trans_passthru} config_out_config_addr*
set_max_transition ${max_trans_passthru} config_out_config_data*
set_max_transition ${max_trans_passthru} config_out_read* 
set_max_transition ${max_trans_passthru} config_out_write*
set_max_transition ${max_trans_passthru} stall_out*
set_max_transition ${max_trans_passthru} [get_ports read_config_data]
set_max_transition ${max_trans_passthru} reset_out

# Set input transition to match the max transition on outputs
set_input_transition ${max_trans_passthru} [get_ports stall]
set_input_transition ${max_trans_passthru} config_config_data*
set_input_transition ${max_trans_passthru} config_config_addr*
set_input_transition ${max_trans_passthru} config_read*
set_input_transition ${max_trans_passthru} config_write*
set_input_transition ${max_trans_passthru} [get_ports read_config_data_in]
set_input_transition ${max_trans_passthru} reset

#
# Set max delay on REGOUT paths?

# Constrain Feedthrough FIFO bypass
#
# Constrain SB to ~100 ps
set sb_delay 0.3
# Use this first command to constrain all feedthrough paths to just the desired SB delay
set_max_delay -from SB*_IN_* -to SB*_OUT_* [expr ${sb_delay} + ${i_delay} + ${o_delay}]
# Then override the rest of the paths to be full clock period
set_max_delay -from SB*_IN_* -to SB*_OUT_* -through [get_pins [list CB*/* DECODE*/* MemCore_inst0*/* FEATURE*/*]] ${clock_period}

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

if $::env(PWR_AWARE) {
    source inputs/dc-dont-use-constraints.tcl
    # source inputs/mem-constraints-2.tcl
    set_dont_touch [get_cells -hierarchical *u_mux_logic*]
}

# HI LO False path
set_false_path -to [get_ports hi]
set_false_path -to [get_ports lo]

