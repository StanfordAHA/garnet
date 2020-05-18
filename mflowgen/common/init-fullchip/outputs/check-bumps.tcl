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
    # Hm looks like the name should actually be "check_all_selected_bumps"
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

proc report_unconnected_bumps_phy { bumpnet bumplist } {
    # Check $bumplist for unconnected or misconnected bumps
    # EXAMPLE: report_unconnected_bumps_phy ext_clk_test0_p *25.18
    # TEST:    set bumpnet ext_clk_test0_p; set bumplist *25.18; set bump Bump_642.25.18

    # Save selected objects
    set save_selections [ get_db selected ]; deselect_obj -all

    set unconnected_bumps []
    foreach b $bumplist {
        set bump [dbGet top.bumps.name $b]; # set bump Bump_653.26.3

        # Select bumps so as to do get_unconnected_bumps2 further down...
        select_obj $bump

        # Get all wires that cross bump $b
        set bbox     [dbGet [dbGet -p top.bumps.name $b].bump_shape_bbox]
        set wires    [dbQuery -area $bbox -objType sWire]
        set ap_wires [dbGet -p2 $wires.layer.name AP]
        set nets     [dbGet $ap_wires.net.name]

        # Bump is connected if one or more wires belong to required net
        set is_connected false
        foreach net $nets {
            if { $net == $bumpnet } {
                set is_connected true
            } else {
                echo "@file_info ERROR $bumpnet bump '$bump' connected to net '$net' instead"
                set is_connected false
                break
            }
        }
        if { $is_connected == "false" } { lappend unconnected_bumps $bump }
    }

    # Do this check too I dunno why are you asking me ugh
    set ub2 [ get_unconnected_bumps2 -selected ]; # Finds (only) unconnected signal bumps

    # Restore selected objects from before
    deselect_obj -all; select_obj $save_selections

    set ubumps [remove_redundant_items [concat $unconnected_bumps $ub2]]
    report_unconnected_bumps $ubumps
}

proc get_unconnected_bumps { args } {
    # Returns a list of all unconnected bumps
    # Usage: "get_unconnected_bumps [ -all | -selected (default) ]
    # When/if need another way to check bump connectivity, see "get_unconnected_bumps1.tcl"
    set ub1 [ get_unconnected_bumps1 $args ]; # Finds unconnected power bumps
    set ub2 [ get_unconnected_bumps2 $args ]; # Finds (only) unconnected signal bumps
    set ub3 []
    if { "$args" == "-all" } { 
        # Count signal nets to make sure we didn't mess up!
        # (With this extra check, probably don't actually need "get_unconnected_bumps3" anymore...)
        # (OTOH bumps3 does give dangling-wire warnings that the other don't provide)
        # select_bumpring_section 0 99 0 99 (presumably this was done already)
        set signal_nets0 [dbGet [dbGet -p selected.net.isPwrOrGnd 0].name]
        set n0 [llength $signal_nets0]
        set signal_nets1 [dbGet [dbGet -p top.bumps.net.isPwrOrGnd 0].name]
        set n1 [llength $signal_nets1]
        if { $n0 != $n1 } {
            echo "@file_info ERROR signal nets don't match, $n0 != $n1, see route-bumps.tcl"
            exit 13
        }
        set ub3 [ get_unconnected_bumps3 ]; # Check ALL the bumps
    }
    return [remove_redundant_items [concat $ub1 $ub2 $ub3]]
}
proc remove_redundant_items { L } {
    set L2 []
    foreach item $L {
        if { $item == "Net" } { continue } ; # convenient little hacky wack
        if { !($item in $L2) } { lappend L2 $item }
    }
    return $L2
}

########################################################################
# get_unconnected_bumps2 finds unconnected signal bumps
# but not so good finding unconnected power/ground bumps

proc get_unconnected_bumps2 { args } {
    # Returns a list of all unconnected / partially-connected bumps
    # Usage "get_unconnected_bumps2 [ -all | -selected (default) ]
    # FIXME/NOTE: destroys all existing markers
    # Note: -all is fast and accurate, no real need to ever use -selected (maybe?)

    # FIXME? SIDE EFFECT checks all power bump targets whether selected or not
    # E.g. flags violations for CVSS,CVDD bumps with unconnected targets

    # Save existing selections before selecting markers
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

proc check_conn_violations {subtype msg} {
    set badbumps []
    set badnets [dbGet [dbGet -p top.markers.subType $subtype].message]
    set badnets  [remove_redundant_items $badnets]
    foreach n $badnets {
        if { $badnets == 0 } { continue }
        echo "@file_info $msg $n"
        lappend badbumps [dbGet [dbGet -p2 top.bumps.net.name $n].name]
    }
    return $badbumps
}
# check_conn_violations "ConnectivityAntenna"  "WARNING found dangling net"
proc get_unconnected_bumps3 {} {
    # Possibly redundant with and better than 'get_unconnected_bumps2 -all'
    # Checks *all* nets for unconnected bumps, instead of
    # checking *preselected bumps* for unconnected nets

    # Make a list of all signal nets attached to bumps
    set signal_nets [dbGet [dbGet -p top.bumps.net.isPwrOrGnd 0].name]

    # verifyConnectivity -net pad_jtag_intf_i_phy_tck

    # Save existing selections before selecting markers!
    # Else might delete a bunch of selected bumps :o
    set save_selections [ get_db selected ]; deselect_obj -all

    # Use markers to check connecticity
    select_obj [ get_db markers ]; deleteSelectedFromFPlan
    verifyConnectivity -net $signal_nets
    dbGet top.markers.message

    set unconnected_bumps \
        [check_conn_violations "UnConnectedPin"  "ERROR found unconnected net:"]

    set open_bumps \
        [check_conn_violations "Open"  "ERROR found open net:       "]

    set dangling_bumps \
        [check_conn_violations "ConnectivityAntenna"  "WARNING found dangling net: "]

    set badbumps \
        [remove_redundant_items \
             [concat $unconnected_bumps $open_bumps]]

    # Restore saved selections
    deselect_obj -all; select_obj $save_selections

    return $badbumps
}
# final_signal_bump_check
