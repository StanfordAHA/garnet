# :: means global namespace / avail inside proc def
# set ::VTO_GOLD /sim/steveri/garnet/tapeout_16/synth/ref
set ::VTO_GOLD /sim/steveri/garnet/tapeout_16/synth/gpf0_gold

# set ::env(VTO_OPTDESIGN) 0
# # delete this after at least one successful run!
# if { $::env(VTO_OPTDESIGN) } {
#      puts "@file_info: VTO_OPTDESIGN=$::env(VTO_OPTDESIGN)"
# }
# puts "@file_info: VTO_OPTDESIGN=$::env(VTO_OPTDESIGN)"
if { [info exists ::env(VTO_OPTDESIGN)] } {
    puts "@file_info: VTO_OPTDESIGN=$::env(VTO_OPTDESIGN)"
} else {
    puts "@file_info: No VTO_OPTDESIGN (yet)"
}


# Want a record of where the reference db files are coming from
if { ! [file isdirectory $::VTO_GOLD] } {
    puts "@file_info: No ref dir (daring aren't we)" 
} else {
    puts -nonewline "@file_info: "
    ls -l $::VTO_GOLD
}

##############################################################################
# Figure out which stages are wanted
# FIXME/TODO should be a task
# 
# Default: do all stages of the flow
# 
# Note: previously had best success with stages "route eco" only


if { ! [info exists env(VTO_STAGES)] } {
  set ::env(VTO_STAGES) "all"
}
set vto_stage_list [split $::env(VTO_STAGES) " "]
puts "@file_info: $vto_stage_list"

# To do all stages, unset env var VTO_STAGES and/or set to "all"
# To do e.g. just flowwplan and eco, do 'export VTO_STAGES="floorplan eco"'
if {[lsearch -exact $vto_stage_list "all"] >= 0} {
    set ::env(VTO_STAGES) "floorplan place cts fillers route eco"
    set vto_stage_list [split $::env(VTO_STAGES) " "]
    puts "@file_info: $vto_stage_list"
}

# Turn stages env variable into a useful list
puts "@file_info: VTO_STAGES='$::env(VTO_STAGES)'"
puts "@file_info: vto_stage_list='$vto_stage_list'"

##############################################################################

proc sr_read_db { db } {
    if { ! [file isdirectory $db] } { set db $::VTO_GOLD/$db }
    puts "@file_info: read_db $db"
    read_db $db
}

# proc sr_verify_syn_results {} {
#     # ERROR: (TCLCMD-989): cannot open SDC file
#     # 'results_syn/syn_out._default_constraint_mode_.sdc' for mode 'functional'
#     if { ! [file isdirectory results_syn] } {
#         # set db $::VTO_GOLD/$db
#         ln -s $::VTO_GOLD/results_syn
#     }
# }

# Apparently everyone needs this?
if { ! [file isdirectory results_syn] } {
    # ERROR: (TCLCMD-989): cannot open SDC file
    # 'results_syn/syn_out._default_constraint_mode_.sdc' for mode 'functional'
    # set db $::VTO_GOLD/$db
    ln -s $::VTO_GOLD/results_syn
    ls -l results_syn/*.sdc
}


##############################################################################
# Execute desired stages
# 
# Should match e.g. "floorplan", "plan", "floorplanning", "planning"...
if {[lsearch $vto_stage_list "*plan*"] >= 0} {
  puts "@file_info: floorplan"

  source ../../scripts/init_design_multi_vt.tcl
  source ../../scripts/floorplan.tcl

  # floorplan.tcl ends with this write_db command:
  # write_db powerplanned.db

  # Must read database just written by floorplan.tcl, else seg faults.
  # FIXME figure out why this is necessary and fix it!
  # Note the floorplan takes about eleven hours to complete so expect
  # a very long turnaround time when/if you decide to work on it.
  # Also see (closed) issue 349 https://github.com/StanfordAHA/garnet/issues/349

  # set db powerplanned.db
  # We now do this naturally as port of the next stage (placement)
}

##############################################################################
if {[lsearch -exact $vto_stage_list "place"] >= 0} {
  puts "@file_info: placement"
  # FIXME is this good? is this fragile?
  # might be doing unnecessary read_db if e.g. we just now wrote it above
  sr_read_db powerplanned.db

  # Okay so this is all part of placement why not
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
  puts "@file_info: write_db placed.db"
  write_db placed.db -def -sdc -verilog
}

##############################################################################
if {[lsearch -exact $vto_stage_list "cts"] >= 0} {
    puts "@file_info: cts"
    # FIXME is this good? is this fragile?
    # might be doing unnecessary read_db if e.g. we just now wrote it above
    sr_read_db placed.db

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
  # Unskipping b/c Mark said "NO NO NO!"
  # Clock tree
  eval_legacy { source ../../scripts/cts.tcl}
  puts "@file_info: write_db cts.db"
  write_db cts.db -def -sdc -verilog
}

##############################################################################
# Matches e.g. "fill", "filler", "fillers"
if {[lsearch $vto_stage_list "fill*"] >= 0} {
    puts "@file_info: fill"
    sr_read_db cts.db

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
  puts "@file_info: write_db filled.db"
  write_db filled.db -def -sdc -verilog
}

##############################################################################
if {[lsearch -exact $vto_stage_list "route"] >= 0} {
    puts "@file_info: route"
    sr_read_db filled.db

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
      puts "@file_info: routeDesign"
      routeDesign
      setAnalysisMode -aocv true
      puts "@file_info: saveDesign init_route.enc"
      saveDesign init_route.enc -def -tcon -verilog

      if { ! [info exists ::env(VTO_OPTDESIGN)] } {
          puts "@file_info: No VTO_OPTDESIGN found"
          puts "@file_info: Will default to 1 (do optDesign)"
          set ::env(VTO_OPTDESIGN) 1
      }
      puts "@file_info: VTO_OPTDESIGN=$::env(VTO_OPTDESIGN)"
      if { $::env(VTO_OPTDESIGN) } {
          puts "@file_info: optDesign"
          optDesign -postRoute -hold -setup
      }
      puts "@file_info: write_db routed.db"
      write_db routed.db -def -sdc -verilog

      puts "@file_info: route.tcl DONE"
    }
    ##############################################################################
}


##############################################################################
if {[lsearch -exact $vto_stage_list "eco"] >= 0} {
    puts "@file_info: eco"
    sr_read_db routed.db

    # ecoRoute YES(24)
    eval_legacy { source ../../scripts/eco.tcl}
    puts "@file_info: write_db eco.db"
    write_db eco.db -def -sdc -verilog

    puts "@file_info: eco done"

    # Fix pad ring? YES(24)
    source ../../scripts/chip_finishing.tcl
    puts "@file_info: write_db final.db"
    write_db final.db -def -sdc -verilog

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

    eval_legacy {
        puts "@file_info: source scripts/save_netlist.tcl"
        source ../../scripts/save_netlist.tcl
    }
    # write_db final_final.db/
    # write_db final_updated_netlist.db
    # echo "redirect pnr.clocks {report_clocks}" >> $wrapper
    # echo "exit" >> $wrapper

    # From old TOP.sh wrapper
    redirect pnr.clocks {report_clocks}
}

exit
