# Flowkit v0.2
################################################################################
# This file contains 'create_flow_step' content for steps which are required
# in an implementation flow, but whose contents are specific.  Reivew  all
# <PLACEHOLDER> content and replace with commands and options more appropiate
# for the design being implemented. Any new flowstep definitions should be done
# using the 'flow_config.tcl' file.
################################################################################

##############################################################################
# STEP init_design
##############################################################################
create_flow_step -name init_design -owner cadence {
  if {[get_db current_design] eq ""} {
    # print configuration
    puts " CRAFT run = [get_db flow_run_tag]"
    puts " CRAFT toplevel = [get_db core]"

    # setup
    read_mmmc [get_db flow_source_directory]/mmmc_config.tcl
    read_physical -lef  "[glob [get_db tech]/lef/*]"
    puts " CRAFT reading RTL"
    read_hdl [get_db rtl]

    # elaborate the design
    elaborate [get_db core]

    # initialize library and design information
    init_design -top [get_db core]

    # optionally setup power intent from UPF/CPF/1801
    foreach power_file [get_db power_files] {
      read_power_intent $power_file -cpf
    }

    # add cells and commint power rules
    commit_power_intent
  }
}

##############################################################################
# STEP init_floorplan
##############################################################################
create_flow_step -name init_floorplan -skip_db -owner cadence {
  # save db
  write_db prefp.enc

  # create floorplan
  create_floorplan  -core_density_size 1

  # optionally setup power intent from UPF/CPF/1801
  foreach power_file [get_db power_files] {
    read_power_intent $power_file -cpf
  }

  # add cells and commint power rules
  commit_power_intent

  # read manually dumped floorplan if it exists, otherwise create it
  # [stevo]: gen_floorplan steps take 22 minutes right now, not a big deal
  if {[file exists [get_db flow_source_directory]/[get_db core].fp]} {
    read_floorplan [get_db flow_source_directory]/[get_db core].fp
  } else {
    # just adds a bunch of procedures
    source [get_db flow_source_directory]/gen_floorplan.tcl

    # call each procedure
    # reads IO file which creates bumps, too
    gen_fp

    # clock receiver routing
    read_def [get_db flow_source_directory]/clkrx.def -special_nets
    #read_def [get_db flow_source_directory]/rdl.def -special_nets

    # bump stuff
    #source [get_db flow_source_directory]/read_bump_csv.tcl
    #select_bumps -net {VDD VSS}
    #unassign_bumps -selected
    #gen_route_bumps

    # other stuff
    source [get_db flow_source_directory]/place_srams.tcl
    gen_routing_rules 
    add_core_clamps
    add_core_fiducials
    done_fp
    # [stevo]: boundary fiducials added inside gen_power
    gen_power
    delete_route_halo -all_blocks
    delete_route_blockages -name RAILBLOCK
  }

  # don't do the routing with these things
  foreach bbox [get_db [get_db insts -if {.name == ifid_icovl_* || .name == ifid_dtcd_feol_*}] .bbox] {
    set margin 4
    set lx [expr [lindex $bbox 0]-$margin]
    set ly [expr [lindex $bbox 1]-$margin]
    set ux [expr [lindex $bbox 2]+$margin]
    set uy [expr [lindex $bbox 3]+$margin]
    create_route_blockage -except_pg_net -area $lx $ly $ux $uy -layers M0 M1 M2 M3 M4 M5 M6 M7 -name SIGNALBLOCK
  }
  set bbox [lindex [get_db [get_db insts *clkrx*] .bbox] 0]
  set margin 2
  set lx [expr [lindex $bbox 0]-$margin]
  set ly [expr [lindex $bbox 1]-$margin]
  set ux [expr [lindex $bbox 2]+$margin]
  set uy [expr [lindex $bbox 3]+$margin]
  create_route_blockage -except_pg_net -area $lx $ly $ux $uy -layers M0 M1 M2 M3 M4 M5 M6 M7 -name SIGNALBLOCK

  # [stevo]: do we need this?
  #check_drc
  #fix_via -min_step
  #fix_via -min_cut
}


