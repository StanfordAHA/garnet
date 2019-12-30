# :: means global namespace / avail inside proc def
source ../../scripts/sr_funcs.tcl

# env var VTO_GOLD is used by sr_read_db to find "gold" design database snapshots
sr_funcs_setenv_VTO_GOLD
puts "@file_info env var VTO_GOLD=$::env(VTO_GOLD)"


##############################################################################
# Use env var VTO_STAGES to figure out which stages are wanted
# To do all stages, unset env var VTO_STAGES and/or set to "all"
# To do e.g. just floorplan and eco, do 'export VTO_STAGES="floorplan eco"'
set vto_stage_list [sr_funcs_set_stages]
puts "@file_info: vto_stage_list='$vto_stage_list'"

# Or you can set it manually, e.g.
#   set vto_stage_list "all"
#   set vto_stage_list "plan eco"
#   set vto_stage_list 'floorplan place cts fillers route optDesign eco'


##############################################################################
# Where is results_syn? Which one should we use?
# If local results_syn exists, use it. Otherwise, link to a gold copy.
sr_funcs_find_or_create_results_syn
puts -nonewline "@file_info: "; ls -ltd results_syn


##############################################################################
# Execute desired stages
# 
# Should match e.g. "floorplan", "plan", "floorplanning", "planning"...
if {[lsearch $vto_stage_list "*plan*"] >= 0} {
  sr_info "Begin stage 'floorplan'"

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
  sr_info "Begin stage 'placement'"
  # FIXME is this good? is this fragile?
  # might be doing unnecessary read_db if e.g. we just now wrote it above
  sr_find_and_read_db powerplanned.db

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
  # - steveri 1912 omg what is this hack!!?? appears to be putting
  # - extra-large blockage areas around just two of the 42 icovl blocks
  # - but the area appears to be hard-wired and we've changed th icovl block    
  # - placement so who knows where they were supposed to be and why
  # - as of now the blockage appears around blocks 1,0 and 1,13 of the 2x21
  # - array of center icovl blocks, where LL block is (0,0)
  # - also note the blockage goes in *after* e.g. M1 stripes were built
  # - so hella drc errors where they now overlap :(
  # - i will file an issue
  # create_route_blockage -all {route cut} -rects {{2332 2684 2414 2733}{2331 3505 2414 3561}}       
  set_db [get_db insts ifid_icovl*] .route_halo_size 4
  set_db [get_db insts ifid_icovl*] .route_halo_bottom_layer M1
  set_db [get_db insts ifid_icovl*] .route_halo_top_layer AP


  # Huh looks like this got sourced twice (see above)
  source ../../scripts/timing_workaround.tcl

  # This is where seg fault happens if didn't reread floorplan db
  eval_legacy {source ../../scripts/place.tcl}

    # Weird corner_ur problem [sr 1912]
    if { [ get_db insts corner_ur] == "" } { 
        puts "@file_info ----------------------------------------------------------------"
        puts "@file_info CORNER_UR PROBLEMS"
        puts "@file_info OMG corner_ur is back like a zombie only this time it's on top of corner_ll"
        puts "@file_info See github issue #<TBD> for details"
        puts "@file_info"
        puts "@file_info     corner_ur.place_status: [ get_db inst:GarnetSOC_pad_frame/corner_ur .place_status ]"
        puts "@file_info     corner_ur.bbox: [ get_db inst:GarnetSOC_pad_frame/corner_ur .bbox ]"
        puts "@file_info     corner_ul.bbox: [ get_db inst:GarnetSOC_pad_frame/corner_ll .bbox ]"
        puts "@file_info"
        puts "@file_info Deleting corner_ur (again): 'delete_inst -inst corner_ur'"
        delete_inst -inst corner_ur*
        puts "@file_info ----------------------------------------------------------------"
    }

  sr_info "write_db placed.db"
  write_db placed.db -def -sdc -verilog

  sr_info "End stage 'placement'"
}

