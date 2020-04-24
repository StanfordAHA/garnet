########################################################################
# check_io_to_bump_connectivity command does not do the right thing!
# Everything from here down is designed to replace that functionality,
# only better. Instead of
#   check_io_to_bump_connectivity
#   check_connectivity -nets pad*
#
# For a list of all unconnected bumps, can simply do
#   get_unconnected_bumps -all

# For a nice summary, can do
#   check_all_bumps
#   "@file_info: Routed 1/288 bumps, 287 remain unconnected"
proc check_all_bumps {} {
    set n_bumps [ llength [ get_db selected ] ]
    set unconnected [ get_unconnected_bumps -all ]
    set n_unconnected [ llength $unconnected ]
    set n_connected [ expr $n_bumps - $n_unconnected ]
    set msg1 "Routed $n_connected/$n_bumps bumps"
    set msg2 "$n_unconnected remain unconnected"
    puts "@file_info:   - $msg1, $msg2"
}

# Among a selected group, tells how many bumps are unconnected
proc check_selected_bumps {} {
    # -v:
    #   @file_info:   Routed 283/288 bumps, 5 remain unconnected
    # -brief:
    #   @file_info:   - all bumps connected (78/78)
    #   @file_info:   - WARNING 5 UNCONNECTED BUMPS (got 35/40)
    set n_bumps [ llength [ get_db selected ] ]
    set unconnected [ get_unconnected_bumps -selected ]
    set n_unconnected [ llength $unconnected ]
    set n_connected [ expr $n_bumps - $n_unconnected ]

    if { $n_connected == $n_bumps } {
        puts "@file_info:   - all bumps connected ($n_connected/$n_bumps)"
    } else {
        puts "@file_info:   - WARNING $n_unconnected UNCONNECTED BUMPS (got $n_connected/$n_bumps)"
        puts "@file_info:   - WARNING UNCONNECTED BUMP(S): $unconnected"
    }
}

proc report_unconnected_bumps { bumps } {
    # If you want to see the unconnected bumps highlighted in the gui, do:
    # deselect_obj -all; select_obj $bumps
    if {![llength $bumps]} {
        puts "@file_info:   NO UNCONNECTED BUMPS"; return
    }

    foreach bump $bumps {
        set b [ get_db bumps -if { .name == $bump } ]
        set n [ get_db $b .net ]
        set n [ get_db $n .name ]
        # echo BUMP $bump B $b NET $n
        puts "@file_info:   STILL UNCONNECTED: $bump <---> $n"
    }
}

proc get_unconnected_bumps { args } {
    # Returns a list of all unconnected bumps
    # Usage: "get_unconnected_bumps [ -all | -selected (default) ]
    # When/if need another way to check bump connectivity, see "get_unconnected_bumps1.tcl"
    set ub1 [ get_unconnected_bumps1 $args ]; # Finds unconnected power bumps
    set ub2 [ get_unconnected_bumps2 $args ]; # Finds (only) unconnected signal bumps
    return [concat $ub1 $ub2]
}

########################################################################
# get_unconnected_bumps2 finds unconnected signal bumps
# but not so good finding unconnected power/ground bumps

proc get_unconnected_bumps2 { args } {
    # Returns a list of all unconnected / partially-connected bumps
    # Usage "get_unconnected_bumps2 [ -all | -selected (default) ]
    # FIXME/NOTE: destroys all existing markers
    # FIXME: should save and restore existing markers, if any
    # Note: -all is fast and accurate, no real need to ever use -selected (maybe?)

    # Save existing selections
    set save_selections [ get_db selected ]; deselect_obj -all

    select_obj [ get_db markers ]; deleteSelectedFromFPlan
    verifyIO2BumpConnectivity > /dev/null

    set incomplete_paths []
    set markers [ get_db markers -if { .subtype == "BumpConnectTargetOpen" } ]
    foreach m $markers {
        set msg [ get_db $m .message ]; # "Net pad_trace_clk_o[0]"
        set net [ lindex $msg 1 ];      # "pad_trace_clk_o[0]"
        if { $net ni $incomplete_paths } { lappend incomplete_paths $net }
    }
    if { [lindex $args 0] != "-all" } {
        set bumps [ get_db bumps ]
    } else {
        set bumps [ get_db selected ]
    }
    set ubumps []
    foreach net $incomplete_paths {
        set b [ get_db bumps -if { .net == "net:*$net" } ]
        lappend ubumps [ get_db $b .name ]
    }

    # Restore saved selections
    deselect_obj -all; select_obj $save_selections

    # return $incomplete_paths
    return $ubumps
}

########################################################################
# get_unconnected_bumps1 finds unconnected power/ground bumps
# but not so good finding unconnected signal bumps

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
            # echo $bump
            # echo [ get_db $bump .name ]
            # echo get_db $bump .name
            # lappend ubumps [ get_db $bump .name ]
            # lappend ubumps $bump
            lappend ubumps [ get_db $bump .name ]
        }
    }
    # echo UBUMPS $ubumps
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
