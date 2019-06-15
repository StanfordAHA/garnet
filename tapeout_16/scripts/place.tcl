### Place Design
set_interactive_constraint_modes [all_constraint_modes]
set_multicycle_path -thr */C -setup 10
set_multicycle_path -thr */C -hold 9
#set_false_path -thr [get_cells -hier *GlobalController*]
set_false_path -thr [get_pins -hier *stall*]
set_multicycle_path -thr */PAD -setup 2
set_multicycle_path -thr */PAD -hold 1
set_dont_touch true [get_nets -of */PAD]
#set_multicycle_path -from [get_pins *_io_bit_reg/CP] -through [get_pins */C] -setup 10
#set_multicycle_path -from [get_pins *_io_bit_reg/CP] -through [get_pins */C] -hold 9
#set_multicycle_path -from [get_pins */clk_in] -setup 2
#set_multicycle_path -from [get_pins */clk_in] -hold 1

set_interactive_constraint_mode [all_constraint_modes]
set_timing_derate -clock -early 0.97 -delay_corner _default_delay_corner_ 
set_timing_derate -clock -late 1.03  -delay_corner _default_delay_corner_
set_timing_derate -data -late 1.05  -delay_corner _default_delay_corner_
set_interactive_constraint_mode {}

eval_novus {set_db [get_nets rte] .skip_routing true}
setMultiCpuUsage -localCpu 8
place_opt_design -place
place_opt_design -opt

setTieHiLoMode -maxDistance 20 -maxFanout 16
addTieHiLo -cell "TIEHBWP16P90 TIELBWP16P90"
