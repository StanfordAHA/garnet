set clock_net  clk
set clock_name ideal_clock

create_clock -name ${clock_name} \
             -period ${clock_period} \
             [get_ports ${clock_net}]

# Make all signals limit their fanout

set_max_fanout 20 $design_name

# Make all signals meet good slew

set_max_transition 0.1 $design_name

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

set_max_fanout 10 $design_name

# Make all signals meet good slew

set_max_transition 0.050 $design_name

########################################################################
# FROM MEM TILE (mostly)
########################################################################

# Passthrough clock inputs
set pt_clk_in [get_ports clk_pass_through]

# Passthrough clock outputs
set pt_clk_out [get_ports clk*out*]

# Other Passthrough inputs
set pt_inputs [get_ports " \
    stall \
    config_config_data* \
    config_config_addr* \
    config_read* \
    config_write* \
    reset \
    flush"]

# Other Passthrough Outputs
set pt_outputs [get_ports " \
    stall_out \
    config_out_config_data* \
    config_out_config_addr* \
    config_out_read* \
    config_out_write* \
    reset_out \
    flush_out"]

# read_config_data passthrough signals
# List these seprately because the constraints are slightly different
# (more relaxed) than for the other pt signals
set pt_read_data_inputs [get_ports read_config_data_in]
set pt_read_data_outputs [get_ports read_config_data]

# Now rip this driving cell off of our passthrough signals
# We are going to use an input/output slew and tighten a bit
remove_driving_cell $pt_clk_in
remove_driving_cell $pt_inputs
remove_driving_cell $pt_read_data_inputs

# Drive passthru ports with a particular buffer
#set_driving_cell -lib_cell BUFFD2BWP16P90 clk_pass_through
# set_input_delay constraints for input ports
#
# Constrain INPUTS
# - make this non-zero to avoid hold buffers on input-registered designs
set i_delay [expr 0.2 * ${clock_period}]
set_input_delay -clock ${clock_name} ${i_delay} [all_inputs -no_clocks]
# Pass through should have no input delay
# Fix config input delay to specific value
set pt_i_delay 0.700
set_input_delay -clock ${clock_name} ${pt_i_delay} $pt_clk_in
set_input_delay -clock ${clock_name} ${pt_i_delay} $pt_inputs
set_input_delay -clock ${clock_name} ${pt_i_delay} $pt_read_data_inputs

# Constrain OUTPUTS
# set_output_delay constraints for output ports
set o_delay [expr 0.0 * ${clock_period}]
set_output_delay -clock ${clock_name} ${o_delay} [all_outputs]
# Pass through should have no output delay
set_output_delay -clock ${clock_name} 0 $pt_clk_out
set_output_delay -clock ${clock_name} 0 $pt_outputs
set_output_delay -clock ${clock_name} 0 $pt_read_data_outputs

# Set timing on pass through clock
# Set clock min delay and max delay
set clock_min_delay 0
set clock_max_delay 0.05
set_min_delay -from $pt_clk_in -to $pt_clk_out [expr ${clock_min_delay} + ${pt_i_delay} + ${o_delay}]
set_max_delay -from $pt_clk_in -to $pt_clk_out [expr ${clock_max_delay} + ${pt_i_delay} + ${o_delay}]

# Min and max delay a little more than our clock
#set min_w_in [expr ${clock_max_delay} + ${i_delay}]
set min_w_in [expr ${clock_max_delay} + ${pt_i_delay} + ${o_delay}]
set_min_delay -to $pt_outputs ${min_w_in}
set_min_delay -to $pt_read_data_outputs ${min_w_in}

# Pass through (not clock) timing margin
set alt_passthru_margin 0.03
set alt_passthru_max [expr ${min_w_in} + ${alt_passthru_margin}]
set_max_delay -to $pt_outputs ${alt_passthru_max}
# This doesn't need to be as tight
set rd_cfg_margin 0.300
set_max_delay -from $pt_read_data_inputs -to $pt_read_data_outputs [expr ${rd_cfg_margin} + ${pt_i_delay} + ${o_delay}]

# 5fF approx load
set mark_approx_cap 0.025

set_load ${mark_approx_cap} $pt_outputs
set_load ${mark_approx_cap} $pt_read_data_outputs
set_load ${mark_approx_cap} $pt_clk_out

# Set max transition on these outputs as well
set max_trans_passthru .020
set_max_transition ${max_trans_passthru} $pt_outputs
set_max_transition ${max_trans_passthru} $pt_read_data_outputs
set_max_transition ${max_trans_passthru} $pt_clk_out

# Set input transition to match the max transition on outputs
set_input_transition ${max_trans_passthru} $pt_clk_in
set_input_transition ${max_trans_passthru} $pt_inputs
set_input_transition ${max_trans_passthru} $pt_read_data_inputs

# Relax config_addr -> read_config_data path
set_multicycle_path 2 -from [get_ports config_config_addr*] -to [get_ports read_config_data] -setup
set_multicycle_path 1 -from [get_ports config_config_addr*] -to [get_ports read_config_data] -hold
set_multicycle_path 2 -to [get_ports read_config_data* -filter direction==out] -setup
set_multicycle_path 1 -to [get_ports read_config_data* -filter direction==out] -hold

## Constrain SB to ~200 ps
set sb_delay 0.210
# Use this first command to constrain all feedthrough paths to just the desired SB delay
set_max_delay -from SB*_IN_* -to SB*_OUT_* [expr ${sb_delay} + ${i_delay} + ${o_delay}]
# Then override the rest of the paths to be full clock period
set_max_delay -from SB*_IN_* -to SB*_OUT_* -through [get_pins [list CB*/* DECODE*/* PE_inst0*/* FEATURE*/*]] ${clock_period}

########################################################################
# END
########################################################################

set_operating_conditions tt0p8v25c -library tcbn16ffcllbwp16p90tt0p8v25c

if $::env(PWR_AWARE) {
    source inputs/dc-dont-use-constraints.tcl
    # source inputs/pe-constraints-2.tcl
    set_dont_touch [get_cells -hierarchical *u_mux_logic*]
} 

# False paths

set_false_path -to [get_ports hi]
set_false_path -to [get_ports lo]
set_false_path -from [get_ports tile_id]

# Timing path to read_config_data output should never transition through a configuration
# register because we assume the register's value is constant during a read. 
set_false_path -through [get_cells -hier *config_reg_*] -to [get_ports read_config_data]

#set_tlu_plus_files -max_tluplus  $tluplus_max \
#                   -min_tluplus  $tluplus_min \
#                   -tech2itf_map $tluplus_map

# Preserve the RMUXes so that we can easily constrain them later
set rmux_cells [get_cells -hier -regexp .*RMUX_.*_sel_(inst0|value)]
set_dont_touch $rmux_cells true
set_dont_touch [get_nets -of_objects [get_pins -of_objects $rmux_cells -filter name=~O*]] true