##############################################################################
# STEP power_vias
##############################################################################
create_flow_step -name power_vias -skip_db -owner CRAFT {

  # [stevo]: drops vias between M1 and M2 standard cell rails
  # WORK IN PROGRESS
  # this seems to work, but probably takes forever
  set_db add_stripes_stacked_via_bottom_layer M1
  set_db add_stripes_stacked_via_top_layer M2
  set_db generate_special_via_respect_stdcell_geometry false
  set_db generate_special_via_check_signal_routes 0
  set_db generate_special_via_enable_check_drc false
  # [stevo]: do it all in innovus with these commands, but you might graduate before it finishes:
  #set_db generate_special_via_respect_stdcell_geometry true
  #set_db generate_special_via_check_signal_routes 2
  #set_db generate_special_via_enable_check_drc true
  set_db generate_special_via_rule_preference VIAGEN12

  # [stevo]: step 1) run once with full width vias
  # takes 10-15 minutes
  update_power_vias -top_layer M2 -bottom_layer M1 -add_vias 1 -orthogonal_only 0
  check_drc -layer_range {M1 M2} -limit 1000000

  # [stevo]: step 2) delete violations, though it deletes entire rows
  # takes just a few minutes
  write_drc_markers drc.txt -force
  set drc [pwd]/drc.txt
  set py [get_db flow_source_directory]/del_vias.py
  exec python $py $drc
  edit_set_route -drc_on 0
  source del_vias.tcl
  edit_set_route -drc_on 1

  # [stevo]: step 3) add smaller vias to empty rows
  # takes almost 3 hours
  update_power_vias -top_layer M2 -bottom_layer M1 -add_vias 1 -orthogonal_only 0 -split_long_via {2 0.116 -1}
  check_drc -layer_range {M1 M2} -limit 1000000

  # [stevo]: step 4) delete violations, this step deletes individual vias
  # takes just a few minutes
  write_drc_markers drc.txt -force
  set drc [pwd]/drc.txt
  set py [get_db flow_source_directory]/del_vias.py
  exec python $py $drc
  edit_set_route -drc_on 0
  source del_vias.tcl
  edit_set_route -drc_on 1

}


create_flow_step -name set_dont_use -skip_db -owner CRAFT {
  # don't use super wide cells
  # height = 0.576
  # M3 inside-to-inside = 4.092
  set_dont_use [get_db lib_cells -if { .area >= 2.356992 }]

  # [stevo]: don't use these library cells because pins are too close
  set_dont_use [get_db lib_cells *OAI221D0BWP16P90]
  set_dont_use [get_db lib_cells *OAI221D1BWP16P90]
  set_dont_use [get_db lib_cells *OAI221D0BWP16P90LVT]
  set_dont_use [get_db lib_cells *OAI221D1BWP16P90LVT]
  set_dont_use [get_db lib_cells *OAI221D0BWP16P90ULVT]
  set_dont_use [get_db lib_cells *OAI221D1BWP16P90ULVT]
  set_dont_use [get_db lib_cells *AOI221D0BWP16P90]
  set_dont_use [get_db lib_cells *AOI221D1BWP16P90]
  set_dont_use [get_db lib_cells *AOI221D0BWP16P90LVT]
  set_dont_use [get_db lib_cells *AOI221D1BWP16P90LVT]
  set_dont_use [get_db lib_cells *AOI221D0BWP16P90ULVT]
  set_dont_use [get_db lib_cells *AOI221D1BWP16P90ULVT]

  set_dont_use [get_db lib_cells *AOI22D0BWP16P90    ]
  set_dont_use [get_db lib_cells *AOI22D0BWP16P90ULVT]
  set_dont_use [get_db lib_cells *AOI22D0BWP16P90LVT ]
  set_dont_use [get_db lib_cells *AO22D0BWP16P90     ]
  set_dont_use [get_db lib_cells *AO22D1BWP16P90     ]
  set_dont_use [get_db lib_cells *AO22D2BWP16P90     ]
  set_dont_use [get_db lib_cells *AO22D1BWP16P90ULVT ]
  set_dont_use [get_db lib_cells *AO22D0BWP16P90LVT  ]
  set_dont_use [get_db lib_cells *OAI22D0BWP16P90    ]
  set_dont_use [get_db lib_cells *OAI22D0BWP16P90LVT ]
  set_dont_use [get_db lib_cells *OAI22D0BWP16P90ULVT]
  set_dont_use [get_db lib_cells *OAI221D2BWP16P90   ]
  set_dont_use [get_db lib_cells *ND4D0BWP16P90      ]
  set_dont_use [get_db lib_cells *IND4D0BWP16P90     ]
  set_dont_use [get_db lib_cells *OA22D0BWP16P90     ]
  set_dont_use [get_db lib_cells *OA22D1BWP16P90     ]
  set_dont_use [get_db lib_cells *OA22D2BWP16P90     ]
}

