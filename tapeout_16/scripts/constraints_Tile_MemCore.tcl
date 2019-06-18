create_clock -name clk -period 2.2 [get_ports clk*]
create_generated_clock -name clk_out -source [get_ports clk] -multiply_by 1 [get_ports clk_out]
set_input_delay 0.2 -clock clk [all_inputs]
set_output_delay 0.2 -clock clk [all_outputs]
set_input_delay -min 0 -clock clk [all_inputs]
set_output_delay -min 0 -clock clk [all_outputs]

set_input_transition 0.2 [all_inputs]

set_false_path -from [get_ports tile_id*] -to [all_outputs]
set config_file [open "../../../mem_synth.txt"]
set lines [split [read $config_file] "\n"]
# set false paths from config regs
foreach line $lines {
  set_false_path -through [get_pins -hier $line/O*] 
  echo "setting false path through config reg $line"
}

set_attribute ungroup_ok false [get_cells *]
set_attribute ungroup_ok true [get_cells -hier MemCore*]
