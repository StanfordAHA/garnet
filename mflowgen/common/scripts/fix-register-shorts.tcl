# What a hack!
# 
# Build 352 introduced a new type of short, where registers of type
# "SDF*" (inc. specifically SDFQD2BWP16P90 and SDFCNQD2BWP16P90)
# "SDFQD2BWP16P90ULVT", in combination with tight spacing on M3
# power-ground stripes, make it extremely difficult and occasionally
# impossible to route wires wires to the pins.
# 
# The register's D pin, in particular, is trapped inside a maze of
# surrounding M2 metal and is nearly impossible to reach. This is
# where the router consistently gives up and runs an M2 wire straight
# over a one of the blockages to get to the D pin, causing a short.
# 
# This script attempts to find and fix such shorts be removing the
# offending M3 stripes nearest to the short and doing an eco reroute.

proc fix_register_shorts {} {
    set DBG 0

    # Opening message
    set msg "Checking for short circuits in SDF* regs (!)..."
    echo "+++ $msg"
    echo "@file_info: $msg"
    if {$DBG} {echo sleep 5; redraw; sleep 5}
    
    # Generate a fresh set of violation markers
    set nv [ frs_drc_check ]

    # DONE if no markers found
    if { $nv == "0" } {
        echo "@file_info: No DRC errors found"
        return
    }
    if {$DBG} {echo sleep 5; redraw; sleep 5}

    # Only care about violations in registers named "SDF*, delete all others.
    # (Specifically care about SDFQD2BWP16P90, SDFCNQD2BWP16P90.)
    set regs [ delete_unrelated_markers SDF* ]
    if {$DBG} {echo sleep 5; redraw; sleep 5}

    # Enable this block to see regs, errors, and stripes highlighted
    # together, when/if you're working interactively
    if { $DBG } {
        deselectAll
        set badregs [dbGet $regs]
        select_obj $badregs
        select_stripes_near_markers { 0.232 }
        echo sleep 5; redraw; sleep 5
    }
    
    # Okay here's the hack:
    # Delete M# stripes that interfere with reg routing
    deselectAll
    select_stripes_near_markers { 0.232 }
    deleteSelectedFromFPlan
    if {$DBG} {echo sleep 5; redraw; sleep 5}

    # Try and fix the errors with ecoRoute.
    # Note: "ecoRoute -drc" seems to do much better than
    # globalDetailRoute with "setNanoRouteMode -routeWithEco true".
    ecoRoute -fix_drc

    # did it work?
    set nv [frs_drc_check]
    set regs [ delete_unrelated_markers SDF* ]
    set n_errors [ llength $regs ]
    return $n_errors

#     if { $n_errors == 0 } {
#         echo "@file_info: Success! No more SDF-related DRC errors."
#     } else {
#         echo "@file_info: Failure! Still have $n_errors SDF-related DRC error(s)."
#     }

}

# Fetch a fresh set of violation markers
proc frs_drc_check {} {
    # Delete existing markers
    if { [dbGet top.markers] != "0x0" } {
        deselectAll; select_obj [ dbGet top.markers ]; deleteSelectedFromFPlan
    }
    # Do a quick DRC, checking only for regular shorts
    # (and parallel run spacing, maybe some others)
    set_verify_drc_mode -reset
    set_verify_drc_mode -check_only regular
    set_verify_drc_mode -ignore_cell_blockage false
    set_verify_drc_mode -disable_rules "\
      jog2jog_spacing \
      eol_spacing \
      cut_spacing \
      min_cut \
      enclosure \
      color \
      min_step \
      protrusion \
      min_area \
      out_of_die \
    "
    clearDrc; verify_drc 
    set_verify_drc_mode -reset

    # Info
    set nv [llength [get_db markers]]
    echo "@file_info: Found $nv DRC errors"
    return $nv
}


