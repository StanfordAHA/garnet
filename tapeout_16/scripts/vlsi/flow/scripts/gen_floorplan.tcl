set ::USE_ALTERNATIVE_M1_STRIPE_GENERATION 0
source ../../scripts/vlsi/flow/scripts/alt_add_M1_stripes.tcl

###################################
## a collection of floorplan procedures
## mostly written by Brian Richards
## modified heavily by Stevo Bailey
###################################

source ../../scripts/helper_funcs.tcl

proc gen_fp {} {

    create_floorplan -core_margins_by die -die_size_by_io_height max -site core -die_size 4900.0 4900.0 100 100 100 100

    if {[file exists [get_db flow_source_directory]/custom.io]} {
	    read_io_file [get_db flow_source_directory]/custom.io -no_die_size_adjust
    } else {
      read_io_file [get_db io_file] -no_die_size_adjust
    }

    place_inst FFT2Core/FFT2CoreTop/clkrx 302.861 2782.2 r0 -fixed
    #create_place_halo -insts FFT2Core/FFT2CoreTop/clkrx -halo_deltas {2 2 2 2} -snap_to_site
    create_place_halo -insts FFT2Core/FFT2CoreTop/clkrx -halo_deltas {15 15 15 15} -snap_to_site
    #create_route_halo -bottom_layer M0 -space 2 -top_layer M3 -inst FFT2Core/FFT2CoreTop/clkrx

    place_inst FFT2Core/FFT2CoreTop/amyADC/amyBlackBox [expr 4799.97-1387.233-156.623+17-7.516+3.42-0.718-0.028-56.7+89/2-32.5/2] 525 r0 -fixed
    create_place_halo -insts FFT2Core/FFT2CoreTop/amyADC/amyBlackBox -halo_deltas {2 2 2 2} -snap_to_site
    create_route_halo -bottom_layer M0 -space 2 -top_layer M3 -inst FFT2Core/FFT2CoreTop/amyADC/amyBlackBox

    place_inst FFT2Core/FFT2CoreTop/serdes/serdes_afe_dut [expr 1592.42-156.623+21+343.94-345.72-2.402] [expr 238.77-1.647] r0 -fixed
    create_place_halo -insts FFT2Core/FFT2CoreTop/serdes/serdes_afe_dut -halo_deltas {2 2 2 2} -snap_to_site
    create_route_halo -bottom_layer M0 -space 2 -top_layer M3 -inst FFT2Core/FFT2CoreTop/serdes/serdes_afe_dut

    place_inst FFT2Core/FFT2CoreTop/ffastMod/collectADCSamplesBlock/analogBlock/analogBlockAngieModel 1763.44 4375.529 r0 -fixed
    create_place_halo -insts FFT2Core/FFT2CoreTop/ffastMod/collectADCSamplesBlock/analogBlock/analogBlockAngieModel -halo_deltas {2 2 2 2} -snap_to_site
    create_route_halo -bottom_layer M0 -space 2 -top_layer M3 -inst FFT2Core/FFT2CoreTop/ffastMod/collectADCSamplesBlock/analogBlock/analogBlockAngieModel
}

proc done_fp {} {
    set ioFillerCells "PFILLER10080 PFILLER00048 PFILLER01008 PFILLER00001"

    
    # Snap the right and left IO drivers to the 0.048um fin grid
    snap_floorplan -io_pad 

    # [stevo]: delete upper right corner cell, because LOGO can't be close to metal
    delete_inst -inst corner_ur*

    # FIXME should we run globalNetCommand before add_io_fillers?
    #
    # From Innovus Text Command Reference manual, for "addIoFiller":
    # Note: Before using addIoFiller, run the globalNetCommand to provide
    # global-net-connection rules for supply pins of the added
    # fillers. Without these rules, the built-in design-rule checks of
    # addIoFiller will not be accurate.
    #
    # (The globalNetCommand note does not appear in the stylus version of the 
    # man page (add_io_fillers)

    # [stevo]: add -logic so fillers get RTE signal connection
    # add_io_fillers -cells "$ioFillerCells" -logic -derive_connectivity

    # [steveri 11/2019]: Dunno where "-derive_connectivity" comes from, but it
    # throws errors when used in conjunction w/Soong-jin's ANAIOPAD shenanigans
    add_io_fillers -cells "$ioFillerCells" -logic

    # [stevo]: connect corner cells to RTE
    # delete and recreate cell to set "is_physical" attribute to false (can't connect net to pin of physical-only cell)
    foreach inst [get_db insts pads/corner*] {
      set loc [get_db $inst .location]
      set ori [get_db $inst .orient]
      set name [get_db $inst .name]
      delete_inst -inst $name
      create_inst -inst $name -cell PCORNER  -status fixed -location [lindex $loc 0] -orient [string toupper $ori]
      connect_pin -net pads/rte -pin RTE -inst $name
    }
    set_db [get_db nets rte] .skip_routing true
    set_db [get_db nets rte] .dont_touch true
    set_db [get_db nets esd] .skip_routing true
    set_db [get_db nets esd] .dont_touch true

    snap_floorplan -all
    check_floorplan
}

