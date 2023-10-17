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

# . -> Empty
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
    set nb_rows 51
    set nb_cols 25
    set bp_x 155.952;
    set bp_y 78.12
    set bump_start_x 63.936
    set bump_start_y 62.46
    create_bump -cell           $bumpCell \
                -edge_spacing   {12.96 13.86 12.96 13.86} \
                -loc_type       cell_lowerleft \
                -name_format    "Bump_%i.%r.%c" \
                -orientation    R0 \
                -pitch          $bp_x $bp_y \
                -loc            $bump_start_x $bump_start_y \
                -pattern_array  "$nb_rows $nb_cols" \
                -stagger_type   odd_rows \
                -stagger_offset [expr $bp_x / 2.0]

    # delete the middle column (only the left half of it)
    select_bump -bumps "Bump_*.*.13"
    deselect_bump -area {2000 0 4000 4000}

    # delete the middle row
    select_bump -bumps "Bump_*.26.*"

    # delete the top right single bump
    select_bump -bumps "Bump_*.47.24"
    
    deleteBumps -selected
}

proc assign_signals_to_bumps { bump_types } {
    # Assign signal bumps
    deselect_bump
    select_bump -bumps [bumps_of_type $bump_types "d"]
    # exclude the outer most bumps
    deselect_bump -area {0 0 4000 100}
    deselect_bump -area {0 0 100 4000}
    deselect_bump -area {0 3950 4000 4050}
    deselect_bump -area {3800 0 4000 4050}
    deselect_bump -bumps "Bump_47.2.23"
    deselect_bump -bumps "Bump_73.3.24"
    deselect_bump -bumps "Bump_73.3.24"
    deselect_bump -bumps "Bump_50.3.1"
    assignBump -selected -exclude_pgnet {VDD VSS VDDPST}
    deselect_bump

    # Assign all VCC bumps
    # deselect_bump
    # select_bump -bumps [bumps_of_type $bump_types "V"]
    # assignPGBumps -selected -nets VDD

    # Assign all VCCIO bumps
    # deselect_bump
    # select_bump -bumps [bumps_of_type $bump_types "o"]
    # assignPGBumps -selected -nets VDDPST

    # Assign all IOVSS bumps
    # deselect_bump
    # select_bump -bumps [bumps_of_type $bump_types "g"]
    # select_bump -bumps [bumps_of_type $bump_types "G"]
    # assignPGBumps -selected -nets VSS
}

proc unassign_problematic_bumps {} {
    # These bumps create routes that cut through the stripes
    # Route them manually instead
    deselect_bump
    select_bump -bumps "Bump_1174.48.23"
    select_bump -bumps "Bump_1198.49.22"
    select_bump -bumps "Bump_1173.48.22"
    select_bump -bumps "Bump_1222.50.22"
    select_bump -bumps "Bump_1163.48.12"
    select_bump -bumps "Bump_1155.48.4"
    select_bump -bumps "Bump_1179.49.3"
    select_bump -bumps "Bump_1154.48.3"
    select_bump -bumps "Bump_834.35.1"
    select_bump -bumps "Bump_638.27.1"
    select_bump -bumps "Bump_589.25.1"
    select_bump -bumps "Bump_393.17.1"
    select_bump -bumps "Bump_344.15.1"
    select_bump -bumps "Bump_246.11.1"
    select_bump -bumps "Bump_197.9.1"
    select_bump -bumps "Bump_174.8.3"
    select_bump -bumps "Bump_194.8.23"
    select_bump -bumps "Bump_220.9.24"
    unassignBump -selected
}

gen_bumps $ADK_BUMP_CELL
assign_signals_to_bumps $bump_types
unassign_problematic_bumps 