##############################################################################
if {[lsearch -exact $vto_stage_list "cts"] >= 0} {
    sr_info "Begin stage 'cts'"
    # FIXME is this good? is this fragile?
    # might be doing unnecessary read_db if e.g. we just now wrote it above
    sr_find_and_read_db placed.db

  # Run 23 started here ish I think

  # New/different in run 23? (Run 23 successfully completed optDesign)
  update_constraint_mode -name functional \
    -sdc_files results_syn/syn_out._default_constraint_mode_.sdc
  # Sometimes results_syn/ is a symlink to /sim/ajcars... (golden snapshot).
  # Does/did update_constraint_mode (above) modify it???
  # No: timestamp is still months ago.

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
  sr_info "write_db cts.db"
  write_db cts.db -def -sdc -verilog
}

##############################################################################
# Matches e.g. "fill", "filler", "fillers"
if {[lsearch $vto_stage_list "fill*"] >= 0} {
    sr_info "Begin stage 'fill'"
    sr_find_and_read_db cts.db

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
  sr_info "write_db filled.db"
  write_db filled.db -def -sdc -verilog
    sr_info "End stage 'fill'"
}

##############################################################################
if {[lsearch -exact $vto_stage_list "route"] >= 0} {
    sr_info "Begin stage 'route'"
    sr_find_and_read_db filled.db

    ##############################################################################
    # Route design
    # 
    # eval_legacy { source ../../scripts/route.tcl} # INLINED BELOW
    # INLINING route.tcl to elminate failing optDesign step

    # FIXME SHORT TERM HACK
    # ? What's the hack?? Don't need to source tool_settings? Or what??
    eval_legacy { source ../../scripts/tool_settings.tcl }
    set_multi_cpu_usage -local_cpu 8

    # No need to route bumps to pad nets (routed during floorplan step)
    foreach_in_collection x [get_nets pad_*] {
        set cmd "setAttribute -net [get_property $x full_name] -skip_routing true"
        puts $cmd; 
        eval_legacy $cmd
    }
    ##### Route Design
    # [sr 1912] Looks like it's going through at least 75 rounds of opt
    #   At the end there are still 33 violations.
    #   First twenty iterations suffice to go from 1056 down to 50 violations
    #   {1,5,10,15,20} iterations => {1056,71,62,50,50} violations
    #   May as well limit iterations to twenty.
    #   I guess ECO is supposed to cleanup the remaining violations
    #   Takes about two hours to do 75 iterations. What happens if we limit to 20?
    #   setNanoRouteMode -drouteEndIteration 20
    sr_info "routeDesign"
    eval_legacy {
        setNanoRouteMode -drouteEndIteration 20
        routeDesign
        # FIXME [sr1912] What is this (below) and why is it here? Isn't it too late?
        setAnalysisMode -aocv true
    }

    # write_db init_route.enc.dat
    sr_info "saveDesign init_route.enc"
    eval_legacy { saveDesign init_route.enc -def -tcon -verilog }

    sr_info "route.tcl DONE"
    sr_info "End stage 'route'"
}

##############################################################################
# Do optDesign separately because it's so problematical...
# 
# Matches e.g. "opt", "optDesign", "optdesign"
if {[lsearch $vto_stage_list "opt*"] >= 0} {
    sr_info "Begin stage 'optdesign'"
    sr_find_and_read_db init_route.enc.dat


    eval_legacy {
      # OMG really? Scoping?
      proc sr_info { msg } {
        set time [ clock format [ clock seconds ] -format "%H:%M" ]
        puts "@file_info $time $msg"
      } 
          # sr_info "optDesign -postRoute -hold -setup"
          # optDesign -postRoute -hold -setup

          # check_signal_drc true  AND no -noEcoRoute: sticks in addfiller for DAYS
          # check_signal_drc false AND    -noEcoRoute: finishes in 7-8 hours
          # check_signal_drc false AND no -noEcoRoute: still going after 15 hours
          # check_signal_drc true  AND    -noEcoRoute: not tried

          ### set filler mode(s)
          # Before/orig:
          #   -diffCellViol false        
          #   -add_fillers_with_drc false
          #   -check_signal_drc true     
          #   -ecoMode false             
          #   ...
          # 
          # Now:
          getFillerMode
          setFillerMode \
              -diffCellViol false \
              -add_fillers_with_drc false \
              -check_signal_drc false \
              -ecoMode false
          getFillerMode


          ### set design mode(s)
          # eval_legacy { setDesignMode -flowEffort express } # Can't do postroute in express mode
          # Pretty sure this doesn't change anything, i.e. was standard already
          getDesignMode
          setDesignMode -flowEffort standard
          getDesignMode

          ### set opt mode(s)
          setOptMode -verbose true
          getOptMode

          # Check the clock (not really necessary but whatevs)
          report_clocks
          # redirect pre-optdesign.clocks {report_clocks}

          # cold feet on this one (didn't ever do it)
          # generateRCFactor -postroute low

          # With    -noEcoRoute: 7 hours ish
          # Without -noEcoRoute: 15 hours+ - 4pm->7am and still running

          sr_info "optDesign -postRoute -hold -setup -noEcoRoute"
          optDesign -postRoute -hold -setup -noEcoRoute
      }
      sr_info "write_db routed.db"
      write_db routed.db -def -sdc -verilog

    sr_info "optdesign DONE"
}

