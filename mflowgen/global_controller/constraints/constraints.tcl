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

set clock_net  clk_in
set clock_name ideal_clock

create_clock -name ${clock_name} \
             -period ${clock_period} \
             [get_ports ${clock_net}]

set jtag_clock_net  tck
set jtag_clock_name jtag_clock

create_clock -name ${jtag_clock_name} \
             -period [expr 20 * ${clock_period}] \
             [get_ports ${jtag_clock_net}]

# Don't check clock domain crossing
set_false_path -from [get_clocks $clock_name] -to [get_clocks $jtag_clock_name]
set_false_path -from [get_clocks $jtag_clock_name] -to [get_clocks $clock_name]

###################################
# custom constraints
###################################
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

# set_input_delay constraints for input ports
#
# - make this non-zero to avoid hold buffers on input-registered designs

set_input_delay -clock ${clock_name} [expr ${clock_period}/2.0] [all_inputs]

# set_output_delay constraints for output ports

set_output_delay -clock ${clock_name} 0 [all_outputs]

# Make all signals limit their fanout

set_max_fanout 20 $design_name

# Make all signals meet good slew

set_max_transition [expr 0.05*${clock_period}] $design_name

# steveri 05/2022
# Get rid of violation "Early External Delay Assertion" assoc. w/clk_in.
# Don't care if this clock passes through global controller too quickly.
# Also we don't use this clock anyway.

set_false_path -hold -from [ get_ports clk_in ] -to [ get_ports clk_out ]

