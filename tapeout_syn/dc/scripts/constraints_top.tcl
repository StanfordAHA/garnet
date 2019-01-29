create_clock -name clk -period 2 -waveform {0 2} [get_ports pad_clk_in]
create_clock -name tck -period 20 -waveform {0 25} [get_ports pad_tck]
set_input_delay 0.2 -clock clk [get_ports -filter "name!~t* && name!~clk_in"]
set_input_delay 10 -clock tck [get_ports -filter "name=~pad_t* && name!~clk_in && name!~pad_tck && direction==in"]
set_output_delay 0.2 -clock clk [all_outputs]
set_load 0.1 [all_outputs]
set_input_transition 0.2 [all_inputs]
set_multicycle_path -setup 2 -from */read_data[0] -to global_controller/config_data_jtag_in_reg*
set_multicycle_path -hold 1 -from */read_data[0] -to global_controller/config_data_jtag_in_reg* 
set_max_fanout 1 [get_lib_pin -of [get_lib_cells -of /designs/top/instances_comb/tdo_IOPAD] -filter "name==C"]
set_false_path -from [get_clocks clk] -to [get_clock tck]
set_false_path -to [get_clocks clk] -from [get_clock tck]
set_multicycle_path -setup 3 -thr */gout_u
set_multicycle_path -hold 2 -thr */gout_u
set_multicycle_path -setup 3 -thr [get_pins -hier *IOPAD/I]
set_multicycle_path -hold 2 -thr [get_pins -hier *IOPAD/I]

puts "DONE CONSTRAINING"
