# New gen_route_bumps does the following:
# - incremental bump routing instead of all at once
# - better check for routed vs. unrouted bumps

proc route_bumps {} {

    # sr 1912 These blockages are causing a *lot* of problems
    # They render many/most bumps unroutable, see me for details (steveri)
    # gen_rdl_blockages
    # 
    # sr 2020-04 Restoring gen_rdl_blockages at Alex's request
    gen_rdl_blockages


    puts "@file_info: -------------------------------------------"
    puts -nonewline "@file_info: Before rfc: Time now "; date +%H:%M
    puts "@file_info:   route_bumps - expect 20-30 min fo finish"

    set_fc_parms; # (defined below) connect power cells, AP layer; manhattan

    # If in gui, can do this to show all target bumps:
    # select_bumpring_section   0 99  0 99

    # If try to route all bumps at once, get "Too many bumps" warning.
    # Also get poor result, unrouted bumps.
#--BOOKMARK--
    puts "@file_info:   Route bumps as five separate groups"
    puts "@file_info:   Group 1: bottom center, 78 bumps"
    select_bumpring_section   1  5  5 22; routem; # rows 1-5, cols 5-22

    puts "@file_info: Route bumps group 2: left side, 84 bumps"
    select_bumpring_section  00 99 01 04; routem

    puts "@file_info: Route bumps group 3: top, 40 bumps"
    puts "@file_info:   Expect five unrouted bumps b/c iphy has AP blockage (why?) (FIXME)"
    select_bumpring_section  24 99 05 99; routem

    puts "@file_info: Route bumps group 4: right side exc. bottom corner, 53 bumps"
    select_bumpring_section 10 23 23 99; routem

    puts "@file_info: Route bumps group 5: bottom right corner, 33 bumps"
    select_bumpring_section 1 9 23 99; routem

    # Final check. Expect "5/288 bumps unconnected"
    select_bumpring_section 0 99 0 99; check_all_bumps
    set bumps [get_unconnected_bumps -all]

    puts "@file_info:   STILL UNCONNECTED: $bumps"
    # Do this if you want to see the unconnected bumps highlighted in the gui
    # deselect_obj -all; select_obj $bumps

    puts -nonewline "@file_info: After rfc: Time now "; date +%H:%M
    puts "@file_info: -------------------------------------------"
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

    # Note no stylus/legacy translation needed for 'create_route_blockage'


    create_route_blockage_stylus -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx [expr $ury - $io_b1] $urx $ury"
    create_route_blockage_stylus -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx [expr $ury - $io_b3] $urx [expr $ury - $io_b2]"
    create_route_blockage_stylus -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx [expr $lly + $io_b2] $urx [expr $lly + $io_b3]"
    create_route_blockage_stylus -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx $lly $urx [expr $lly + $io_b1]"

    create_route_blockage_stylus -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "$llx $lly [expr $llx + $io_b1] $ury"
    create_route_blockage_stylus -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "[expr $llx + $io_b2] $lly [expr $llx + $io_b3] $ury"
    create_route_blockage_stylus -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "[expr $urx - $io_b3] $lly [expr $urx - $io_b2] $ury"
    create_route_blockage_stylus -layers {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-area "[expr $urx - $io_b1] $lly $urx $ury"

    # get_db current_design .core_bbox
    foreach bump [get_db bumps Bump*] {
	set bbox [get_db $bump .bbox]
	create_route_blockage_stylus -name rdl_$bump -layers RV \
	    -area $bbox
    }
}

proc set_fc_parms {} {
    # set_db flip_chip_connect_power_cell_to_bump true
    # set_db flip_chip_bottom_layer AP
    # set_db flip_chip_top_layer AP
    # set_db flip_chip_route_style manhattan 
    # set_db flip_chip_connect_power_cell_to_bump true

    # [-layerChangeBotLayer AP
    # [-layerChangeTopLayer AP
    # [-route_style {manhattan | 45DegreeRoute}]
    # [-connectPowerCellToBump {true | false}]
    setFlipChipMode -connectPowerCellToBump true
    setFlipChipMode -layerChangeBotLayer AP
    setFlipChipMode -layerChangeTopLayer AP
    setFlipChipMode -route_style manhattan
    setFlipChipMode -connectPowerCellToBump true
}

# [steveri 12/2019] This lets us select bumps one section at a time
# E.g. "select_bumpring_section 23 99 0 99 selects the top strip only
proc select_bumpring_section { rmin rmax cmin cmax } {
    select_bump_ring
    foreach bump [get_db selected] {
        # regexp {GarnetSOC_pad_frame\/(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
        regexp {pad_frame\/(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
        # puts "$row $col"
        if {
            ($row < $rmin) || ($row > $rmax) 
            ||
            ($col < $cmin) || ($col > $cmax)
        } {
            puts "deselecting $bump"
            set b "${base}${row}.${col}"
            deselect_bumps -bumps $b
        }
    }
}
# Examples:
#   select_bumpring_section -1 99 0 99; # select entire ring
#   select_bumpring_section 23 99 0 99; # select top strip

# [steveri 12/2019] These are all the bumps we want to route.
# Selects edge-adjacent bumps but leaves out bumps in the middle (why?)
proc select_bump_ring {} {
    deselect_obj -all
    deselect_bumps -bumps *
    select_bumps -type signal
    select_bumps -type power
    select_bumps -type ground
    
    # Deselect power/gnd bumps in the middle (?why?)
    foreach bump [get_db selected] {
        # regexp {GarnetSOC_pad_frame\/(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
        regexp {pad_frame\/(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
        if {($row>3) && ($row<24) && ($col>3) && ($col<24)} {
            set b "${base}${row}.${col}"
            deselect_bumps -bumps $b
        }
    }
    select_bumps -type signal
}

# (Try to) route selected bumps to their target pads
proc routem {} {
    # # set_fc_parms
    # set_db flip_chip_connect_power_cell_to_bump true
    # set_db flip_chip_bottom_layer AP
    # set_db flip_chip_top_layer AP
    # set_db flip_chip_route_style manhattan 
    # set_db flip_chip_connect_power_cell_to_bump true
    setFlipChipMode -connectPowerCellToBump true
    setFlipChipMode -layerChangeBotLayer AP
    setFlipChipMode -layerChangeTopLayer AP
    setFlipChipMode -route_style manhattan
    setFlipChipMode -connectPowerCellToBump true

  # sr 1912 note: orig route_flip_chip command included "-doubel_bend_route"
  # option, which seems to have the unfortunate side effect of turning off
  # manhattan routing and building diagonal/45-degree wires instead. So to
  # honor what seems to be the original intent, I'm turning it off.
  # Also note: diagonal routing caused drc errors later. See github issues.

  # route_flip_chip -incremental -target connect_bump_to_pad -verbose \
  #     -route_engine global_detail -selected_bumps \
  #     -bottom_layer AP -top_layer AP -route_width 3.6
  # #   -double_bend_route

    # ?right?
    addBumpConnectTargetConstraint -selected -PGConnectType iopin
    foreach type { signal power } {

        # set type signal
        # Can add '-verbose' for debugging
        fcroute -type $type \
            -incremental \
            -selected_bump \
            -layerChangeBotLayer AP \
            -layerChangeTopLayer AP \
            -routeWidth 3.6
    }
    

  check_selected_bumps
}

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
        set msg "all bumps connected ($n_connected/$n_bumps)"
    } else {
        set msg "WARNING $n_unconnected BUMPS (got $n_connected/$n_bumps)"
    }
    puts "@file_info:   - $msg"
}

# Returns a list of all unconnected bumps
# Usage "get_unconnected_bumps [ -all | -selected (default) ]
proc get_unconnected_bumps { arg } {
    if { $arg == "-all" } { select_bump_ring }

    # Find the set of all wires in the RDL layer
    set save_selected [ get_db selected ]
    deselect_obj -all
    select_routes -layer AP; set endpoints [ get_db selected .path ]
    deselect_obj -all
    select_obj $save_selected

    set ubumps {}
    foreach bump [get_db selected] {
        if { ! [ bump_connected $bump $endpoints ] } {
            lappend ubumps $bump
        }
    }
    return $ubumps
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


# source ../../scripts/gen_route_bumps_sr.tcl
set_proc_verbose route_bumps; # For debugging
route_bumps
