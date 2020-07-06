source /sim/kongty/tsmc16_setup.tcl
lappend search_path . ..

set power_enable_analysis true
set power_analysis_mode time_based

set sim_type "gate"
set activity_file /sim/kongty/garnet/global_buffer/glb_power.vcd
set parasitics_file /sim/kongty/mflowgen/build-glb/18-cadence-innovus-signoff/outputs/design.spef.gz
read_verilog /sim/kongty/mflowgen/build-glb/18-cadence-innovus-signoff/outputs/design.vcs.v

set dut "global_buffer"

set report_dir "./reports"

#########################################################
# Read in design                                        #
#########################################################
current_design global_buffer

set LINK_STATUS [link_design]

#########################################################
# Constraints                                           #
#########################################################
create_clock -name clk -period 1.0 [get_ports clk]

set_input_delay 0.0 -clock clk [all_inputs]
set_output_delay 0.0 -clock clk [all_outputs]
set_input_delay -min 0.0 -clock clk [all_inputs]
set_output_delay -min 0.0 -clock clk [all_outputs]

read_parasitics $parasitics_file

#########################################################
# Read VCD                                              #
#########################################################
while {[get_license {"PrimeTime-PX"}] == 0} {
  echo {Waiting for PrimeTime-PX license...}
  sh sleep 120
}
puts "LICENSE ACQUIRED"

set time_window [list [1005000] [2285000]]
switch [file extension $activity_file] {
    ".vcd"  {read_vcd -rtl $activity_file -strip_path $dut -time $time_window}
}

#########################################################
# Iterate over switching activity files to generate     #
# average or time based power reports per diag          #
#########################################################

report_switching_activity
report_switching_activity > "$report_dir/pre_switching_activity.rpt"

report_power
report_power > "$report_dir/power.rpt"

report_switching_activity > "$report_dir/post_switching_activity.rpt"

get_switching_activity -toggle_rate "*" > "$report_dir/switching.rpt"

report_power -nosplit -hierarchy -leaf > "$report_dir/hierarchy.rpt"

report_power -groups clock_network -nosplit -hierarchy -leaf > "$report_dir/clock_power.rpt"

exit
