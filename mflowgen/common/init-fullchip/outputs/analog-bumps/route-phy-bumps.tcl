proc route_phy_bumps {} {
    set TEST 0; # Set to '1' to debug interactively w/ gui; else must be 0
    
    if {$TEST} {
        # Delete previous attempts
        editDelete -net net:pad_frame/CVDD
        editDelete -net net:pad_frame/CVSS
    }

    puts "@file_info: PHY bumps 0: add nets CVDD, CVSS etc."
    source inputs/analog-bumps/build-phy-nets.tcl
    # source ../../pad_frame/3-netlist-fixing/outputs/netlist-fixing.tcl
    # source /sim/steveri/soc/components/cgra/garnet/mflowgen/common/fc-netlist-fixing/outputs/netlist-fixing.tcl
    if {$TEST} {
        source inputs/analog-bumps/build-phy-nets.tcl
    }

    # FIXME I guess these should never have been assigned in the first place...!
    puts "@file_info: PHY bumps 0.1: remove prev bump assignments"
    foreach net {CVDD CVSS AVDD AVSS} {
        foreach bumpname [dbGet [dbGet -p2 top.bumps.net.name $net].name] { 
            if { $bumpname == 0x0 } { continue }
            echo unassignBump -byBumpName $bumpname
            unassignBump -byBumpName $bumpname
        }
    }

    puts "@file_info: PHY bumps 1: route bump S1 to CVDD"
    connect_bump *26.3 CVDD

    puts "@file_info: PHY bumps 2: route bump S2 to CVSS"
    connect_bump *26.4 CVSS "770 4800  1590 4900"
}


# Procedure for routing PHY power bump 'bump'
proc route_phy_power { bump args } {
    # FIXME should save and restore selected objects, prev flipchip mode(s)

#     # Phy bumps don't route correctly if this is false
#     # But must remember to restore it later---should be false for normal bump routing
#     setFlipChipMode -honor_bump_connect_target_constraint true


    setFlipChipMode -connectPowerCellToBump true
    setFlipChipMode -layerChangeBotLayer AP
    setFlipChipMode -layerChangeTopLayer AP
    setFlipChipMode -route_style manhattan
    setFlipChipMode -connectPowerCellToBump true

#     # Seems this is important to make sure we connect to STRIPE and not pad
#     setFlipChipMode -honor_bump_connect_target_constraint false


    # Nope for phy bump routing want this to be TRUE
    setFlipChipMode -honor_bump_connect_target_constraint true

    deselectAll; select_obj $bump; sleep 1
    setFlipChipMode -route_style 45DegreeRoute
    fcroute -type signal -selected \
        -layerChangeBotLayer AP \
        -layerChangeTopLayer AP \
        -routeWidth 30.0 \
        {*}$args

#     # False is the default maybe
#     setFlipChipMode -honor_bump_connect_target_constraint false



}

# Connect bump 'b' to net 'net'
proc connect_bump { b net args } {
    # Connect bump 'b' to net 'net'
    # Can include an optional blockage box to direct the routing
    # Examples:
    #     connect_bump *26.3 CVDD
    #     connect_bump *26.4 CVSS "770 4800  1590 4900"
    set blockage "none"; if {[llength $args]} { set blockage $args }

    set TEST 0; # Set to '1' to debug interactively w/ gui; else must be 0
    if {$TEST} {
        # Removes (all) prev routes related to $net
        editDelete -net net:pad_frame/$net

        # And/or can use this command to delete ALL RDL wires and start with a clean slate:
        # deselectAll; editSelect -layer AP; deleteSelectedFromFPlan; sleep 1

        # Cut'n' paste one of these for interactive test
        set b *26.3; set net CVDD; set blockage "none"
        set b *26.4; set net CVSS; set blockage "770 4800  1590 4900"

    }
    echo "@file_info b=$b net=$net blockage=$blockage"
    # Get targeted bump, net, pad, and blockage
    # Note we use ANAIOPAD_$net as the pad; we may want to change this at some 
    # point and e.g. route both CVDD and CVSS bumps to different ports on e.g. ANAIOPAD_CVDD
    # set b [dbGet top.bumps.name *26.3]; # Bump_653.26.3 (row 26, col 3)
    set pad ANAIOPAD_$net
    set b [dbGet top.bumps.name $b]
    echo "@file_info b=$b pad=$pad"

    # Assign the bump to the net; then
    # show flight line resulting from default assignment
    if {$TEST} { unassignBump -byBumpName $b }
    assignPGBumps -nets $net -bumps $b
    viewBumpConnection -bump $b; sleep 1

    # Find and assign more precise bump target
    findPinPortNumber -instName $pad -netName $net; # ANAIOPAD_CVDD:TACVDD:1
    set ppn [findPinPortNumber -instName $pad -netName $net]
    set pin_name [lindex [split $ppn ":"] 1]
    set port_num [lindex [split $ppn ":"] 2]
    echo addBumpConnectTargetConstraint -bump $b \
        -instName $pad \
        -pinName $pin_name \
        -portNum $port_num

    addBumpConnectTargetConstraint -bump $b \
        -instName $pad \
        -pinName $pin_name \
        -portNum $port_num

    # Verify constraint for bump $b, show new flight line
    dbGet [dbGet -p top.bumps.name $b].props.??
    viewBumpConnection -bump $b; sleep 1

    # Use optional blockage to direct the routing. Useful blocks may include
    #   "960 4670 1480 4730"    "770 4800 1630 4900"    "770 4800 1590 4900"
    if { $blockage != "none" } {
        echo create_route_blockage -layer AP -box $blockage -name temp
        create_route_blockage -layer AP -box $blockage -name temp
        redraw; sleep 1
    }

    # Route the bump, then delete temporary blockage and flightlines
    route_phy_power $b
    if { $blockage != "none" } { deleteRouteBlk -name temp }
    viewBumpConnection -remove
}

# Useful tests for proc connect_bump
if {0} {
    # Cut'n'paste for interactive testing
    deselectAll; select_obj [ get_db markers ]; deleteSelectedFromFPlan
    deselectAll; editSelect -layer AP; deleteSelectedFromFPlan; sleep 1

    unassignBump -byBumpName Bump_653.26.3
    connect_bump *26.3 CVDD
    connect_bump *26.4 CVSS "770 4800  1590 4900"
}
