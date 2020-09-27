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
# set_input_delay constraints for input ports
set_max_transition 0.120 $dc_design_name

# Constrain INPUTS
# - make this non-zero to avoid hold buffers on input-registered designs
set i_delay [expr 0.2 * ${dc_clock_period}]
set_input_delay -clock ${clock_name} ${i_delay} [all_inputs]

# Constrain OUTPUTS
# set_output_delay constraints for output ports
# 100ps for margin?
set o_delay [expr 0.0 * ${dc_clock_period}]
set_output_delay -clock ${clock_name} ${o_delay} [all_outputs]


