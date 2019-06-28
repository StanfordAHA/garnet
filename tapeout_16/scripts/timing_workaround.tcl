#
set_multi_cpu_usage -local_cpu 8
set_interactive_constraint_mode [all_constraint_modes]
foreach_in_collection p [all_inputs] {
  set_annotated_delay 0.1 -from $p -net
}

foreach_in_collection p [all_outputs] {
  set_annotated_delay 0.1 -to $p -net
}

set_load 2 [all_outputs]

set_multicycle_path -setup 20 -through [get_pins core_cgra_subsystem/Interconnect_inst0_Tile*/read_config_*]
set_false_path -hold -through [get_pins core_cgra_subsystem/Interconnect_inst0_Tile*/read_config_*]

set_false_path -through core_cgra_subsystem/Interconnect_inst0_Tile*/config_out*
set_false_path -through core_cgra_subsystem/Interconnect_inst0_Tile*/reset_out*
set_false_path -through core_cgra_subsystem/Interconnect_inst0_Tile*/stall_out*

set_clock_uncertainty -hold 0.05 -from cgra_clock -to cgra_clock
set_clock_uncertainty -hold 0.05 -from master_clock -to master_clock
set_clock_uncertainty -hold 0.05 -from tlx_fwd_clock -to tlx_fwd_clock
set_clock_uncertainty -hold 0.05 -from tlx_rev_clock -to tlx_rev_clock
set_clock_uncertainty -hold 0.05 -from trace_clock -to trace_clock

set_timing_derate -clock -early 0.97 -delay_corner ss_0p72_m40c_dc
set_timing_derate -clock -late 1.03  -delay_corner ss_0p72_m40c_dc
set_timing_derate -data -late 1.05  -delay_corner ss_0p72_m40c_dc
set_timing_derate -clock -early 0.97  -delay_corner ss_0p72_125c_dc
set_timing_derate -clock -late 1.03  -delay_corner ss_0p72_125c_dc
set_timing_derate -data -late 1.05  -delay_corner ss_0p72_125c_dc
set_timing_derate -clock -early 0.97  -delay_corner ff_0p88_0c_dc
set_timing_derate -clock -late 1.03  -delay_corner ff_0p88_0c_dc
set_timing_derate -data -late 1.05   -delay_corner ff_0p88_0c_dc
set_interactive_constraint_mode {}

eval_legacy {remove_assigns -net * -report}
set_dont_use true [get_lib_cells {*/E* */G* */*D16* */*D20* */*D24* */*D28* */*D32* */SDF* */*DFM* */*SEDF*}]