# Delete markers unrelated to named instance "name".
# Returns list of instances found atop markers.
# 
# E.g. to delete markers unrelated to SDF* regs:
#   delete_unrelated_markers SDF*
#   # Returns list of SDF* regs containing markers.
# 
proc delete_unrelated_markers { name } {

    # E.g. [ delete_unrelated_markers SDF* ] because
    # only care about violations in registers named e.g. "SDF*
    # (specifically care about SDFQD2BWP16P90, SDFCNQD2BWP16P90)
    set reglist ""
    foreach m [ dbGet top.markers ] {
        if { $m == "0x0" } { break }
        set result 0
        foreach i [ dbGet -p2 top.insts.cell.name $name ] {
            if { $i == "0x0" } { break }
            set result [isMarkerInInstance $m $i]
            # echo "marker $m instance $i $result"
            if "$result == 1" { 
                set viol [dbGet [dbGet $m].subType]
                echo "DRC '$viol' err in reg '[dbGet $i.name]'"
                lappend reglist $i
                break
            }
        }
        if "$result != 1" { 
            set viol [dbGet [dbGet $m].subType]
            set loc  [dbGet [dbGet $m].box]
            echo "Deleting marker for unrelated violation '$viol' at '$loc'"
            deselectAll; select_obj $m; deleteSelectedFromFPlan
        }
    }
    if { [dbGet top.markers] == "0x0" } {
        echo "@file_info: Found no DRC errors in $name registers"
        return ""
    }
    set nv [llength [dbGet top.markers]]
    echo "@file_info: Found $nv DRC errors in $name registers"
    return $reglist
}
# delete_unrelated_markers foo
# delete_unrelated_markers SDFQ*

# Find and select all stripes near violation markers.
proc select_stripes_near_markers { distance } {
    # Stripe pitch is about .35 and width is .114 
    # so can use (.35+.114)/2 for reasonable distance
    # set distance .232
    foreach m [dbGet top.markers] {

        set mar $m
        set llx [get_db $mar .bbox.ll.x]
        set lly [get_db $mar .bbox.ll.y]
        set urx [get_db $mar .bbox.ur.x]
        set ury [get_db $mar .bbox.ur.y]
        # puts "found marker bounding box $llx $lly $urx $ury"

        set xleft  [ expr $llx - $distance ]
        set xright [ expr $llx + $distance ]
        # echo "$xleft 0.0 $xright 100.0"

        editSelect -area "$xleft 0.0 $xright 100.0" -shape STRIPE
    }
}

# Return 1 if marker is inside instance, else 0
proc isMarkerInInstance { marker instance } {
    # echo "marker:   [get_db $marker   .bbox]"
    # echo "instance: [get_db $instance .bbox]"

    # Find marker location LL
    set marker_llx [get_db $marker .bbox.ll.x]
    set marker_lly [get_db $marker .bbox.ll.y]
    # FIXME should really use [dbGet $marker.box_llx] etc. :(

    # Find instance box
    set instance_llx [get_db $instance .bbox.ll.x]
    set instance_lly [get_db $instance .bbox.ll.y]

    set instance_urx [get_db $instance .bbox.ur.x]
    set instance_ury [get_db $instance .bbox.ur.y]

    set x_in_range "( $marker_llx > $instance_llx ) && ( $marker_llx < $instance_urx )"
    set y_in_range "( $marker_lly > $instance_lly ) && ( $marker_lly < $instance_ury )"

    # echo '$x_in_range'
    # echo '$y_in_range'

#     set RESULT [expr "\
#         ( $marker_llx > $instance_llx ) && ( $marker_llx < $instance_urx ) \
#         && \
#         ( $marker_lly > $instance_lly ) && ( $marker_lly < $instance_ury ) \
#     "]

    set RESULT [ expr "$x_in_range && $y_in_range" ]
    return $RESULT
}
# delete_unrelated_markers foo

set DBG 0
set n_errors [ fix_register_shorts ]
if { $n_errors == 0 } {
    echo "@file_info: Success! No more SDF-related DRC errors."
} else {
    echo "@file_info: Failure! Still have $n_errors SDF-related DRC error(s)."
    echo exit 13
    if { ! $DBG } { exit 13 }
}
