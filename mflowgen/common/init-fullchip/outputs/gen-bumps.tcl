# from floorplan.tcl:

#----------------------------------------------------------------
# This is probably for the RDL bump routing I guess?
# See "man setNanoRouteMode" for legacy equivalents

# set_db route_design_antenna_diode_insertion true 
setNanoRouteMode -routeInsertAntennaDiode true

# set_db route_design_antenna_cell_name ANTENNABWP16P90 
setNanoRouteMode -routeAntennaCellName ANTENNABWP16P90 

# set_db route_design_fix_top_layer_antenna true
# FIXME CANNOT FIND COMMON UI EQUIVALENT FOR THIS

#----------------------------------------------------------------
# Note in old floorplan.tcl, power happens before bumps i guess
# gen_power

##############################################################################
# Still in old floorplan.tcl:
# # Note: proc gen_bumps is defined in gen_floorplan.tcl
# gen_bumps
# snap_floorplan -all
# 
# # gen_route_bumps
# # FIXED bump routing sr 12/2019
# # Old proc "gen_route_bumps" warned "too many bumps are selected"
# # and it took a long time and a lot of bumps didn't get routed.
# # New routine getn_route_bumps_sr below uses area restrictions
# # etc. to only do a few bumps at a time.
# # 
# # New route_bumps routine "gen_route_bumps_sr" has
# # - incremental bump routing instead of all at once
# # - better check for routed vs. unrouted bumps
# source ../../scripts/gen_route_bumps_sr.tcl
# set_proc_verbose gen_route_bumps_sr; # For debugging
# gen_route_bumps_sr

# NOTE Needs stylus compatibility procs
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

    # create_bump -cell $bumpCell
    create_bump_stylus -cell $bumpCell   \
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
	"sgossbgsssoobboosssgbssogs"
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
    #   sr 1911: Below code gives warning
    #   "**WARN: (IMPSIP-7355):  PG net 'VSS' is dangling"
    #   even though/if do "eval_legacy { globalNetConnect VSS -pin VSS }" first.
    #   Dangling net doesn't seem to harm/help anything tho
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "g"]
    assign_signal_to_bump -selected -net VSS 

    # sr 1910 This is the original code. Looks like a VDD->VSS short to me!!!
    # sr 1911 Okay never mind, it goes to the VSS *port* of the VDD pad I guess.
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
    # sr 1911: **WARN: (IMPSIP-7355):  PG net 'VDDPST' is dangling.
    # Dangling net doesn't seem to harm/help anything tho
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "o"]
    assign_signal_to_bump -selected -net VDDPST
    assign_bumps -multi_bumps_to_multi_pads -selected -pg_only -pg_nets VDDPST -pg_insts ${io_root}*VDDPST_*  -exclude_region {1050 1050 3840 3840}
    #assign_bumps -multi_bumps_to_multi_pads -selected -pg_only -pg_nets VDDPST -pg_insts ${io_root}*VDDPSTANA_*  -exclude_region {1050 1050 3840 3840}

    # sr 1911: **WARN: (IMPSIP-7355):  PG net 'VDD' is dangling.
    # Dangling net doesn't seem to harm/help anything tho
    deselect_bumps
    select_bumps -bumps [bumps_of_type $bump_types "b"]
    assign_signal_to_bump -selected -net VDD
    assign_bumps -multi_bumps_to_multi_pads -selected -pg_only -pg_nets VDD -pg_insts ${io_root}*VDD_*  -exclude_region {1050 1050 3840 3840}
    #assign_bumps -multi_bumps_to_multi_pads -selected -pg_only -pg_nets VDD -pg_insts ${io_root}*VDDANA_*  -exclude_region {1050 1050 3840 3840}

    ########################################################################
    # SIGNAL BUMP ASSIGNMENTS - automatically mostly,
    # except for a couple special assignments for the PHY...
    # Ugh yes it's a mixture of stylus and legacy commands :( :(

    # On special assignment from the analog guys...
    # two new digital signals for the phy with specific bumps requested
    # FIXME/TODO should do this for all the analog signals (i.e. jtag)
    # you know build an array or a dictionary or sumpm
    set cross_bump Bump_620.24.22; set cross_net pad_freq_lvl_cross
    set ramp_bump  Bump_647.25.23; set ramp_net  pad_ramp_clock
    
    assignSigToBump -net $cross_net -bumps $cross_bump
    assignSigToBump -net $ramp_net  -bumps $ramp_bump
    
    # Select all signal bumps
    deselect_bump
    select_bump -bumps [bumps_of_type $bump_types "s"]
    assignBump     -selected -exclude_region {1050 1050 3840 3840} -exclude_pgnet   {VDD VSS VDDPST}
    deselect_bumps

    ########################################################################
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

    # voltage labels to prevent DRCs
    foreach bump_center [dbGet top.bumps.bump_shape_center] {
      add_gui_text -label 0 -pt $bump_center -layer CUSTOM_AP_test4 -height 1
      add_gui_text -label 0.8 -pt $bump_center -layer CUSTOM_AP_test3 -height 1
    }

    gui_show_bump_connections
}
gen_bumps
