create_clock -name clk -period 2.2 [get_ports clk*]
set_input_delay 0.2 -clock clk [all_inputs]
set_output_delay 0.2 -clock clk [all_outputs]
set_input_delay -min 0 -clock clk [all_inputs]
set_output_delay -min 0 -clock clk [all_outputs]

set_input_transition 0.2 [all_inputs]

set_false_path -setup -from [get_ports {config* tile_id* reset}] -to [all_outputs]
set config_file [open "/sim/ajcars/garnet/mem_synth.txt"]
set lines [split [read $config_file] "\n"]
# set false paths from config regs
foreach line $lines {
  set_false_path -through [get_pins -hier $line/O*] 
  echo "setting false path through config reg $line"
}

set_attribute ungroup_ok false [get_cells *]
set_attribute ungroup_ok true [get_cells -hier MemCore*]
