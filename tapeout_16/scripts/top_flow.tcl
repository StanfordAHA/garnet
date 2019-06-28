source ../../scripts/floorplan.tcl
update_constraint_mode -name functional -sdc_files results_syn/syn_out._default_constraint_mode_.sdc
source ../../scripts/timing_workaround.tcl
set_db [get_db nets ext_*] .skip_routing true
set_db [get_db nets ext_rstb] .skip_routing false
set_db [get_db nets ext_dump_start] .skip_routing false
set_db [get_db nets rte] .skip_routing true
set_db [get_db nets rte_3] .skip_routing true
#Disconnect iphy pins that go straight to bumps
set iphy_pins [get_pins {iphy/ext_rx_in* iphy/clk_out* iphy/clk_trig*}]
foreach_in_collection pin $iphy_pins {
  disconnect_pin -inst iphy -pin [get_property $pin name]
}
foreach x [get_db insts *icovl*] {
  set bbox [get_db $x .bbox]
  set bbox1 [lindex $bbox 0]
  set l0 [expr [lindex $bbox1 0] - 2.2] 
  set l1 [expr [lindex $bbox1 1] - 2.2] 
  set l2 [expr [lindex $bbox1 2] + 2.2] 
  set l3 [expr [lindex $bbox1 3] + 2.2] 
  if {$l0 < 10} continue;
  create_route_blockage -area [list $l0 $l1 $l2 $l3]  -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} 
}
eval_legacy {source ../../scripts/place.tcl}
write_db placed.db -def -sdc -verilog
set_interactive_constraint_modes [all_constraint_modes]
eval_legacy {setAnalysisMode -cppr both}
set_false_path -hold -to [all_outputs]
set_interactive_constraint_mode {}
eval_legacy { source ../../scripts/cts.tcl}
write_db cts.db -def -sdc -verilog
eval_legacy { source ../../scripts/route.tcl}
write_db routed.db -def -sdc -verilog
eval_legacy { source ../../scripts/eco.tcl}
write_db eco.db -def -sdc -verilog
source ..//scripts/chip_finishing.tcl
write_db final.db -def -sdc -verilog

#HACK: Last minute fix for Sung-Jin's block
deselect_obj -all
select_vias  -cut_layer VIA8 -area 1600 3850 1730 4900
delete_selected_from_floorplan

eval_legacy { source ../scripts/stream_out.tcl}
