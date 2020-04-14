# New gen_route_bumps does the following:
# - incremental bump routing instead of all at once
# - better check for routed vs. unrouted bumps

# To load procs w/o executing script at bottom:
#   set load_but_dont_execute 1
#   source inputs/route-bumps.tcl
# Procs needed to run these scripts:
#   source inputs/stylus-compatibility-procs.tcl
#   source inputs/check-bumps.tcl

proc route_bumps_to_rings {} {
    # Route signal bumps to pad pins, power bumps to pad rings
    route_bumps route_sig_then_pwr
}

proc route_bumps_to_pads {} {
    # Attempt to route all bumps to pad pins. Routes all signal bumps
    # but leaves about 65 power bumps unrouted.

    # The rdl blockages below cover the pad rings, thus forcing all
    # routes to pads. Needless to say, that makes things quite difficult.
    gen_rdl_blockages
    route_bumps route_signals
    route_bumps route_power_to_pads
}

proc route_bumps { route_cmd} {

    # set route_cmd route_sig_then_pwr    : route sig bumps to pins, pwr bumps to rungs
    # set route_cmd route_power : route power bumps to pads
    # set route_cmd route_sigs: route sig bumps to pins

    puts "@file_info: -------------------------------------------"
    puts -nonewline "@file_info: Before rfc: Time now "; date +%H:%M
    puts "@file_info:   route_bumps - expect 20-30 min fo finish"

#     set_fc_parms; # (defined below) connect power cells, AP layer; manhattan

    # If in gui, can do this to show all target bumps:
    # select_bumpring_section   0 99  0 99

    ########################################################################
    # If try to route all bumps at once, get "Too many bumps" warning.
    # Also get poor result, unrouted bumps. Thus, route in separate sections
    puts "@file_info:   Route bumps as five separate groups"

    puts "@file_info: Route bumps group 1: entire bottom, 121 bumps"
    select_bumpring_section  1  6  1 99; $route_cmd; # rows 1-6, cols 1-ALL

    puts "@file_info: Route bumps group 2: left center, 56 bumps"
    select_bumpring_section  7 23  1  4; $route_cmd; # left center

    puts "@file_info: Route bumps group 3: top exc. right corner, 37 bumps"
    select_bumpring_section  24 99 01 22; # top exc. right corner
    deselect_obj Bump_619.24.21; # Remove this,
    select_obj   Bump_673.26.23; # add that...
    $route_cmd

    # Top right corner is tricky b/c logo displaces a bunch of pads
    # FIXME/TODO should do this section FIRST?
    puts "@file_info: Route bumps group 4a: top right corner, 48 bumps"
    select_bumpring_section 15 99 21 99; $route_cmd; # top right corner

    puts "@file_info: Route bumps group 4b: right center top, 16 bumps"
    select_bumpring_section 11 14 21 99; $route_cmd; # right center top

    puts "@file_info: Route bumps group 4c: right center bottom, 15 bumps"
    select_bumpring_section  7 10 21 99; $route_cmd;  # right center bottom

    ########################################################################
    # Clean up the dirt (unconnected/dangling nets).  Mainly needed only
    # after trying to route power bumps to pad pins, which frequently fails.
    select_bumpring_section 0 99 0 99
    fcroute -type signal -eco -selected_bump

    ########################################################################
    # Final check. Expect "all bumps connected (288/288)"
    select_bumpring_section 0 99 0 99; check_all_bumps
    set bumps [get_unconnected_bumps -all]

    # To see unconnected bumps highlighted in gui:
    # deselect_obj -all; select_obj $bumps

    report_unconnected_bumps $bumps; # "STILL UNCONNECTED: $bumps"

    puts -nonewline "@file_info: After rfc: Time now "; date +%H:%M
    puts "@file_info: -------------------------------------------"
}