proc gen_bumps {} {
    set core_fp_width 4900
    set core_fp_height 4900
    set bumpCell PAD85APB_LF_BU
    set io_root IOPAD
    set nb 26
    set bp 173.470; # 170 / 98%
    set bump_array_width [expr ($nb - 1) * $bp]
    set bofsW [expr ($core_fp_width - $bump_array_width) / 2.0]
    set bofsS [expr ($core_fp_height - $bump_array_width) / 2.0]
    set bofsE 0
    set bofsN 0
    delete_bumps -all
    create_bump -cell $bumpCell   \
    -edge_spacing "$bofsW $bofsS $bofsE $bofsN"   \
    -location_type cell_center   \
    -name_format "Bump_%i.%r.%c"   \
    -orient r0   \
    -pitch "$bp $bp"   \
    -location "$bofsW $bofsS"   \
    -pattern_array "$nb $nb"
    select_bumps -bumps "Bump_1.* Bump_3.* Bump_26.* Bump_651.* Bump_676.*"
    delete_bumps -selected
    # CRAFT 5mm x 5mm package.  Face-up View
    # UL: A26  UR: A1
    # LL: AF26 LR: AF1 Key pin: AF24
    # . -> Empty (5)
    # g -> VSS
    # o -> VIO
    # b -> VDD Core in periphery
    # 1 -> VDD1
    # 2 -> VDD2
    # 3 -> VDD3
    # 4 -> VDD4
    # 5 -> VDD5
    # 6 -> VDD6
    # r -> Core VDD (global)
    # d -> Diff pair
    # s -> Regular signal
    # FFT2Chip bumps with hard-IP bumps as X
    set bump_types {
	".bwxgosbsgssggssgsbsogssb."
	"bogyzsssssggssggsssssssgob"
	"ugossbgsssoobboosssgbssogs"
	"vssgssssgssssssssgssssgsss"
	"gsssgsssssbssssbsssssgsssg"
	"osbssrr111222222333rrssbso"
	"ssgssggggggggggggggggssgss"
	"bssss11111rr22rr33333ssssb"
	"sssgsggggggggggggggggsgsss"
	"gssssrr111222222333rrssssg"
	"sgosbggggggggggggggggbsogs"
	"sgoss11111rr22rr33333ssogs"
	"gsbssggggggggggggggggssbsg"
	"gsbssggggggggggggggggssbsg"
	"sgoss44444rr55rr66666ssogs"
	"sgosbggggggggggggggggbsogs"
	"gssssrr444555555666rrssssg"
	"sssgsggggggggggggggggsgsss"
	"bssss44444rr55rr66666ssssb"
	"ssgssggggggggggggggggssgss"
	"osbssrr444555555666rrssbso"
	"gsssgsssssbssssbsssssgsssg"
	"sssgssssgssssssssgssssgsss"
	"sgossbssssoobboosssgbssogs"
	"bogsssssssggssggsssssssgob"
	".b.sgosbsgssggssgsbsogssb."
    }

    deselect_bumps
#    select_bumps -bumps [bumps_of_type $bump_types "u"]
#    assign_signal_to_bump -selected -net RVSS 
#    deselect_bumps
#    select_bumps -bumps [bumps_of_type $bump_types "v"]
#    assign_signal_to_bump -selected -net RVDD 
#    deselect_bumps
#    select_bumps -bumps [bumps_of_type $bump_types "w"]
#    assign_signal_to_bump -selected -net AVSS 
#    deselect_bumps
#    select_bumps -bumps [bumps_of_type $bump_types "x"]
#    assign_signal_to_bump -selected -net AVSS1 
#    deselect_bumps
#    select_bumps -bumps [bumps_of_type $bump_types "y"]
#    assign_signal_to_bump -selected -net AVDD 
#    deselect_bumps
#    select_bumps -bumps [bumps_of_type $bump_types "z"]
#    assign_signal_to_bump -selected -net AVDD1 

    # Select all VSS bumps
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "g"]
    assign_signal_to_bump -selected -net VSS 

    # This is the original code. Looks like a VDD->VSS short to me!!!
    assign_bumps -multi_bumps_to_multi_pads -selected -pg_only \
        -pg_nets VSS -pg_insts ${io_root}*VDDPST_* \
        -exclude_region {1050 1050 3840 3840}

    assign_bumps -multi_bumps_to_multi_pads -selected -pg_only \
        -pg_nets VSS -pg_insts ${io_root}*VDD_* \
        -exclude_region {1050 1050 3840 3840}

    #assign_bumps -multi_bumps_to_multi_pads -selected -pg_only
    # -pg_nets VSS -pg_insts ${io_root}*VDDPSTANA_* -exclude_region {1050 1050 3840 3840}

    #assign_bumps -multi_bumps_to_multi_pads -selected
    # -pg_only -pg_nets VSS -pg_insts ${io_root}*VDDANA_*  -exclude_region {1050 1050 3840 3840}




    # Select all VDD bumps
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "o"]
    assign_signal_to_bump -selected -net VDDPST
    assign_bumps -multi_bumps_to_multi_pads -selected -pg_only -pg_nets VDDPST -pg_insts ${io_root}*VDDPST_*  -exclude_region {1050 1050 3840 3840}
    #assign_bumps -multi_bumps_to_multi_pads -selected -pg_only -pg_nets VDDPST -pg_insts ${io_root}*VDDPSTANA_*  -exclude_region {1050 1050 3840 3840}
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "b"]
    assign_signal_to_bump -selected -net VDD
    assign_bumps -multi_bumps_to_multi_pads -selected -pg_only -pg_nets VDD -pg_insts ${io_root}*VDD_*  -exclude_region {1050 1050 3840 3840}
    #assign_bumps -multi_bumps_to_multi_pads -selected -pg_only -pg_nets VDD -pg_insts ${io_root}*VDDANA_*  -exclude_region {1050 1050 3840 3840}

    # Select all signal bumps
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "s"]
    assign_bumps -selected -exclude_region {1050 1050 3840 3840} -exclude_pg_nets {VDD VSS VDDPST}
    deselect_bumps

    ### Select all core power pins and assign as VDD
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "r"]
    select_bumps -bumps [bumps_of_type $bump_types "1"]
    select_bumps -bumps [bumps_of_type $bump_types "2"]
    select_bumps -bumps [bumps_of_type $bump_types "3"]
    select_bumps -bumps [bumps_of_type $bump_types "4"]
    select_bumps -bumps [bumps_of_type $bump_types "5"]
    select_bumps -bumps [bumps_of_type $bump_types "6"]
    assign_signal_to_bump -selected -net VDD 
    deselect_bumps

    gui_show_bump_connections
}

