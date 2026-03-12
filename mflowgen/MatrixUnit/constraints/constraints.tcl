#=========================================================================
# Design Constraints File
#=========================================================================

set_units -time ps -capacitance fF

#=========================================================================
# General
#=========================================================================

# -- clock
set clock_net  auto_clock_in_clock
set clock_name ideal_clock
create_clock -name ${clock_name} \
             -period ${clock_period} \
             [get_ports ${clock_net}]

create_clock -name ${clock_name}_virtual \
             -period ${clock_period}

# -- load and drive
set_load -pin_load ${ADK_TYPICAL_ON_CHIP_LOAD} [all_outputs]
set_driving_cell -no_design_rule -lib_cell ${ADK_DRIVING_CELL} [all_inputs]

# -- fanout
set_max_fanout 20 ${design_name}

# -- transition
set_max_transition 100 ${design_name}

#=========================================================================
# Clock Constraints
#=========================================================================

set all_clock_setup_uncertainty  [expr 0.050 * 1000]
set all_clock_hold_uncertainty   [expr 0.050 * 1000]

set_clock_uncertainty -setup $all_clock_setup_uncertainty [get_clocks ${clock_name}]
set_clock_uncertainty -hold $all_clock_hold_uncertainty   [get_clocks ${clock_name}]

set_clock_uncertainty -setup $all_clock_setup_uncertainty [get_clocks ${clock_name}_virtual]
set_clock_uncertainty -hold $all_clock_hold_uncertainty   [get_clocks ${clock_name}_virtual]

# Matches clock latency from previous runs (plus some more)
# TODO: Ask Kathleen about this -- should Zircon include this constraint?
# set all_clock_latency [expr -0.800 * 1000]
# set_clock_latency -source $all_clock_latency [get_clocks ${clock_name}]
set all_clock_latency 0
#=========================================================================
# Cycle Definition
#=========================================================================

set cycle80         [expr 0.80 * ${clock_period}]
set cycle70         [expr 0.70 * ${clock_period}]
set cycle60         [expr 0.60 * ${clock_period}]
set cycle50         [expr 0.50 * ${clock_period}]
set cycle40         [expr 0.40 * ${clock_period}]
set cycle25         [expr 0.25 * ${clock_period}]
set cycle20         [expr 0.20 * ${clock_period}]
set cycle10         [expr 0.10 * ${clock_period}]

#=========================================================================
# Input/Output Delays
#=========================================================================

set_input_delay  $cycle25 -clock ${clock_name}_virtual [remove_from_collection [all_inputs] [get_ports "${clock_net}"] ]
set_output_delay $cycle40 -clock ${clock_name}_virtual [all_outputs]

# set max delay on connections with VectorUnit
set_output_delay $cycle40 -clock ${clock_name}_virtual [remove_from_collection [get_ports *outputsFromSystolicArray*] *outputsFromSystolicArray*rdy]
set_input_delay  [expr $cycle40 + $all_clock_latency] -clock ${clock_name}_virtual [get_ports *outputsFromSystolicArray*rdy]

set_input_delay $cycle40 -clock ${clock_name}_virtual [get_ports "auto_clock_in_reset"]

set_input_delay  [expr $cycle25 + $all_clock_latency] -clock ${clock_name}_virtual [get_ports *axi_in*      -filter {port_direction == in}]
set_input_delay  [expr $cycle25 + $all_clock_latency] -clock ${clock_name}_virtual [get_ports *unified_out* -filter {port_direction == in}]
set_output_delay [expr $cycle25 + $all_clock_latency] -clock ${clock_name}_virtual [get_ports *axi_in*      -filter {port_direction == out}]
set_output_delay [expr $cycle25 + $all_clock_latency] -clock ${clock_name}_virtual [get_ports *unified_out* -filter {port_direction == out}]


#=========================================================================
# False / Multicycle Path / State
#=========================================================================
set_false_path -hold -through [get_property [get_pins -hierarchical */fwen]      full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */clkbyp]    full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */mcen]      full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */mc[0]]     full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */mc[1]]     full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */mc[2]]     full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wpulseen]  full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wpulse[0]] full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wpulse[1]] full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wa[0]]     full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wa[1]]     full_name]

#=========================================================================
# Don't touch
#=========================================================================
# TODO: Ask Kathleen about this -- should Zircon include this constraint?
# set_dont_touch [ get_cells io_buf* ]

# Don't touch the internal nets between Processing Elements
set_dont_touch [get_nets -hier *systolicArray/input_wires*] true
set_dont_touch [get_nets -hier *systolicArray/weight_wires*] true
set_dont_touch [get_nets -hier *systolicArray/psum_wires*] true