# [steveri 12/2019] This lets us select bumps one section at a time
# E.g. "select_bumpring_section 23 99 0 99 selects the top strip only
proc select_bumpring_section { rmin rmax cmin cmax } {
    select_bump_ring
    foreach bump [get_db selected] {
        regexp {(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
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

proc select_bump_ring {} {
    # [steveri 12/2019] These are all the bumps we want to route.
    # Selects edge-adjacent bumps but leaves out bumps in the middle (why?)
    # Examples:
    #   select_bumpring_section -1 99 0 99; # select entire ring
    #   select_bumpring_section 23 99 0 99; # select top strip
    deselect_obj -all
    deselect_bumps -bumps *
    select_bumps -type signal
    select_bumps -type power
    select_bumps -type ground
    
    # Deselect power/gnd bumps in the middle (?why?)
    foreach bump [get_db selected] {
        regexp {(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
        if {($row>3) && ($row<24) && ($col>3) && ($col<24)} {
            set b "${base}${row}.${col}"
            deselect_bumps -bumps $b
        }
    }
    select_bumps -type signal
}
proc route_sig_then_pwr {} {
    # Route signal bumps to pad pins, power bumps to pad rings

    get_selected_bump_nets
    # Route signal bumps FIRST b/c they're the hardest
    # (when we allow power bumps to connect to pad ring stripes).
    # Note: can add '-verbose' for debugging
    if [llength $signal_nets] {
        myfcroute -incremental -nets $signal_nets
    }
    # Now route remaining selected bumps
    if [llength $power_bumps] {
        myfcroute -incremental -selected_bump
    }
    check_selected_bumps
}

proc route_sigs {} {
    get_selected_bump_nets
    if [llength $signal_nets] {
        myfcroute -incremental -nets $signal_nets
    }
    check_selected_bumps
}
proc route_power {} {
    get_selected_bump_nets
    set a [get_bump_region]

    myfcroute -incremental -selected_bump -area $a -connectInsideArea
    check_selected_bumps
}

proc get_selected_bump_nets { } {
    set design_name [dbGet top.name]

    set signal_bumps [ get_db selected -if { .net != "net:$design_name/V*" } ]
    set power_bumps  [ get_db selected -if { .net == "net:$design_name/V*" } ]

    set Lsignal_nets [ get_db $signal_bumps .net.name ]
    set Lpower_nets  [ get_db $power_bumps  .net.name ]

    upvar power_nets  Lpower_nets
    upvar signal_nets Lsignal_nets
}


proc myfcroute { args } {
    # STYLUS
    # set_db flip_chip_connect_power_cell_to_bump true
    # set_db flip_chip_bottom_layer AP
    # set_db flip_chip_top_layer AP
    # set_db flip_chip_route_style manhattan 
    # set_db flip_chip_connect_power_cell_to_bump true

    # LEGACY
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
    
    # Apparently this bump constraint (below) does nothing, b/c of how
    # our current design is set up; also see github garnet repo issue 462
    # addBumpConnectTargetConstraint -selected -PGConnectType iopin

    # FIXME apparently all our bumps are "-type signal"
    # including power bumps---why???
    # See github garnet repo issue 462
    fcroute -type signal \
        -layerChangeBotLayer AP \
        -layerChangeTopLayer AP \
        -routeWidth 3.6 \
        {*}$args
}

# proc set_fc_parms {} {
# }

proc get_bump_region {} {
    # Confine the routes to region of selected bumps;
    # don't want RDL crossing the center of the chip to other side!
    set xmin [tcl::mathfunc::min {*}[get_db selected .bbox.ll.x]]
    set xmax [tcl::mathfunc::max {*}[get_db selected .bbox.ur.x]]
    set ymin [tcl::mathfunc::min {*}[get_db selected .bbox.ll.y]]
    set ymax [tcl::mathfunc::max {*}[get_db selected .bbox.ur.y]]
    
    # Add 250u margin to enclose nearby pads else how will it route?
    set xmin [expr $xmin - 250]
    set xmax [expr $xmax + 250]
    set ymin [expr $ymin - 250]
    set ymax [expr $ymax + 250]
    echo "$xmin $ymin -- $xmax $ymax"
    return "$xmin $ymin $xmax $ymax"
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
    # Set this to "pads" or "rings"
    set power_bump_target rings

    if { $power_bump_target == "rings" } {
        # This works well, routes all bumps fairly easily
        set_proc_verbose route_bumps_to_rings; # For debugging
        route_bumps_to_rings
    } else {
        # This works poorly, leaves more than 60 bumps unrouted
        set_proc_verbose route_bumps_to_pads;  # For debugging
        route_bumps_to_pads
}
