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
             -period ${dc_clock_period} \
             [get_ports ${clock_net}]

# Deal with passthru clock
set passthru_clock_net clk_pass_through
set passthru_clock_name ideal_clock_passthru

create_clock -name ${passthru_clock_name} \
             -period ${dc_clock_period} \
             [get_ports ${passthru_clock_net}]

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

# Drive passthru ports with a particular buffer
set_driving_cell -lib_cell BUFFD2BWP16P90 clk_pass_through
# set_input_delay constraints for input ports
#
# Constrain INPUTS
# - make this non-zero to avoid hold buffers on input-registered designs
set i_delay [expr 0.2 * ${dc_clock_period}]
set_input_delay -clock ${clock_name} ${i_delay} [all_inputs]

# Clk pass through should have no input delay
set_input_delay -clock ${clock_name} 0 clk_pass_through

# Constrain OUTPUTS
# set_output_delay constraints for output ports
set o_delay [expr 0.5 * ${dc_clock_period}]
set_output_delay -clock ${clock_name} ${o_delay} [all_outputs]

# Set timing on pass through clock
# Set clock min delay and max delay
set_min_delay -from clk_pass_through -to clk*out 0
set_max_delay -from clk_pass_through -to clk*out 0.05

# Set max delay on REGOUT paths?

# Constrain config_read_out
#
# Constrain Feedthrough FIFO bypass
#
# Constrain SB to ~100 ps
set sb_delay 0.150
# Use this first command to constrain all feedthrough paths to just the desired SB delay
set_max_delay -from SB*_IN_* -to SB*_OUT_* [expr ${sb_delay} + ${i_delay} + ${o_delay}]
# Then override the rest of the paths to be full clock period
set_max_delay -from SB*_IN_* -to SB*_OUT_* -through [get_pins [list CB*/* DECODE*/* MemCore_inst0*/* FEATURE*/*]] ${dc_clock_period}

# Make all signals limit their fanout
set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