create_flow_step -name set_dont_touch -skip_db -owner CRAFT {
  set_db [get_db [get_db [get_db insts *clkrx] .pins -if {.direction == "in"}] .net] .preserve true
}


#########################################################
## streamout gds
#########################################################
create_flow_step -name stream_out -skip_db -owner CRAFT {
  puts "CRAFT-404 adding sealring"

  delete_inst -inst sealring*
  create_inst -cell  N16_SR_B_1KX1K_DPO_DOD_5_x_5 -inst sealring -physical

  # Place the sealring to center the IO pads
  set core_fp_width 4900
  set core_fp_height 4900
  set sr_center_x [expr 5001.6 / 2.0]
  set sr_center_y [expr 5001.6 / 2.0]
  set core_center_x [expr $core_fp_width / 2.0]
  set core_center_y $core_center_x
  set sr_offset_x [expr $core_center_x - $sr_center_x + 0.016]
  set sr_offset_y [expr $core_center_y - $sr_center_y + 0.016]
  # Seal Ring place holder
  place_inst sealring $sr_offset_x $sr_offset_y -fixed

  #if {[get_db flow_report_name] == "postroute"} {
  #  #read_def -special_nets [get_db flow_source_directory]/rdl.def
  #  #source [get_db flow_source_directory]/read_bump_csv.tcl
  #}

  puts "CRAFT-404 exporting gds"

  set out_dir [file join [get_db flow_database_directory] [get_db flow_report_name]]
  if {![file exists $out_dir]} {
    file mkdir $out_dir
  }

  # [stevo]: design GDS merged with all others
  # some of this copied from last tapeout
  # don't merge; do that in Calibre
  write_stream [file join $out_dir [get_db core].merge.gds] \
    -map_file [get_db TSMC_gds_map] \
    -unit 1000 \
    -attach_inst_name 12 \
    -attach_net_name 15 \
    -mode ALL \
    -output_macros

    #-merge [get_db gds_files] \
    #-map_file "/tools/projects/stevo/craft/fft2-chip/vlsi/flow/scripts/gds.map" \
  
  # [stevo]: delete sealring
  delete_inst -inst sealring*

  # [stevo]: make sure we do this thing
  write_db [file join $out_dir [get_db core].enc]
}


#########################################################
## pulse width fix
#########################################################
create_flow_step -name fix_pulse_width -skip_db -owner CRAFT {
  report_constraint -all_violators > setup.all_violators.broken
  set vio [pwd]/setup.all_violators.broken
  set py [get_db flow_source_directory]/upsize_drivers.py
  exec python $py $vio
  source upsize_drivers.tcl
  report_constraint -all_violators > setup.all_violators.fixed
}

#########################################################
## Fix DRC violations after postroute
#########################################################
create_flow_step -name postroute_drc_fix -skip_db -owner CRAFT {
  set_db route_design_with_eco 1
  set_db route_design_eco_only_in_layers 1:7
  set_db route_design_selected_net_only 0
  route_global_detail
}
