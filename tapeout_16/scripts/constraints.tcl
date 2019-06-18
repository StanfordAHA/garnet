# Extra top level constraints
set_interactive_constraint_modes [all_constraint_modes]
set_multicycle_path -thr */C -setup 10
set_multicycle_path -thr */C -hold 9
set_multicycle_path -thr */PAD -setup 2
set_multicycle_path -thr */PAD -hold 1
#set_multicycle_path -setup 10 -through [get_pins -hier GlobalController_32_32_inst0/read_data_in*]
#set_multicycle_path -hold 0 -through [get_pins -hier GlobalController_32_32_inst0/read_data_in*]
set_false_path -through [get_pins -hier GlobalController_32_32_inst0/read_data_in*]
set_dont_touch true [get_nets -of */PAD]

set_interactive_constraint_mode [all_constraint_modes]
set_timing_derate -clock -early 0.97 -delay_corner _default_delay_corner_ 
set_timing_derate -clock -late 1.03  -delay_corner _default_delay_corner_
set_timing_derate -data -late 1.05  -delay_corner _default_delay_corner_
set_interactive_constraint_mode {}
