set clock_net  clk
set clock_name ideal_clock

create_clock -name ${clock_name} \
             -period ${dc_clock_period} \
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

########################################################################
# FROM MEM TILE (mostly)
########################################################################

# Now rip this driving cell off of our passthrough signals
# We are going to use an input/output slew and tighten a bit
remove_driving_cell clk_pass_through
remove_driving_cell stall
remove_driving_cell config_config_data*
remove_driving_cell config_config_addr*
remove_driving_cell config_read*
remove_driving_cell config_write*
remove_driving_cell read_config_data_in
remove_driving_cell reset
# Drive passthru ports with a particular buffer
#set_driving_cell -lib_cell BUFFD2BWP16P90 clk_pass_through
# set_input_delay constraints for input ports
#
# Constrain INPUTS
# - make this non-zero to avoid hold buffers on input-registered designs
set i_delay [expr 0.2 * ${dc_clock_period}]
set_input_delay -clock ${clock_name} ${i_delay} [all_inputs]
# Pass through should have no input delay
set_input_delay -clock ${clock_name} 0 clk_pass_through
set_input_delay -clock ${clock_name} 0 stall
set_input_delay -clock ${clock_name} 0 config_config_data*
set_input_delay -clock ${clock_name} 0 config_config_addr*
set_input_delay -clock ${clock_name} 0 config_read*
set_input_delay -clock ${clock_name} 0 config_write*
set_input_delay -clock ${clock_name} 0 read_config_data_in
set_input_delay -clock ${clock_name} 0 reset

# Constrain OUTPUTS
# set_output_delay constraints for output ports
set o_delay [expr 0.0 * ${dc_clock_period}]
set_output_delay -clock ${clock_name} ${o_delay} [all_outputs]

# Set timing on pass through clock
# Set clock min delay and max delay
set clock_max_delay 0.05
set_min_delay -from clk_pass_through -to clk*out 0
set_max_delay -from clk_pass_through -to clk*out ${clock_max_delay}

# Min and max delay a little more than our clock
#set min_w_in [expr ${clock_max_delay} + ${i_delay}]
set min_w_in ${clock_max_delay}
set_min_delay -to config_out_config_addr* ${min_w_in}
set_min_delay -to config_out_config_data* ${min_w_in}
set_min_delay -to config_out_read* ${min_w_in}
set_min_delay -to config_out_write* ${min_w_in}
set_min_delay -to stall_out* ${min_w_in}
set_min_delay -from read_config_data_in -to read_config_data ${min_w_in}
set_min_delay -to reset_out* ${min_w_in}

# Pass through (not clock) timing margin
set alt_passthru_margin 0.03
set alt_passthru_max [expr ${min_w_in} + ${alt_passthru_margin}]
set_max_delay -to config_out_config_addr* ${alt_passthru_max}
set_max_delay -to config_out_config_data* ${alt_passthru_max}
set_max_delay -to config_out_read* ${alt_passthru_max}
set_max_delay -to config_out_write* ${alt_passthru_max}
set_max_delay -to stall_out* ${alt_passthru_max}
set_max_delay -to reset_out* ${alt_passthru_max}
# This doesn't need to be as tight
set rd_cfg_margin 0.300
set_max_delay -from read_config_data_in -to read_config_data ${rd_cfg_margin}

# 5fF approx load
set mark_approx_cap 0.025
set_load ${mark_approx_cap} config_out_config_addr*
set_load ${mark_approx_cap} config_out_config_data*
set_load ${mark_approx_cap} config_out_read* 
set_load ${mark_approx_cap} config_out_write*
set_load ${mark_approx_cap} stall_out*
set_load ${mark_approx_cap} clk*out
set_load ${mark_approx_cap} read_config_data
set_load ${mark_approx_cap} reset_out*

# Set max transition on these outputs as well
set max_trans_passthru .020
set_max_transition ${max_trans_passthru} config_out_config_addr*
set_max_transition ${max_trans_passthru} config_out_config_data*
set_max_transition ${max_trans_passthru} config_out_read* 
set_max_transition ${max_trans_passthru} config_out_write*
set_max_transition ${max_trans_passthru} stall_out*
set_max_transition ${max_trans_passthru} clk*out
set_max_transition ${max_trans_passthru} read_config_data
set_max_transition ${max_trans_passthru} reset_out*

# Set input transition to match the max transition on outputs
set_input_transition ${max_trans_passthru} clk_pass_through
set_input_transition ${max_trans_passthru} stall
set_input_transition ${max_trans_passthru} config_config_data*
set_input_transition ${max_trans_passthru} config_config_addr*
set_input_transition ${max_trans_passthru} config_read*
set_input_transition ${max_trans_passthru} config_write*
set_input_transition ${max_trans_passthru} read_config_data_in
set_input_transition ${max_trans_passthru} reset

# Commenting out for now -- no need to have this so tight
#set read_config_data_timing 0.300
#set_max_delay -from config_config_addr* -to read_config_data ${read_config_data_timing}

# Constrain SB to ~200 ps
set sb_delay 0.210
# Use this first command to constrain all feedthrough paths to just the desired SB delay
set_max_delay -from SB*_IN_* -to SB*_OUT_* [expr ${sb_delay} + ${i_delay} + ${o_delay}]
# Then override the rest of the paths to be full clock period
set_max_delay -from SB*_IN_* -to SB*_OUT_* -through [get_pins [list CB*/* DECODE*/* PE_inst0*/* FEATURE*/*]] ${dc_clock_period}

########################################################################
# END
########################################################################

# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

set_operating_conditions tt0p8v25c -library tcbn16ffcllbwp16p90tt0p8v25c

if $::env(PWR_AWARE) {
    source inputs/dc-dont-use-constraints.tcl
    source inputs/pe-constraints-2.tcl
    set_dont_touch [get_cells -hierarchical *u_mux_logic*]
} 

# False paths

set_false_path -to [get_ports hi]
set_false_path -to [get_ports lo]
set_false_path -from [get_ports tile_id]

set_tlu_plus_files -max_tluplus  $dc_tluplus_max \
                   -min_tluplus  $dc_tluplus_min \
                   -tech2itf_map $dc_tluplus_map
