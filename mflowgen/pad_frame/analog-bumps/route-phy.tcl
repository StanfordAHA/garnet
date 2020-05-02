proc route_phy_power { bump args } {
    # FIXME should save and restore selected objects, prev flipchip mode(s)

    # Seems like a good idea to do this, even though it
    # seems to work the same regardless of true or false
    setFlipChipMode -honor_bump_connect_target_constraint true

    deselectAll; select_obj $bump; sleep 1
    setFlipChipMode -route_style 45DegreeRoute
    fcroute -type signal -selected \
        -layerChangeBotLayer AP \
        -layerChangeTopLayer AP \
        -routeWidth 30.0 \
        {*}$args
}

########################################################################
# 1. Route bump S1 to CVDD
set TEST 1; # Set to '1' to debug interactively with gui

# Targeted bump, net, and pad
set b [dbGet top.bumps.name *26.3]; # Bump_653.26.3 (row 26, col 3)
set net CVDD; set pad ANAIOPAD_$net

# Assign the bump to the net
if {$TEST} {unassignBump -byBumpName $b}
assignPGBumps -nets $net -bumps $b
if {$TEST} {
    # Show default connection resulting from default assignment
    viewBumpConnection -bump $b; sleep 1
}

# YES need this constraint (new)
findPinPortNumber -instName $pad -netName $net
# ANAIOPAD_CVDD:TACVDD:1
set ppn [findPinPortNumber -instName $pad -netName $net]
set pin_name [lindex [split $ppn ":"] 1]
set port_num [lindex [split $ppn ":"] 2]
addBumpConnectTargetConstraint -bump $b \
    -instName $pad \
    -pinName $pin_name \
    -portNum $port_num
# Verify constraint for bump $b, new flight line
if {$TEST} {
    dbGet [dbGet -p top.bumps.name $b].props.??
    viewBumpConnection -bump $b; sleep 1
}
# Delete prev routes and nets if desired
if {$TEST}{
    # BEWARE! This deletes all RDL wires throughout the entire chip
    deselectAll; editSelect -layer AP; deleteSelectedFromFPlan

    # OR use this to surgically remove only wires related to target net
    editDelete -net net:pad_frame/$net
}

# Might be good to keep these blockages in our back pocket just in case
# Can optionally use blockages to help direct the routing
# create_route_blockage -layer AP -box "960 4670  1480 4730" -name temp
# create_route_blockage -layer AP -box "770 4800  1630 4900" -name temp; redraw
# create_route_blockage -layer AP -box "770 4800  1590 4900" -name temp; redraw; sleep 1

# deselectAll; select_obj $b
# route_phy_power -selected_bump
route_phy_power $b
# deleteRouteBlk -name temp

########################################################################
# 2. Route bump S2 to CVSS
# set TEST 1; # Set to '1' to debug interactively with gui

# Targeted bump, net, and pad
set b [dbGet top.bumps.name *26.4]; # Bump_654.26.4 (row 26, col 4)
set net CVSS; set pad ANAIOPAD_$net

# Assign the bump to the net
if {$TEST} {unassignBump -byBumpName $b}
assignPGBumps -nets $net -bumps $b
if {$TEST} {
    # Show default connection resulting from default assignment
    viewBumpConnection -bump $b; sleep 1
}

# YES need this constraint (new)
findPinPortNumber -instName $pad -netName $net
# ANAIOPAD_CVDD:TACVDD:1
set ppn [findPinPortNumber -instName $pad -netName $net]
set pin_name [lindex [split $ppn ":"] 1]
set port_num [lindex [split $ppn ":"] 2]
addBumpConnectTargetConstraint -bump $b \
    -instName $pad \
    -pinName $pin_name \
    -portNum $port_num
# Verify constraint for bump $b, new flight line
if {$TEST} {
    dbGet [dbGet -p top.bumps.name $b].props.??
    viewBumpConnection -bump $b; sleep 1
}
# Delete prev routes and nets if desired
if {$TEST}{
    # BEWARE! This deletes all RDL wires throughout the entire chip
    deselectAll; editSelect -layer AP; deleteSelectedFromFPlan

    # OR use this to surgically remove only wires related to target net
    editDelete -net net:pad_frame/$net
}

# Can optionally use blockages to help direct the routing
deleteRouteBlk -name temp
create_route_blockage -layer AP -box "770 4800 1630 4900" -name temp; redraw; sleep 1
# ... route_phy_power ... deleteRouteBlk -name temp

# deselectAll
# set net CVSS; set b Bump_654.26.4; select_obj $b
# unassignBump -byBumpName $b
# assignPGBumps -nets $net -bumps $b
# viewBumpConnection -bump $b; sleep 1

route_phy_power $b
deleteRouteBlk -name temp

