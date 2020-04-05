# An alternate/clever way of checking bump connectivity

proc get_unconnected_bumps1 { args } {
    # Returns a partial list of all unconnected bumps
    # Finds bumps with no wires attached
    # FIXME/NOTE may be obviated/superceded by get_unconnected_bumps2
    # Usage "get_unconnected_bumps1 [ -all | -selected (default) ]

    if { [lindex $args 0] == "-all" } { select_bump_ring }
    set endpoints [ get_all_rdl_wire_endpoints ]
    set ubumps []
    foreach bump [get_db selected] {
        if { ! [ bump_connected $bump $endpoints ] } {
            echo $bump
            echo [ get_db $bump .name ]
            echo get_db $bump .name
            # lappend ubumps [ get_db $bump .name ]
            # lappend ubumps $bump
            lappend ubumps [ get_db $bump .name ]
        }
    }
    echo UBUMPS $ubumps
    return $ubumps
}
proc get_all_rdl_wire_endpoints {} {
    # Find the set of all wires in the RDL layer
    # Can't figure out how to get them w/o selecting them
    # so must save/restore whatever is currently selected :(
    set save_selections [ get_db selected ]; deselect_obj -all

        select_routes -layer AP
        set endpoints [ get_db selected .path ]

    deselect_obj -all; select_obj $save_selections
    return $endpoints
}

# Given a set of wire endpoints, see if any of them are in the given bump
proc bump_connected { bump endpoints } {
    set c [ get_db $bump .center ]
    set c [ split [ lindex $c 0 ] ]
    foreach xy $endpoints {
        set xy [ split $xy ]
        if [ xy_match $c $xy ] { return 1 }
    }
    return 0
}
# select_routes -layer AP; set endpoints [ get_db selected .path ]

# TRUE (1) if wire endpoint xy1 is inside the bump whose center is xy2
proc xy_match {xy1 xy2} {
    set x1 [ lindex $xy1 0 ]; set y1 [ lindex $xy1 1 ]; # echo $x1 , $y1 ,
    set x2 [ lindex $xy2 0 ]; set y2 [ lindex $xy2 1 ]; # echo $x2 , $y2 ,
    set xdiff [ expr $x1 - $x2 ]; # echo $xdiff
    set diff [ expr abs($x1 - $x2) + abs($y1 - $y2) ]; # echo diff=$diff

    # bump is 89x89; so 44 should be "good enough"
    set close_enough [ expr abs($diff) < 44 ]
    return $close_enough
}
# xy_match {4618.375 455.095} {4618.375 455.096}
# xy_match {100 200 } {200 100}
