set search_path [list \
  /tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tphn16ffcllgv18e_110c/ \
  /tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/ \
  /tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90lvt_100a/ \
  /tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90ulvt_100a/ \
  /tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90pm_100a/ \
  /sim/kongty/
]                                                                                              
set link_path [list \
  * \
  tphn16ffcllgv18ett0p8v1p8v85c.db \
  tcbn16ffcllbwp16p90tt0p8v85c.db \
  tcbn16ffcllbwp16p90lvttt0p8v85c.db \
  tcbn16ffcllbwp16p90ulvttt0p8v85c.db \
  tcbn16ffcllbwp16p90pmtt0p8v85c.db \
  ts1n16ffcllsblvtc2048x64m8sw_130a_tt0p8v110c.db \
]

set power_enable_analysis true
set power_analysis_mode time_based

set sim_type "gate"
set activity_file /sim/kongty/garnet/global_buffer/global_buffer_power.vcd
set parasitics_file {/sim/kongty/pnr_annotate/global_buffer.spef.gz /sim/kongty/pnr_annotate/glb_tile.spef.gz}
read_verilog {/sim/kongty/pnr_annotate/global_buffer.lvs.v /sim/kongty/pnr_annotate/glb_tile.lvs.v}

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
    ".vcd"  {read_vcd -rtl $activity_file -strip_path "top/dut" -time {4165 5445}}
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
