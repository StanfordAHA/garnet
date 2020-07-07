source ./tsmc16_setup.tcl
#lappend search_path . ..

set power_enable_analysis true
set power_analysis_mode time_based

set sim_type "gate"
set activity_file /sim/kongty/garnet/global_buffer/global_buffer_power.vcd
set parasitics_file {/sim/kongty/pnr_annotate/global_buffer.spef.gz /sim/kongty/pnr_annotate/glb_tile.spef.gz}
read_verilog {/sim/kongty/pnr_annotate/global_buffer.v /sim/kongty/pnr_annotate/glb_tile.v}

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

read_parasitics -format spef $parasitics_file

#########################################################
# Read VCD                                              #
#########################################################
#set time_window [list [1005000] [2285000]]
switch [file extension $activity_file] {
    ".vcd"  {read_vcd -rtl $activity_file -strip_path "top/dut" -time {1005 2285}}
}

#########################################################
# Iterate over switching activity files to generate     #
# average or time based power reports per diag          #
#########################################################

report_switching_activity
report_switching_activity > "$report_dir/pre_switching_activity.rpt"

update_power

report_power
report_power > "$report_dir/power.rpt"

report_switching_activity > "$report_dir/post_switching_activity.rpt"

get_switching_activity -toggle_rate "*" > "$report_dir/switching.rpt"

report_power -nosplit -hierarchy -leaf > "$report_dir/hierarchy.rpt"

report_power -groups clock_network -nosplit -hierarchy -leaf > "$report_dir/clock_power.rpt"

exit
