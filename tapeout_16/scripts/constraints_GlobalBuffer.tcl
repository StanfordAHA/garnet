create_clock -name clk -period 10 [get_ports clk*]
set_input_delay -max 0.2 -clock clk [all_inputs]
set_output_delay -max 0.2 -clock clk [all_outputs]
set_input_delay -min 0 -clock clk [all_inputs]
set_output_delay -min 0 -clock clk [all_outputs]
set_false_path -from [get_ports {*config* *reset*}] -to [all_outputs]
set_false_path -from [get_ports *stall*]

set config_regs [get_nets -hier {io_ctrl_start_addr* io_ctrl_num_words* io_ctrl_mode* io_ctrl_switch_sel* io_ctrl_done_delay* io_ctrl_done_gate* \
                                 cfg_ctrl_switch_sel* cfg_ctrl_start_addr* cfg_ctrl_num_words*}]
set_false_path -through $config_regs


set_input_transition 0.2 [all_inputs]