proc gen_rdl_blockages {} {
    set io_b1 10.8
    set io_b2 18.5
    set io_b3 50.0

    set des [get_db current_design]
    set urx [get_db $des .bbox.ur.x]
    set ury [get_db $des .bbox.ur.y]
    set llx [get_db $des .bbox.ll.x]
    set lly [get_db $des .bbox.ll.y]

    create_route_blockage -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx [expr $ury - $io_b1] $urx $ury"
    create_route_blockage -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx [expr $ury - $io_b3] $urx [expr $ury - $io_b2]"
    create_route_blockage -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx [expr $lly + $io_b2] $urx [expr $lly + $io_b3]"
    create_route_blockage -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx $lly $urx [expr $lly + $io_b1]"

    create_route_blockage -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx $lly [expr $llx + $io_b1] $ury"
    create_route_blockage -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "[expr $llx + $io_b2] $lly [expr $llx + $io_b3] $ury"
    create_route_blockage -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "[expr $urx - $io_b3] $lly [expr $urx - $io_b2] $ury"
    create_route_blockage -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "[expr $urx - $io_b1] $lly $urx $ury"

    # get_db current_design .core_bbox
    foreach bump [get_db bumps Bump*] {
	set bbox [get_db $bump .bbox]
	create_route_blockage -name rdl_$bump -layers RV \
	    -area $bbox
    }
}

proc gen_power_rdl {} {
    global bump_types

    set_db flip_chip_connect_power_cell_to_bump false
    set_db flip_chip_bottom_layer AP
    set_db flip_chip_top_layer AP
    set_db flip_chip_constraint_file ../../scripts/vlsi/flow/scripts/fcroute.cons

    gen_rdl_blockages

    set_db add_stripes_stacked_via_bottom_layer M9
    set_db add_stripes_stacked_via_top_layer AP

    # Add straps over contiguous rows of power bumps
    add_stripes -nets {VDD VSS} \
	-over_bumps 1 \
	-layer AP -direction horizontal \
	-width 20.0 -spacing 20.0 -number_of_sets 1 \
	-start_from left \
	-area {1050.0 1050.0 3850.0 3850.0}

    # Add small straps to all remaining VDD and VSS bumps.
    select_bumps -nets {VDD VSS}
    gen_power_rdl_sel
}

proc gen_power_rdl_sel {} {
    foreach bump [get_db selected] {
	set llx [get_db $bump .bbox.ll.x]
	set lly [get_db $bump .bbox.ll.y]
	set urx [get_db $bump .bbox.ur.x]
	set ury [get_db $bump .bbox.ur.y]
	set cx [expr ($llx + $urx) / 2.0]
	set cy [expr ($lly + $ury) / 2.0]
	set dx 20.0
	set dy 10.0
		 
	if {$cx > 1050.0 && $cx < 3850.0 && $cy > 1050.0 && $cy < 3850.0} {
	    # Skip the center 16 x 16 grid of pads.
	    continue
	}
	set bb [list [expr $llx - $dx] [expr $cy - $dy] \
		    [expr $urx + $dx] [expr $cy + $dy]]
	add_stripes -nets [get_db $bump .net.name] \
	    -layer AP -direction horizontal \
	    -width 20.0 -spacing 20.0 -number_of_sets 1 \
	    -start_from left \
	    -area $bb
    }

    # eval_legacy { addStripe -nets {VDD VSS} -layer AP -direction horizontal -width 10 -spacing 10 -number_of_sets 1 -area {2072.9365 3035.8215 2824.8235 3091.03} -start_from left -switch_layer_over_obs false -max_same_layer_jog_length 2 -padcore_ring_top_layer_limit AP -padcore_ring_bottom_layer_limit M9 -block_ring_top_layer_limit AP -block_ring_bottom_layer_limit M9 -use_wire_group 0 -snap_wire_center_to_grid None -skip_via_on_pin {  standardcell } -skip_via_on_wire_shape {  noshape } }

    # assign_pg_bumps -nets VDD -selected -connect_type stripe
    # route_flip_chip -target connect_bump_to_ring_stripe -bottom_layer AP -top_layer AP -route_width 20 -selected_bumps
    # eval_legacy "fcroute -type power \
    # -layerChangeBotLayer AP \
    # -layerChangeTopLayer AP \
    # -routeWidth 0 \
    # -selected_bump \
    # -keepDRC \
    # -straightConnections straightWithDrcClean \
    # -jogControl preferSameLayer"

}

proc gen_rdl {} {
    global bump_types
    set io_root pads/IOPAD_

    unassign_bumps -all

    # Select all VSSPST bumps
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "G"]
    assign_bumps -selected -pg_only -pg_nets VSSPST -pg_insts ${io_root}VDDPST_* \
	-multi_bumps_to_multi_pads

    # Select all VSS bumps
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "g"]
    assign_bumps -selected -pg_only -pg_nets VSS -pg_insts ${io_root}VDD_*    \
	-multi_bumps_to_multi_pads

    # Select all VDDPST bumps
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "o"]
    assign_bumps -selected -pg_only -pg_nets VDDPST -pg_insts ${io_root}VDDPST_* \
	-multi_bumps_to_multi_pads

    # Select all VDD bumps
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "b"]
    assign_bumps -selected -pg_only -pg_nets VDD -pg_insts ${io_root}VDD_*    \
	-multi_bumps_to_multi_pads

    set_db flip_chip_connect_power_cell_to_bump true
    set_db flip_chip_bottom_layer AP
    set_db flip_chip_top_layer AP
    set_db flip_chip_constraint_file [get_db flow_source_directory]/fcroute.cons
    route_flip_chip -target connect_bump_to_pad -verbose -route_engine global_detail -delete_existing_routes
}

