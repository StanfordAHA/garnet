#Make sure that global signal pass throughs toggle after clk_out to avoid hold time problems
set global_signals [get_ports {config_out* reset_out* stall_out* read_config_data}]

# Add in the max input and output delays
set_max_delay -combinational_from_to -from [get_ports {config_config* config_read* config_write*}] -to [get_ports config_out*] 0.2
set_max_delay -combinational_from_to -from [get_ports stall] -to [get_ports stall_out*] 0.2
set_max_delay -combinational_from_to -from [get_ports reset] -to [get_ports reset_out*] 0.2

# constrain clk skew so we don't have differences between tile types
if {$::env(DESIGN) eq "Tile_PE"} {
  set_max_delay -combinational_from_to -from [get_ports clk] -to [get_ports clk_out] 0.15
  specifyNetWeight clk_out 15
} else {
  set_max_delay -combinational_from_to -from [get_ports clk] -to [get_ports clk_out] 0.2
  specifyNetWeight clk_out 1
}

foreach_in_collection signal $global_signals {
  echo "signal: [get_property $signal hierarchical_name]"
  set_data_check -clock clk -from [get_ports clk_out] -to $signal -hold 2.4
}
