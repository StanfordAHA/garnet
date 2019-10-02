# FIXME Instead of 0, should be something like if { start_from_fill_db }
if { 1 } {
  source ../../scripts/init_design_multi_vt.tcl
  # read_db ../gpf6_setDesignMode/filled.db
  read_db ../ref/filled.db
} else {
  source ../../scripts/init_design_multi_vt.tcl
  source ../../scripts/floorplan.tcl

  # Must read database just written by floorplan.tcl, else seg faults.
  # FIXME figure out why this is necessary and fix it!
  # Note the floorplan takes about eleven hours to complete so expect
  # a very long turnaround time when/if you decide to work on it.
  # Also see (closed) issue 349 https://github.com/StanfordAHA/garnet/issues/349
  read_db powerplanned.db

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

  foreach x [get_db insts *dtcd*] {
    set bbox [get_db $x .bbox]
    set bbox1 [lindex $bbox 0]
    set l0 [expr [lindex $bbox1 0] - 2.2] 
    set l1 [expr [lindex $bbox1 1] - 2.2] 
    set l2 [expr [lindex $bbox1 2] + 2.2] 
    set l3 [expr [lindex $bbox1 3] + 2.2] 
    if {$l0 < 10} continue;
    create_route_blockage -area [list $l0 $l1 $l2 $l3]  -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} 
  }

  #Fixes for ICOVL DRCs
  create_route_blockage -all {route cut} -rects {{2332 2684 2414 2733}{2331 3505 2414 3561}}       
  set_db [get_db insts ifid_icovl*] .route_halo_size 4
  set_db [get_db insts ifid_icovl*] .route_halo_bottom_layer M1
  set_db [get_db insts ifid_icovl*] .route_halo_top_layer AP


  source ../../scripts/timing_workaround.tcl

  # This is where seg fault happens if didn't reread floorplan db
  eval_legacy {source ../../scripts/place.tcl}
  write_db placed.db -def -sdc -verilog

  # Run 23 started here ish I think

  # New/different in run 23? (Run 23 successfully completed optDesign)
  update_constraint_mode -name functional -sdc_files results_syn/syn_out._default_constraint_mode_.sdc

  set_interactive_constraint_modes [all_constraint_modes]
  eval_legacy {setAnalysisMode -cppr both}
  set_false_path -hold -to [all_outputs]
  set_interactive_constraint_mode {}
  set_multi_cpu_usage -local_cpu 8

  source ../../scripts/timing_workaround.tcl

  # NOTE run 23 skpped this step. So I will too.
  # # Clock tree
  # eval_legacy { source ../../scripts/cts.tcl}
  # write_db cts.db -def -sdc -verilog

  # 9/11/2019 Nikhil says maybe try filling *before* routing
  # else must do DRC on each filler cell as it is added
  # therefore maybe the cause of strips taking so long
  # as outlined in issue 351
  # https://github.com/StanfordAHA/garnet/issues/351
  #
  # Note (successful (ish)) run 23 did fill *before* route (and got chastised)
  # 
  # Fill
  eval_legacy { source ../../scripts/fillers.tcl}
  write_db filled.db -def -sdc -verilog
}


##############################################################################
# Route design - this is where optDesign hangs forever

# eval_legacy { source ../../scripts/route.tcl} # INLINED BELOW
# INLINING route.tcl to elminate failing optDesign step
eval_legacy {
  source ../../scripts/tool_settings.tcl
  ##No need to route bump to pad nets (routed during fplan step)
  setMultiCpuUsage -localCpu 8
  foreach_in_collection x [get_nets pad_*] {set cmd "setAttribute -net [get_property $x full_name] -skip_routing true"; puts $cmd; eval_legacy $cmd}

  ##### Route Design
  routeDesign
  setAnalysisMode -aocv true
  saveDesign init_route.enc -def -tcon -verilog
  # optDesign -postRoute -hold -setup # Commented out b/c never finishes
  write_db routed.db -def -sdc -verilog
}
##############################################################################




# ecoRoute YES(24)
eval_legacy { source ../../scripts/eco.tcl}
write_db eco.db -def -sdc -verilog

# Fix pad ring? YES(24)
source ../../scripts/chip_finishing.tcl
write_db final_final.db -def -sdc -verilog

# This is the last thing 24 did before being halted in optDesign
# eval_legacy { source ../../scripts/stream_out.tcl}

# Go ahead and leave this in for now, I guess,
# although have not verified that it happened in final tapeout
#HACK: Last minute fix for Sung-Jin's block
deselect_obj -all
select_vias  -cut_layer VIA8 -area 1600 3850 1730 4900
delete_selected_from_floorplan

# eval_legacy { source ../../scripts/save_netlist.tcl}
# eval_legacy { source ../../scripts/stream_out.tcl}


# SR 09/2019
# This (below) was already done in "chip_finishing", above
# Errs if you do it twice
# But, uh, why is ESD and POC commented out???
# 
# # from final-tapeout run 27:
# create_net -name RTE_DIG
# foreach x [get_property [get_cells {*IOPAD*ext_clk_async* *IOPAD_bottom* *IOPAD_left* *IOPAD_right*}] full_name] {
#   #connect_global_net ESD_0 -netlist_override -pin ESD -inst $x
#   #connect_global_net POC_0 -pin POCCTRL -inst $x
#   connect_pin -net RTE_DIG -pin RTE -inst $x
# }



eval_legacy {source ../../scripts/save_netlist.tcl }
# write_db final_final.db/
# write_db final_updated_netlist.db
# echo "redirect pnr.clocks {report_clocks}" >> $wrapper
# echo "exit" >> $wrapper

# From old TOP.sh wrapper
redirect pnr.clocks {report_clocks}
exit
