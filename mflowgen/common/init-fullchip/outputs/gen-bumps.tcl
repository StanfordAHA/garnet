# from floorplan.tcl:

#----------------------------------------------------------------
# This is probably for the RDL bump routing I guess?
# See "man setNanoRouteMode" for legacy equivalents

# set_db route_design_antenna_diode_insertion true 
setNanoRouteMode -routeInsertAntennaDiode true

# set_db route_design_antenna_cell_name ANTENNABWP16P90 
setNanoRouteMode -routeAntennaCellName $ADK_ANTENNA_CELL

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
# bumpCell: name of bump cell from ADK
proc gen_bumps { bumpCell } {
    set io_root IOPAD
    set nb_rows 51
    set nb_cols 25
    set bp_x 155.952; # bump pitch with no shrink
    set bp_y 78.12; # bump pitch with no shrink
    set bump_start_x 63.936
    set bump_start_y 62.46
    deleteBumps -all
    create_bump -cell $bumpCell   \
        -edge_spacing {12.96 13.86 12.96 13.86}   \
        -loc_type cell_lowerleft   \
        -name_format "Bump_%i.%r.%c"   \
        -orientation R0   \
        -pitch $bp_x $bp_y   \
        -loc $bump_start_x $bump_start_y   \
        -pattern_array "$nb_rows $nb_cols" \
        -stagger_type odd_rows \
        -stagger_offset [expr $bp_x / 2.0]

    # delete the middle column (only the left half of it)
    select_bumps -bumps "Bump_*.*.13"
    deselect_bump -area {2000 0 4000 4000}
    # delete the middle row
    select_bumps -bumps "Bump_*.26.*"
    # delete the top right single bump
    select_bumps -bumps "Bump_*.47.24"
    
    delete_bumps -selected
    
    # . -> Empty (you created it and deleted it, so the index has already beeb assigned to them)
    # V -> Core VDD
    # G -> Core VSS
    # o -> IOVDD
    # g -> IOVSS
    # d -> Diff Pair (Data)
    set bump_types {
    "dddddddddddddddddddddddd"
    "dgdddddddddd.ddddddddddgd"
    "dddddddddddddddddddddddd"
    "dgdddddddddd.ddddddddddgd"
    "ggggggggggggggggggggggg."
    "ogoooooooooo.oooooooooogo"
    "ggoddddddddddddddddddogg"
    "dgdddddddddd.ddddddddddgd"
    "ddoddddddddddddddddddodd"
    "dgdddddddddd.ddddddddddgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "........................."
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdGGGGGGGGG.GGGGGGGGGdgd"
    "ddoVVVVVVVVVVVVVVVVVVodd"
    "dgdddddddddd.ddddddddddgd"
    "ddoddddddddddddddddddodd"
    "dgdddddddddd.ddddddddddgd"
    "ggoddddddddddddddddddogg"
    "ogoooooooooo.oooooooooogo"
    "gggggggggggggggggggggggg"
    "dgdddddddddd.ddddddddddgd"
    "dddddddddddddddddddddddd"
    "dgdddddddddd.ddddddddddgd"
    "dddddddddddddddddddddddd"
    }

    # Assign signal bumps
    deselect_bump
    select_bump -bumps [bumps_of_type $bump_types "d"]
    # exclude the outer most bumps
    deselect_bump -area {0 0 4000 100}
    deselect_bump -area {0 0 100 4000}
    deselect_bump -area {0 3950 4000 4050}
    deselect_bump -area {3800 0 4000 4050}
    assignBump -selected -exclude_pgnet {VDD VSS VDDPST}
    deselect_bumps

    # Assign all IOVDD bumps
    # deselect_bumps
    # select_bumps -bumps [bumps_of_type $bump_types "o"]
    # assign_signal_to_bump -selected -net VDDPST
    # assign_bumps \
    #     -multi_bumps_to_multi_pads \
    #     -selected \
    #     -pg_only \
    #     -pg_nets VDDPST \
    #     -pg_insts *SUPPLY*
    # # Assign all IOVSS bumps
    # deselect_bumps
    # select_bumps -bumps [bumps_of_type $bump_types "g"]
    # assign_signal_to_bump -selected -net VSS 
    # assign_bumps \
    #     -multi_bumps_to_multi_pads \
    #     -selected \
    #     -pg_only \
    #     -pg_nets VSS \
    #     -pg_insts *SUPPLY*

    ########################################################################
    # SIGNAL BUMP ASSIGNMENTS - automatically
    # Ugh yes it's a mixture of stylus and legacy commands :( :(

    # Select all signal bumps
    # deselect_bump
    # select_bump -bumps [bumps_of_type $bump_types "d"]
    # assignBump -selected -exclude_pgnet {VDD VSS VDDPST}
    # deselect_bumps
    
    # Assign ESD label to all power/ground bumps
    # select_bumps -bumps [bumps_of_type $bump_types "g"]
    # foreach bump_center [dbGet selected.bump_shape_center] {
    #   add_gui_text -label HC_POWER_ESD -pt $bump_center -layer LBESD -height 1
    # }
    # deselect_bumps

    # voltage labels to prevent DRCs
    # foreach bump_center [dbGet top.bumps.bump_shape_center] {
    #   add_gui_text -label 0 -pt $bump_center -layer CUSTOM_LB_test4 -height 1
    #   add_gui_text -label 0.8 -pt $bump_center -layer CUSTOM_LB_test3 -height 1
    #   # Block VV at LV area of bump
    #   set center_x [lindex $bump_center 0]
    #   set center_y [lindex $bump_center 1]
    #   # Create square blockage with side length "blk_size" centered on bump
    #   set blk_size 70.0
    #   set blk_llx [expr $center_x - ($blk_size / 2)]
    #   set blk_lly [expr $center_y - ($blk_size / 2)]
    #   set blk_urx [expr $center_x + ($blk_size / 2)]
    #   set blk_ury [expr $center_y + ($blk_size / 2)]
    #   createRouteBlk \
    #     -layer VV \
    #     -box $blk_llx $blk_lly $blk_urx $blk_ury 
    # }

    # gui_show_bump_connections
}

gen_bumps $ADK_BUMP_CELL
