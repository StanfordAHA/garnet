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

set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.8] [get_ports hi]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.8] [get_ports lo]

set_input_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [all_inputs]

set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [get_ports config_out*]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [get_ports read_config_data]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [get_ports SB*_OUT_*]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [get_ports clk_out]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [get_ports clk_pass_through_out]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [get_ports reset_out]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [get_ports stall_out]

# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

if $::env(PWR_AWARE) {
    source inputs/dc-dont-use-constraints.tcl
    source inputs/pe-constraints.tcl
    set_dont_touch [get_cells -hierarchical *u_mux_logic*]
} 