##############################################################################
if {[lsearch -exact $vto_stage_list "eco"] >= 0} {
    sr_info "Begin stage 'eco'"

    # Read db from prev stage; b/c optdesign is optional, this gets a little complicated...
    ################################################################
    # Life was simpler when optDesign wasn't optional...
    # sr_find_and_read_db routed.db
    #
    # Now, follow a search path; use first one found:
    #    ./routed.db
    #    ./init_route.enc.dat
    # gold/routed.db
    # gold/init_route.enc.dat
    # 
    # Best case: we ran a successful optdesign locally and produced a local "routed.db"
    # Second best: we ran route locally but not optdesign, start from "init_route"; etc
    if {             ! [ sr_read_db_local routed.db          ] } {
        if {         ! [ sr_read_db_local init_route.enc.dat ] } {
            if {     ! [ sr_read_db_gold  routed.db          ] } {
                if { ! [ sr_read_db_gold  init_route.enc.dat ] } {
                    sr_info "ERROR could not find proper database"
                }
            }
        }
    }
    ################################################################

    # ecoRoute
    eval_legacy { source ../../scripts/eco.tcl}
    sr_info "write_db eco.db"
    write_db eco.db -def -sdc -verilog

    sr_info "eco done"

    # Fix pad ring?
    sr_info "Fix pad ring?"
    source ../../scripts/chip_finishing.tcl

    sr_info "write_db final.db"
    write_db final.db -def -sdc -verilog

    #HACK: Last minute fix for Sung-Jin's block
    sr_info "HACK: Last minute fix for Sung-Jin's block"
    deselect_obj -all
    select_vias  -cut_layer VIA8 -area 1600 3850 1730 4900
    delete_selected_from_floorplan

    # From old TOP.sh wrapper
    sr_info "clock report => pnr.clocks"
    redirect pnr.clocks {report_clocks}

    # "save_netlist" builds pnr.final.gls.v, pnr.final.lvs.v maybe
    sr_info "source save_netlist.tcl (builds pnr.final.{gls,lvs}.v maybe)"
    eval_legacy { source ../../scripts/save_netlist.tcl}

    # Huh. Apparently, stream_out needs TAPEOUT var etc
    # Originally I guess it came from files like Alex's .cshrc
    #    setenv TAPEOUT
    #    "/sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/"
    #
    # set gds_files [list \
    #   $::env(TAPEOUT)/synth/Tile_PE/pnr.gds \
    #   $::env(TAPEOUT)/synth/Tile_MemCore/pnr.gds \
    # set env(TAPEOUT) to ..
    if { ! [info exists env(TAPEOUT)] } {
        set ::env(TAPEOUT) ".."
    }

    # "stream_out" builds "final_final.gds" I think
    sr_info "source stream_out.tcl (builds final_final.gds I think)"
    eval_legacy { source ../../scripts/stream_out.tcl}
}
sr_info "DONE!"

exit





# OLD
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
    # eval_legacy {
    #     sr_info "source scripts/save_netlist.tcl"
    #     source ../../scripts/save_netlist.tcl
    # }
    # write_db final_final.db/
    # write_db final_updated_netlist.db
    # echo "redirect pnr.clocks {report_clocks}" >> $wrapper
    # echo "exit" >> $wrapper
