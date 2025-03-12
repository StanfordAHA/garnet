#=========================================================================
# Design Constraints File
#=========================================================================

set_units -time ps -capacitance pF

#=========================================================================
# General
#=========================================================================

# -- clock
set clock_net  clk
set clock_name ideal_clock
create_clock -name ${clock_name} \
             -period ${clock_period} \
             [get_ports ${clock_net}]

# -- load and drive
set_load -pin_load ${ADK_TYPICAL_ON_CHIP_LOAD} [all_outputs]
set_driving_cell -no_design_rule -lib_cell ${ADK_DRIVING_CELL} [all_inputs]

# -- fanout
set_max_fanout 20 ${design_name}

# -- transition
set_max_transition 50 ${design_name}

#=========================================================================
# Clock Constraints
#=========================================================================

set all_clock_setup_uncertainty  [expr 0.10 * ${clock_period}]
set all_clock_hold_uncertainty   [expr 0.10 * ${clock_period}]

set_clock_uncertainty -setup $all_clock_setup_uncertainty [get_clocks ${clock_name}]
set_clock_uncertainty -hold $all_clock_hold_uncertainty   [get_clocks ${clock_name}]


#=========================================================================
# Input/Output Delays
#=========================================================================

set_input_delay  [expr 0.50 * ${clock_period}] -clock ${clock_name} [remove_from_collection [all_inputs] [get_ports "${clock_net}"] ]
set_output_delay [expr 0.50 * ${clock_period}] -clock ${clock_name} [all_outputs]

set_input_delay [expr 0.80 * ${clock_period}] -clock ${clock_name} [get_ports "rstn"]

# Might need to redo these constraints to avoid setup violations between in/out
# set_input_delay [expr 0.40 * ${clock_period}] -clock ${clock_name} [get_ports "inputIn_dat* psumIn_dat* weightIn_dat*"]
# set_output_delay [expr 0.30 * ${clock_period}] -clock ${clock_name} [get_ports "inputOut_dat* psumOut_dat* weightOut_dat*"]

#set_min_delay $cycle10 -to [all_outputs]
# set_min_delay [expr 0.40 * ${clock_period}] -to [get_ports "inputOut_dat* psumOut_dat* weightOut_dat*"]
