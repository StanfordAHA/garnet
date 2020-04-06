# New gen_route_bumps does the following:
# - incremental bump routing instead of all at once
# - better check for routed vs. unrouted bumps

# To load procs w/o executing script at bottom:
#   set load_but_dont_execute 1
#   source inputs/route-bumps.tcl
# Procs needed to run these scripts:
#   source inputs/stylus-compatibility-procs.tcl
#   source inputs/check-bumps.tcl

proc route_bumps {} {
    puts "@file_info: -------------------------------------------"
    puts -nonewline "@file_info: Before rfc: Time now "; date +%H:%M
    puts "@file_info:   route_bumps - expect 20-30 min fo finish"

    set_fc_parms; # (defined below) connect power cells, AP layer; manhattan

    # If in gui, can do this to show all target bumps:
    # select_bumpring_section   0 99  0 99

    # If try to route all bumps at once, get "Too many bumps" warning.
    # Also get poor result, unrouted bumps. Thus, route in separate sections.

    puts "@file_info:   Route bumps as five separate groups"
    puts "@file_info:   Group 1: bottom center, 78 bumps"
    select_bumpring_section   1  5  5 22; routem; # rows 1-5, cols 5-22

    puts "@file_info: Route bumps group 2: left side, 84 bumps"
    select_bumpring_section  00 99 01 04; routem

    puts "@file_info: Route bumps group 3: top, 40 bumps"
    select_bumpring_section  24 99 05 99; routem

    puts "@file_info: Route bumps group 4: right side exc. bottom corner, 53 bumps"
    select_bumpring_section 10 23 23 99; routem

    puts "@file_info: Route bumps group 5: bottom right corner, 33 bumps"
    select_bumpring_section 1 9 23 99; routem

    # Final check. Expect "5/288 bumps unconnected"
    select_bumpring_section 0 99 0 99; check_all_bumps
    set bumps [get_unconnected_bumps -all]

    # puts "@file_info:   STILL UNCONNECTED: $bumps"
    report_unconnected_bumps $bumps

    puts -nonewline "@file_info: After rfc: Time now "; date +%H:%M
    puts "@file_info: -------------------------------------------"
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

    # sr 1912 note: orig route_flip_chip command included "-double_bend_route"
    # option, which seems to have the unfortunate side effect of turning off
    # manhattan routing and building diagonal/45-degree wires instead. So to
    # honor what seems to be the original intent, I'm turning it off.
    # Also note: diagonal routing caused drc errors later. See github issues.
    
    # route_flip_chip -incremental -target connect_bump_to_pad -verbose \
    #     -route_engine global_detail -selected_bumps \
    #     -bottom_layer AP -top_layer AP -route_width 3.6
    # #   -double_bend_route

    # Apparently this bump constraint (below) does nothing, b/c of how
    # our current design is set up; also see github garnet repo issue 462
    # addBumpConnectTargetConstraint -selected -PGConnectType iopin

    # foreach type { signal power } { fcroute... }
    # Haha the way we set things up there are no power types :(
    # See github garnet repo issue 462

    set power_bumps  [ get_db selected -if { .net == "net:pad_frame/V*" } ]
    set signal_bumps [ get_db selected -if { .net != "net:pad_frame/V*" } ]

    # echo [llength [ get_db selected ]] bumps
    # echo [llength $power_bumps]  power bumps
    # echo [llength $signal_bumps] signal bumps
    # FIXME want 'ASSERT n_bumps = n_power_bumps + n_signal_bumps'

    set signal_nets [ get_db $signal_bumps .net.name ]
    set power_nets  [ get_db $power_bumps  .net.name ]

    # Route signal bumps FIRST b/c they're the hardest
    # (when we allow power bumps to connect to pad ring stripes).
    # Note: can add '-verbose' for debugging
    fcroute -type signal \
            -incremental \
            -nets $signal_nets \
            -layerChangeBotLayer AP \
            -layerChangeTopLayer AP \
            -routeWidth 3.6

    # Now route remaining selected bumps
    fcroute -type signal \
            -incremental \
            -selected_bump \
            -layerChangeBotLayer AP \
            -layerChangeTopLayer AP \
            -routeWidth 3.6

    check_selected_bumps
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

    # Stylus vs. legacy notes for create_route_blockages
    # Stylus '-area'   == legacy '-box'
    # Stylus '-layers' == legacy '-layer'

    create_route_blockage -layer {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-box "$llx [expr $ury - $io_b1] $urx $ury"
    create_route_blockage -layer {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-box "$llx [expr $ury - $io_b3] $urx [expr $ury - $io_b2]"
    create_route_blockage -layer {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-box "$llx [expr $lly + $io_b2] $urx [expr $lly + $io_b3]"
    create_route_blockage -layer {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-box "$llx $lly $urx [expr $lly + $io_b1]"

    create_route_blockage -layer {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-box "$llx $lly [expr $llx + $io_b1] $ury"
    create_route_blockage -layer {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-box "[expr $llx + $io_b2] $lly [expr $llx + $io_b3] $ury"
    create_route_blockage -layer {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-box "[expr $urx - $io_b3] $lly [expr $urx - $io_b2] $ury"
    create_route_blockage -layer {RV M1 M2 M3 M4 M5 M6 M7 M8 M9} \
	-box "[expr $urx - $io_b1] $lly $urx $ury"

    # get_db current_design .core_bbox
    foreach bump [get_db bumps Bump*] {
	set bbox [get_db $bump .bbox]
	create_route_blockage -name rdl_$bump -layer RV \
	    -box $bbox
    }
}


# do "set load_but_dont_execute" to just load the procs
# else do "unset load_but_dont_execute" to undo that
if [info exists load_but_dont_execute] {
    # set load_but_dont_execute 1
    puts "@file_info: WARNING var 'load_but_dont_execute' is set"
    puts "@file_info: WARNING loading but not executing script '[info script]'"
} else {
    # unset load_but_dont_execute
    # source ../../scripts/gen_route_bumps_sr.tcl
    set_proc_verbose route_bumps; # For debugging
    route_bumps
}



