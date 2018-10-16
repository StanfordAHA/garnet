create_clock -name clk -period 2 -waveform {0 2.5} [get_ports clk*]
set_input_delay 0.2 -clock clk [all_inputs]
set_output_delay 0.2 -clock clk [all_outputs]
set_input_delay -min 0 -clock clk [all_inputs]
set_output_delay -min 0 -clock clk [all_outputs]

set_load 0.1 [all_outputs]
set_input_transition 0.2 [all_inputs]

set constant_regs [filter flop true [find / -instance instances_seq/config_*]] 
set_false_path -from [get_pins -of $constant_regs -filter "is_clock_pin==true"]
set_false_path -to [get_pins -of $constant_regs -filter "is_data_pin==true"]
set_false_path -through [get_pins sb*/* -filter "direction==out"] -through [get_pins cb_*/* -filter "direction==in"]
set_false_path -from [get_ports {config* tile_id* reset}] -to [all_outputs]
