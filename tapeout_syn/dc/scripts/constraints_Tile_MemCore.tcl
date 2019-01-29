create_clock -name clk -period 5 -waveform {0 2.5} [get_ports clk]
set_input_delay 0.2 -clock clk [all_inputs]
set_output_delay 0.2 -clock clk [all_outputs]
set_input_delay -min 0 -clock clk [all_inputs]
set_output_delay -min 0 -clock clk [all_outputs]

set_load 0.1 [all_outputs]
set_input_transition 0.2 [all_inputs]

set_false_path -through [get_pins SB*/* -filter "direction==out"] -through [get_pins CB_*/* -filter "direction==in"]
set_false_path -from [get_ports {config* tile_id* reset}] -to [all_outputs]