proc bumps_of_type {bump_array type} {
    set bump_index 1
    set bump_list {}
    foreach type_char [split [join [lreverse $bump_array] ""] {}] {
	    if {$type_char == $type} {
	        lappend bump_list "Bump_${bump_index}.*"
	    }
	    incr bump_index
    }
    return $bump_list
}

proc gen_route_bumps {} {
  gen_rdl_blockages

  deselect_bumps -bumps *
  select_bumps -type signal
  select_bumps -type power
  select_bumps -type ground
  foreach bump [get_db selected] {
    regexp {GarnetSOC_pad_frame\/(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
    if {($row>3) && ($row<24) && ($col>3) && ($col<24)} {
      set b "${base}${row}.${col}"
      deselect_bumps -bumps $b
    }
  }
  select_bumps -type signal

  set_db flip_chip_connect_power_cell_to_bump true
  set_db flip_chip_bottom_layer AP
  set_db flip_chip_top_layer AP
  set_db flip_chip_route_style manhattan 
  set_db flip_chip_connect_power_cell_to_bump true 
  route_flip_chip -incremental -target connect_bump_to_pad -verbose -route_engine global_detail -selected_bumps -bottom_layer AP -top_layer AP -route_width 3.6 -double_bend_route


  ##select_bumps -type ground
  ##foreach bump [get_db selected] {
  ##  regexp {top\/(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
  ##  if {($row>4) && ($row<23) && ($col>4) && ($col<23)} {
  ##    set b "${base}${row}.${col}"
  ##    deselect_bumps -bumps $b
  ##  }
  ##}

  ##set_db flip_chip_connect_power_cell_to_bump true
  ##set_db flip_chip_bottom_layer AP
  ##set_db flip_chip_top_layer AP
  ##route_flip_chip -incremental -target connect_bump_to_pad -verbose -route_engine global_detail -bottom_layer AP -top_layer AP -route_width 3.6  -double_bend_route

    set_db add_stripes_stacked_via_bottom_layer AP
    set_db add_stripes_stacked_via_top_layer AP

  add_stripes -nets {VDD VSS} \
  -over_bumps 1 \
  -layer AP -direction horizontal \
  -width 30.0 -spacing 20.0 -number_of_sets 1 \
  -start_from left \
  -area {1050.0 1050.0 3850.0 3850.0}
}


proc add_boundary_fiducials {} {
  delete_inst -inst ifid*ul*
  gen_fiducial_set 100 4824.0 ul false
  select_obj [get_db insts ifid*ul*]
  snap_floorplan -selected
  deselect_obj -all
  delete_inst -inst ifid*ur*
  gen_fiducial_set 2500.0 4824.00 ur false
  select_obj [get_db insts ifid*ur*]
  snap_floorplan -selected
  deselect_obj -all
  delete_inst -inst ifid*ll*
  gen_fiducial_set 100.0 58.70 ll false
  select_obj [get_db insts ifid*ll*]
  snap_floorplan -selected
  deselect_obj -all
  delete_inst -inst ifid*lr*
  gen_fiducial_set 2500.0 58.70 lr false
  select_obj [get_db insts ifid*lr*]
  snap_floorplan -selected
  deselect_obj -all
}

proc add_core_clamps {} {
  delete_inst -inst core_clamp_*
  gen_clamps  500 4500 core_clamp_11
  gen_clamps 1100 4450 core_clamp_12
  # gen_clamps 2500 4500 core_clamp_13
  gen_clamps 3500 4500 core_clamp_14
  gen_clamps 4400 4500 core_clamp_15
  gen_clamps  500 3500 core_clamp_21
  gen_clamps 1580 3300 core_clamp_22
  gen_clamps 3000 3200 core_clamp_23
  gen_clamps 3600 3500 core_clamp_24
  gen_clamps 4400 3500 core_clamp_25
  gen_clamps  500 2700 core_clamp_31
  gen_clamps 1500 2720 core_clamp_32
  gen_clamps 2776 2500 core_clamp_33
  # gen_clamps 3500 2500 core_clamp_34
  # gen_clamps 4500 2500 core_clamp_35
  gen_clamps  500 1250 core_clamp_41
  gen_clamps 1500 1050 core_clamp_42
  gen_clamps 2776 1250 core_clamp_43
  # gen_clamps 3500 1500 core_clamp_44
  # gen_clamps 4500 1500 core_clamp_45
  gen_clamps  500  500 core_clamp_51
  gen_clamps 1200  500 core_clamp_52
  # gen_clamps 2500  500 core_clamp_53
  gen_clamps 3400  400 core_clamp_54
  gen_clamps 4400  400 core_clamp_55

  connect_global_net VDD -type pg_pin -pin_base_name VDDESD -inst core_clamp*
  connect_global_net VSS -type pg_pin -pin_base_name VSSESD -inst core_clamp*
}

proc add_core_fiducials {} {
  delete_inst -inst ifid*cc*

  # I'll probably regret this...
  set_proc_verbose gen_fiducial_set

  # ORIG SPACING
  # gen_fiducial_set [snap_to_grid 2346.30 0.09 99.99] 2700.00 cc true 0
  # x,y = 2346.39,2700

  # Want to double the footprint of the alignment cells in both x and y
  # gen_fiducial_set [snap_to_grid 2274.00 0.09 99.99] 2200.00 cc true 0
  # x,y = 2274,2200

  # Congestion happens at the bottom of the column between like 2200-2700
  # So let's move them back up, but keep some spacing b/c that was good I think
  gen_fiducial_set [snap_to_grid 2274.00 0.09 99.99] 2700.00 cc true 0
  # x,y = 2274,2700
}

proc gen_clamps {x y inst_name} {
  # [stevo]: confusingly, an _H clamp must be rotated and placed vertically
  # but this should give it the most power stripe access
  create_inst -cell PCLAMPC_H -inst $inst_name \
    -location "$x $y" -orient R90 -status fixed
  place_inst $inst_name $x $y R90 -fixed
  create_place_halo -insts $inst_name \
    -halo_deltas {2 2 2 2} -snap_to_site
  create_route_halo -bottom_layer M0 -space 2 -top_layer M3 \
    -inst $inst_name
}

# [stevo]: moved to stream_out
#proc add_sealring {} {
#  delete_inst -inst sealring*
#  create_inst -cell  N16_SR_B_1KX1K_DPO_DOD_5_x_5 -inst sealring -physical
#
#  # Place the sealring to center the IO pads
#  set core_fp_width 4900
#  set core_fp_height 4900
#  set sr_center_x [expr 5001.6 / 2.0]
#  set sr_center_y [expr 5001.6 / 2.0]
#  set core_center_x [expr $core_fp_width / 2.0]
#  set core_center_y $core_center_x
#  set sr_offset_x [expr $core_center_x - $sr_center_x + 0.016]
#  set sr_offset_y [expr $core_center_y - $sr_center_y + 0.016]
#  # Seal Ring place holder
#  place_inst sealring $sr_offset_x $sr_offset_y -fixed
#}

proc gen_fiducial_set {pos_x pos_y {id ul} grid {cols 8}} {
    # delete_inst -inst ifid_*
    # FEOL
    set core_fp_width 4900
    set core_fp_height 4900

    set ICOVL_cells {
      ICOVL_CODH_OD_20140702
      ICOVL_CODV_OD_20140702
      ICOVL_IMP1_OD_20140702
      ICOVL_IMP2_OD_20140702
      ICOVL_IMP3_OD_20140702
      ICOVL_PMET_OD_20140702
      ICOVL_VT2_OD_20140702
      ICOVL_PO_OD_20140702
      ICOVL_CPO_OD_20140702
      ICOVL_CMD_OD_20140702
      ICOVL_M0OD_OD_20140702
      ICOVL_M0OD_PO_20140702
      ICOVL_M0PO_CMD_20140702
      ICOVL_M0PO_M0OD_20140702
      ICOVL_M0PO_PO_20140702
      ICOVL_M1L1_M0OD_20140702
      ICOVL_M1L2_M1L1_20140702
      ICOVL_M2L1_M1L1_20140702
      ICOVL_M2L2_M2L1_20140702
      ICOVL_M3L1_M2L1_20140702
      ICOVL_M3L2_M3L1_20140702
      ICOVL_M4L1_M3L1_20140702
      ICOVL_M5L1_M4L1_20140702
      ICOVL_M6L1_M5L1_20140702
      ICOVL_M7L1_M6L1_20140702
      ICOVL_V0H1_M0OD_20140702
      ICOVL_V0H1_M1L1_20140702
      ICOVL_V0H2_M1L1_20140702
      ICOVL_V0H2_M1L2_20140702
      ICOVL_V1H1_M1L1_20140702
      ICOVL_V1H1_M2L1_20140702
      ICOVL_V2H1_M2L1_20140702
      ICOVL_V2H1_M3L1_20140702
      ICOVL_V3H1_M3L1_20140702
      ICOVL_V3H1_M3L2_20140702
      ICOVL_V4H1_M4L1_20140702
      ICOVL_V4H1_M5L1_20140702
      ICOVL_V5H1_M5L1_20140702
      ICOVL_V5H1_M6L1_20140702
      ICOVL_V6H1_M6L1_20140702
      ICOVL_V6H1_M7L1_20140702
    }

    set DTCD_cells_feol N16_DTCD_FEOL_20140707   

    set DTCD_cells_beol {
      N16_DTCD_BEOL_M1_20140707
      N16_DTCD_BEOL_M2_20140707
      N16_DTCD_BEOL_M3_20140707
      N16_DTCD_BEOL_M4_20140707
      N16_DTCD_BEOL_M5_20140707
      N16_DTCD_BEOL_M6_20140707
      N16_DTCD_BEOL_M7_20140707
      N16_DTCD_BEOL_V1_20140707
      N16_DTCD_BEOL_V2_20140707
      N16_DTCD_BEOL_V3_20140707
      N16_DTCD_BEOL_V4_20140707
      N16_DTCD_BEOL_V5_20140707
      N16_DTCD_BEOL_V6_20140707
    }

    # [stevo]: DRC rule sets this, cannot be smaller
    # [stevr]: yeh but imma make it bigger (09/2019) (doubling dx, dy)

    # set dx [snap_to_grid [expr 2*(2*8+2*12.6)] 0.09 0]
    # set dy [expr 2*41.472]
    if {$id == "cc"} {

#         puts "@fileinfo id=$id"
#         puts "@fileinfo Double it BUT ONLY for center core (cc) cells"
#         set dx [snap_to_grid [expr 2*(2*8+2*12.6)] 0.09 0]
#         set dy [expr 2*41.472]

        # Okay let's try 1.5 spacing ish
        puts "@fileinfo id=$id"
        puts "@fileinfo y-space 1.5x BUT ONLY for center core (cc) cells"
        set dx [snap_to_grid [expr 2*(2*8+2*12.6)] 0.09 0]
        set dy 63.000


    } else {    
        set dx [snap_to_grid [expr 2*8+2*12.6] 0.09 0]
        set dy 41.472
    }
    set ix $pos_x
    set iy $pos_y
    set i 1
    set fid_name "init"
    # set cols 8


    # [stevo]: don't put below/above IO cells
    if {$grid != "true"} {
      set x_bounds ""
      foreach loc [get_db [get_db insts *IOPAD_VDD_**] .bbox] {
        set y [lindex $loc 1]
        if {$pos_y > [expr $core_fp_height/2] && $y > [expr $core_fp_height/2]} {
          lappend x_bounds [list [lindex $loc 0] [lindex $loc 2]]
        }
        if {$pos_y < [expr $core_fp_height/2] && $y < [expr $core_fp_height/2]} {
          lappend x_bounds [list [lindex $loc 0] [lindex $loc 2]]
        }
      }
    }

    # [stevo]: avoid db access by hard-coding width
    set width 12.6
    
    foreach cell $ICOVL_cells {
      set fid_name "ifid_icovl_${id}_${i}"
      create_inst -cell $cell -inst $fid_name \
        -location "$ix $iy" -orient R0 -physical -status fixed
      place_inst $fid_name $ix $iy R0 -fixed ; # [stevo]: need this!
      set x_start $ix
      set x_end [expr $ix+$width]
      if {$grid != "true"} {
        foreach x_bound $x_bounds {
          set x_bound_start [lindex $x_bound 0]
          set x_bound_end [lindex $x_bound 1]
          if {($x_start >= $x_bound_start && $x_start <= $x_bound_end) || ($x_end >= $x_bound_start && $x_end <= $x_bound_end)} {
            set ix [expr $x_bound_end + 5]
          }
        }
      }
      place_inst $fid_name $ix $iy r0
      if {$grid == "true"} {
          set halo_margin_target 15
      } else {
          set halo_margin_target 8
      }
      set halo_margin [snap_to_grid $halo_margin_target 0.09 0]
      create_place_halo -insts $fid_name \
        -halo_deltas $halo_margin $halo_margin $halo_margin $halo_margin -snap_to_site
      if {$grid == "true"} {
        create_route_blockage -name $fid_name -inst $fid_name -cover -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing $halo_margin
        create_route_blockage -name $fid_name -inst $fid_name -cover -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing [expr $halo_margin + 2]
      } else {
        create_route_blockage -name $fid_name -inst $fid_name -cover -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing 2.5
      }
      if {$grid == "true"} {
        if {($ix-$pos_x)/$dx > $cols} {
          set ix $pos_x
          set iy [expr $iy + $dy]
        } else {
          set ix [expr $ix + $dx]
        }
      } else {
        set ix [expr $ix + $dx]
      }
      incr i
    }

    # once more for the DTCD fiducial
    if {$grid != "true"} { 
      set x_start $ix
      set x_end [expr $ix+$width]
      foreach x_bound $x_bounds {
        set x_bound_start [lindex $x_bound 0]
        set x_bound_end [lindex $x_bound 1]
        if {($x_start >= $x_bound_start && $x_start <= $x_bound_end) || ($x_end >= $x_bound_start && $x_end <= $x_bound_end)} {
          set ix [expr $x_bound_end + 5]
        }
      }
    }

    # The DTCD cells overlap
    set cell $DTCD_cells_feol
    set fid_name "ifid_dtcd_feol_${id}_${i}"
    create_inst -cell $cell -inst $fid_name \
      -location "$ix $iy" -orient R0 -physical -status fixed
    place_inst $fid_name $ix $iy R0 -fixed
    if {$grid == "true"} {
      set tb_halo_margin 27.76
      set lr_halo_margin 22.534
    } else {
      set tb_halo_margin 8
      set lr_halo_margin 8
    }
    create_place_halo -insts $fid_name \
        -halo_deltas $lr_halo_margin $tb_halo_margin $lr_halo_margin $tb_halo_margin -snap_to_site
    create_route_blockage -name $fid_name -inst $fid_name -cover -layers {M1 M2 M3 M4 M5 M6 M7 M8 M9} -spacing $lr_halo_margin
    create_route_blockage -name $fid_name -inst $fid_name -cover -layers {VIA1 VIA2 VIA3 VIA4 VIA5 VIA6 VIA7 VIA8} -spacing [expr $lr_halo_margin + 2]
    #create_place_halo -insts $fid_name \
    #  -halo_deltas {8 8 8 8} -snap_to_site
    incr i
    foreach cell $DTCD_cells_beol {
      set fid_name "ifid_dtcd_beol_${id}_${i}"
      create_inst -cell $cell -inst $fid_name \
        -location "$ix $iy" -orient R0 -physical -status fixed
      place_inst $fid_name $ix $iy R0 -fixed
      incr i
    }
}

# [stevo]: copied from NGC chip
# appears to be used during routing (see innovus_config.tcl)
proc gen_routing_rules {} {

  set metal_layer "M1 M2 M3 M4 M5 M6 M7 M8"

  foreach mlayer $metal_layer {
    puts "${mlayer}  [expr {2*[get_db [get_db layers $mlayer] .width]}]"
    puts "${mlayer} [expr {2*[get_db [get_db layers $mlayer] .min_spacing]}]"
    set ${mlayer}width [expr {2*[get_db [get_db layers $mlayer] .width]}]
    set ${mlayer}spacing [expr {2*[get_db [get_db layers $mlayer] .min_spacing]}]
  }


  create_route_rule -name NDR_2W2S \
    -width    {M1 0.064 M2 0.064 M3 0.076 M4 0.08 M5 0.08 M6 0.08 M7 0.08 } \
    -spacing  {M1 0.064 M2 0.064 M3 0.064 M4 0.08 M5 0.08 M6 0.08 M7 0.08 } \

  create_route_type -name leaf \
    -route_rule NDR_2W2S       \
    -top_preferred_layer    M7 \
    -bottom_preferred_layer M1 \
    -preferred_routing_layer_effort high
  create_route_type -name trunk \
    -route_rule NDR_2W2S       \
    -top_preferred_layer    M7 \
    -bottom_preferred_layer M1 \
    -preferred_routing_layer_effort high
  create_route_type -name top \
    -route_rule NDR_2W2S       \
    -top_preferred_layer    M7 \
    -bottom_preferred_layer M1 \
    -preferred_routing_layer_effort high


}

proc gen_power {} {

    delete_inst -inst FE_FILLER_*
    delete_inst -inst WELLTAP_*
    delete_inst -inst ENDCAP*
    eval_legacy {setEndCapMode \
     -rightEdge BOUNDARY_LEFTBWP16P90 \
     -leftEdge BOUNDARY_RIGHTBWP16P90 \
     -leftBottomCorner BOUNDARY_NCORNERBWP16P90 \
     -leftTopCorner BOUNDARY_PCORNERBWP16P90 \
     -rightTopEdge FILL3BWP16P90 \
     -rightBottomEdge FILL3BWP16P90 \
     -topEdge "BOUNDARY_PROW3BWP16P90 BOUNDARY_PROW2BWP16P90" \
     -bottomEdge "BOUNDARY_NROW3BWP16P90 BOUNDARY_NROW2BWP16P90" \
     -fitGap true \
     -boundary_tap true}
    
    eval_legacy {set_well_tap_mode \
     -rule 5.04 \
     -bottom_tap_cell BOUNDARY_NTAPBWP16P90 \
     -top_tap_cell BOUNDARY_PTAPBWP16P90 \
     -cell TAPCELLBWP16P90}
    
    add_endcaps 

    # [stevo]: can't place these close to endcaps
    foreach inst [get_db insts -if {.is_macro == true}] {
      puts [get_db $inst .name]
      create_place_blockage -inst [get_db $inst .name] -outer_ring_by_side {3.5 2.5 3.5 2.5} -name TAPBLOCK
    }
    foreach inst [get_db insts -if {.name == core_clamp*}] {
      puts [get_db $inst .name]
      create_place_blockage -inst [get_db $inst .name] -outer_ring_by_side {3.5 2.5 3.5 2.8} -name TAPBLOCK
    }
    foreach inst [get_db insts -if {.name == ifid_icovl_* || .name == ifid_dtcd_feol_*}] {
      puts [get_db $inst .name]
      create_place_blockage -inst [get_db $inst .name] -outer_ring_by_side {9.5 8.5 9.5 8.5} -name TAPBLOCK
    }
    add_well_taps \
      -cell_interval 10.08 \
      -in_row_offset 5
    eval_legacy {deletePlaceBlockage  TAPBLOCK}

    puts "@file_info gen_floorplan.tcl/gen_power: add_rings"
    # [stevo]: add rings around everything in M2/M3
    set_db add_rings_stacked_via_top_layer M9
    set_db add_rings_stacked_via_bottom_layer M1
    add_rings \
      -type core_rings   \
      -jog_distance 0.045   \
      -threshold 0.045   \
      -follow core   \
      -layer {bottom M2 top M2 right M3 left M3}   \
      -width 1.96   \
      -spacing 0.84   \
      -offset 1.4   \
      -nets {VDD VSS VDD VSS VDD VSS}

    #NB add a ring around the mdll block
    #add_rings -nets {VDD VSS VDD VSS VDD VSS} -around user_defined -user_defined_region {93.1435 4337.26 93.1435 4804.371 1174.5765 4804.371 1174.5765 4337.26 93.1435 4337.26} -type block_rings -layer {top M2 bottom M2 left M3 right M3} -width {top 1.96 bottom 1.96 left 1.96 right 1.96} -spacing {top 0.84 bottom 0.84 left 0.84 right 0.84} -offset {top 1.4 bottom 1.4 left 1.4 right 1.4} -center 0 -extend_corners {} -threshold 0 -jog_distance 0 -snap_wire_center_to_grid none

    puts "@file_info gen_floorplan.tcl/gen_power: route_pads 1"
    # [stevo]: route pads to this ring
    route_special -connect {pad_pin}  \
      -layer_change_range { M2(2) M8(8) }  \
      -pad_pin_port_connect {all_port one_geom}  \
      -pad_pin_target {ring}  \
      -delete_existing_routes  \
      -pad_pin_layer_range { M3(3) M4(4) }  \
      -crossover_via_layer_range { M2(2) M8(8) }  \
      -nets { VSS VDD }  \
      -allow_layer_change 1  \
      -target_via_layer_range { M2(2) M8(8) } \
      -inst [get_db [get_db insts *IOPAD*VDD_*] .name]

    puts "@file_info gen_floorplan.tcl/gen_power: route_pads 2"
    # [stevo]: route pads to this ring
    route_special -connect {pad_pin}  \
      -layer_change_range { M2(2) M8(8) }  \
      -pad_pin_port_connect {all_port one_geom}  \
      -pad_pin_target {ring}  \
      -pad_pin_layer_range { M3(3) M4(4) }  \
      -crossover_via_layer_range { M2(2) M8(8) }  \
      -nets { VSS VDD }  \
      -allow_layer_change 1  \
      -target_via_layer_range { M2(2) M8(8) } \
      -inst [get_db [get_db insts *IOPAD*VDDANA_*] .name]
    
    # Note M1 stripe generation takes like seven hours
    # se "alt_add_stripes mechanism to try out adding by region etc
  if {$::USE_ALTERNATIVE_M1_STRIPE_GENERATION} {
    # Doing it in three sections (to, middle, bottom)
    # seems to take an hour longer actually...
    set_db add_stripes_stacked_via_bottom_layer M2
    set_db add_stripes_stacked_via_top_layer M2
    alt_add_M1_stripes {}
  } else {
    puts "@file_info: ----------------"
    puts "@file_info: gen_floorplan.tcl/gen_power: add_stripes M1"
    puts "@file_info: - expect this to take like 7 hours"
    puts -nonewline "@file_info: Time now "; date +%H:%M
    # standard cell rails in M1
    # [stevo]: no vias
    set_db add_stripes_stacked_via_bottom_layer M2
    set_db add_stripes_stacked_via_top_layer M2
    add_stripes \
      -pin_layer M1   \
      -over_pins 1   \
      -block_ring_top_layer_limit M1   \
      -max_same_layer_jog_length 3.6   \
      -pad_core_ring_bottom_layer_limit M1   \
      -pad_core_ring_top_layer_limit M1   \
      -spacing 1.8   \
      -master "TAPCELL* BOUNDARY*"   \
      -merge_stripes_value 0.045   \
      -direction horizontal   \
      -layer M1   \
      -area {} \
      -block_ring_bottom_layer_limit M1   \
      -width pin_width   \
      -nets {VSS VDD}
  }
    echo M1 Stripes Complete
    puts "@file_info: - M1 Stripes Complete"
    puts -nonewline "@file_info: Time now "; date +%H:%M
    puts "@file_info: ----------------"

    ####NB DIS# Add M2 horizontal stripes matching M1, but narrower (0.064)
    ####NB DIS# took 5 minutes 9 seconds when DRC checking was off, 5 minutes 55 seconds with DRC checking
    ####NB DISset_db add_stripes_stacked_via_bottom_layer M1
    ####NB DISset_db add_stripes_stacked_via_top_layer M3
    ####NB DISadd_stripes \
    ####NB DIS  -pin_layer M1   \
    ####NB DIS  -over_pins 1   \
    ####NB DIS  -block_ring_top_layer_limit M1   \
    ####NB DIS  -max_same_layer_jog_length 3.6   \
    ####NB DIS  -pad_core_ring_bottom_layer_limit M1   \
    ####NB DIS  -pad_core_ring_top_layer_limit M1   \
    ####NB DIS  -spacing 1.8   \
    ####NB DIS  -master "TAPCELL* BOUNDARY*"   \
    ####NB DIS  -merge_stripes_value 0.045   \
    ####NB DIS  -direction horizontal   \
    ####NB DIS  -layer M2   \
    ####NB DIS  -block_ring_bottom_layer_limit M1   \
    ####NB DIS  -width 0.064   \
    ####NB DIS  -area {}   \
    ####NB DIS  -nets {VSS VDD}
    ####NB DISecho M2 Stripes Complete

    puts "@file_info gen_floorplan.tcl/gen_power: add_rings 2"
    set_db add_rings_stacked_via_top_layer M9
    set_db add_rings_stacked_via_bottom_layer M3
    add_rings \
      -type core_rings   \
      -jog_distance 0.045   \
      -threshold 0.045   \
      -follow core   \
      -layer {bottom M8 top M8 right M9 left M9}   \
      -width 2.1   \
      -spacing 0.77   \
      -offset 1.4   \
      -nets {VDD VSS VDD VSS VDD VSS}

    puts "@file_info gen_floorplan.tcl/gen_power: add_boundary,power_mesh"
    # [stevo]: now place boundary fiducials, avoiding routes between rings and power IO cells
    # if we do this earlier, the M2/3 rings do funky stuff
    add_boundary_fiducials
    add_power_mesh_colors
}

proc straps_over_blocks {inst_names} {
  snap_floorplan -block

  set_db add_stripes_stacked_via_bottom_layer M4
  set_db add_stripes_stacked_via_top_layer M5
  foreach inst [get_db insts $inst_names] {
    add_stripes \
      -max_same_layer_jog_length 2.8 \
      -width 0.8 \
      -spacing 0.8 \
      -set_to_set_distance 4.8 \
      -merge_stripes_value 0.045 \
      -layer M5 \
      -direction vertical \
      -area [get_db $inst .bbox] \
      -nets {VDD VSS}
  }
}


# snap_pads.tcl
# Description: Snap IO drivers on the vertical edges of a design to the
#   0.048um FIN grid.
# Author: B. Richards, U. C. Berkeley

proc snap_pads {inst_names} {
  foreach inst [get_db insts $inst_names] {
	  set iname [get_db $inst .name]
	  set loc [lindex [get_db $inst .location] 0]
	  set loc_x [lindex $loc 0]
	  set loc_y [lindex $loc 1]
	  set loc_x_snap $loc_x
	  set loc_y_snap [expr round($loc_y / 0.048) * 0.048]
	  set orient [get_db $inst .orient]

    if { [expr round($loc_y_snap*1000)] != [expr round($loc_y*1000)]} {
      puts "Snapping $iname Orient: $orient Loc: $loc_x $loc_y $loc_x_snap $loc_y_snap"
      if {$orient == "r90"} {
          # This should be a horizontal pad; snap the Y coord.
          place_inst $iname $loc_x_snap $loc_y_snap r90
      } elseif {$orient == "my90"} {
          # This should be a horizontal pad; snap the Y coord.
          place_inst $iname $loc_x_snap $loc_y_snap my90
      } elseif {$orient == "r270"} {
          # This should be a horizontal pad; snap the Y coord.
          place_inst $iname $loc_x_snap $loc_y_snap r270
      } elseif {$orient == "mx90"} {
          # This should be a horizontal pad; snap the Y coord.
          place_inst $iname $loc_x_snap $loc_y_snap mx90
      }
    }
  }
}

