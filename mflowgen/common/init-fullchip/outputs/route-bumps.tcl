# New gen_route_bumps does the following:
# - incremental bump routing instead of all at once
# - better check for routed vs. unrouted bumps

# [04.2020] To load procs w/o executing script at bottom:
if {0} {
    # Cut'n'paste for interactive debugging:
    set load_but_dont_execute 1
    source inputs/route-bumps.tcl
    # Procs needed to run these scripts:
    source inputs/stylus-compatibility-procs.tcl
    source inputs/check-bumps.tcl
    set route_cmd route_bumps_within_region; # PREFERRED!!
}

proc route_bumps_main {} {
    ######################################################################
    # MAIN executable portion of script

    # Do analog bumps FIRST I guess
    # source inputs/{route-phy-bumps,build-phy-nets}.tcl
    # route_phy_bumps
    
    # This works well, routes all bumps fairly easily
    # set_proc_verbose route_bumps_within_region; # For debugging
    route_bumps route_bumps_within_region
    ######################################################################
}

proc route_bumps { route_cmd} {
    # route_cmd options:
    # set route_cmd route_sig_then_pwr; # route sig bumps to pins, pwr bumps to rungs
    # set route_cmd route_power       ; # route power bumps to pads
    # set route_cmd route_signals     ; # route sig bumps to pins
    set route_cmd route_bumps_within_region; # PREFERRED!!

    puts "@file_info: -------------------------------------------"
    puts -nonewline "@file_info: Before rfc: Time now "; date +%H:%M
    puts "@file_info:   route_bumps - expect 20-30 min to finish"

    # If in gui, can do this to show all target bumps:
    # select_bumpring_section   0 99  0 99

    ########################################################################
    # If try to route all bumps at once, get "Too many bumps" warning.
    # Also get poor result, unrouted bumps. Thus, route in separate sections
    # Note: "sleep 1" in gui mode lets you see selected bumps while routing
    puts "@file_info:   Route bumps separately on each of the four sides"

    puts "@file_info: Route bumps group 1a: right half of bottom row, 38 bumps"
    select_bumpring_section  1 6  20 27; sleep 1; $route_cmd; # rows 1-6, cols 1-ALL

    # 05/16/2020 Move row breakpoint from 1-7 to 1-8
    puts "@file_info: Route bumps group 1b: left half of bottom row, 91 bumps"
    select_bumpring_section  1 7  1 19; sleep 1; $route_cmd; # rows 1-6, cols 1-ALL

    # 05/16/2020 Move row breakpoint from 7-23 to 8-23
    puts "@file_info: Route bumps group 2a: left center, 59 bumps"
    select_bumpring_section  8 23  1  4; sleep 1; $route_cmd; # left center

    # Seven bumps in the top left corner
    # 05/16/2020 Rows 24-26 instead of 20-26 (removed overlap w/prev)
    puts "@file_info: Route bumps group 2b: top left corner"
    select_bumpring_section  24 26  1  4; sleep 1; $route_cmd; # top left corner

    puts "@file_info: Skipping PHY region in top center area"
    #     puts "@file_info: Route bumps group 3: top row exc. right corner, 37 bumps"
    #     select_bumpring_section  24 99 1 22; deselect_obj Bump_619.24.21; select_obj   Bump_673.26.23

    # FIXME could/should insert blockage here and eliminate fix_jtag later, see 'proc fix_jtag'
    puts "@file_info: Route bumps group 3: top right, 12 bumps inc. phy jtag"
    select_bumpring_section  24 99 18 22
    # deselect_obj Bump_619.24.21; # Remove this,
    select_obj     Bump_673.26.23;   # add that (pad_ext_dump_start)...
    select_obj     Bump_647.25.23;   # and this (pad_ramp_clock maybe) 
    select_obj     Bump_648.25.24;   # and this (VSS)
    sleep 1; $route_cmd

    puts "@file_info: Route bumps group 4a: top right corner"
    select_bumpring_section 14 99 23 99; sleep 1; $route_cmd; # top right corner

    puts "@file_info: Route bumps group 4b: right center top"
    select_bumpring_section 11 13 21 99; sleep 1; $route_cmd; # right center top

    puts "@file_info: Route bumps group 4c: right center bottom, 15 bumps"
    select_bumpring_section  7 10 21 99; sleep 1; $route_cmd;  # right center bottom

    # Last minute hack: reroute JTAG bump that shorts with SJK hand routes
    puts "@file_info: Last minute hack to fix jtag routes"
    fix_jtag

    ########################################################################
    # Final check. Expect "all bumps connected (288/288)"
    select_bumpring_section 0 99 0 99
    set bumps [get_unconnected_bumps -all]
    # To see unconnected bumps highlighted in gui:
    # deselect_obj -all; select_obj $bumps
    report_unconnected_bumps $bumps; # "STILL UNCONNECTED: $bumps"
    check_all_bumps;                 # "Routed 223/288 bumps, 65 remain unconnected"

    # DONE!
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
    # Don't reroute handbuilt phy bump connections
    foreach net {CVDD CVSS AVDD AVSS} {
        foreach bumpname [dbGet [dbGet -p2 top.bumps.net.name $net].name] { 
            if { $bumpname == 0x0 } { continue }
            echo deselect_obj $bumpname
            deselect_obj $bumpname
        }
    }
    redraw; sleep 1
}

proc select_bump_ring {} {
    # [steveri 12/2019] These are all the bumps we want to route.
    # Selects edge-adjacent bumps but leaves out bumps in the middle
    # (Center bumps will get strapped to central power stripes later)
    # Examples:
    #   select_bumpring_section -1 99 0 99; # select entire ring
    #   select_bumpring_section 23 99 0 99; # select top strip
    deselect_obj -all
    deselect_bumps -bumps *
    select_bumps -type signal
    select_bumps -type power
    select_bumps -type ground
    
    # Original code:
    # this seems to have unnecessarily deleted some edge power/ground bumps
    #     # Deselect power/gnd bumps in the middle
    #     foreach bump [get_db selected] {
    #         regexp {(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
    #         if {($row>3) && ($row<24) && ($col>3) && ($col<24)} {
    #             set b "${base}${row}.${col}"
    #             deselect_bumps -bumps $b }}
    #     select_bumps -type signal

    # New code:
    # Deselect power/gnd bumps in the middle.
    # They will get strapped to central power stripes later
    # But need power-ground around edge to supply/sink io signal pads
    foreach bump [get_db selected] {
        regexp {(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
      # if {($row>3) && ($row<24) && ($col>3) && ($col<24)}
        if {($row>5) && ($row<24) && ($col>4) && ($col<23)} {
            set b "${base}${row}.${col}"
            deselect_bumps -bumps $b
        }
    }
    # If we did the above correctly, this should add nothing new
    select_bumps -type signal

    # Finally; deselect phy bumps, they get routed separately elewhere
    deselect_phy_bumps
}

proc deselect_phy_bumps {} {
    # Unselect phy bumps, they will be routed seperately elsewhere
    # This includes all bumps enclosed by rows 24-26 anc cols 5-18
    foreach bump [get_db selected] {
        regexp {(Bump_\d\d*\.)(\S*)\.(\S*)} $bump -> base row col
        if {($row>=24) && ($row<=26) && ($col>=5) && ($col<=17)} {
            set b "${base}${row}.${col}"
            deselect_bumps -bumps $b
        }
    }
    # Plus these two on row 26 cols 3 and 4
    deselect_bumps -bumps [dbGet top.bumps.name *26.3]; # CVDD
    deselect_bumps -bumps [dbGet top.bumps.name *26.4]; # CVSS
    
    # Oh and this one too
    deselect_bumps -bumps [dbGet top.bumps.name *25.4]; # CVDD
}

proc route_bumps_within_region {} {
    # Build a box around the selected bumps and route them all
    # get_selected_bump_nets;  # Find names of nets associated with selected bumps
    set a [get_bump_region]; # a= box around bumps with a bit of margin to include pads etc
    myfcroute -incremental -selected_bump -area $a -connectInsideArea
    check_selected_bumps
}
proc get_bump_region {} {
    # Confine the routes to region of selected bumps;
    # don't want paths crossing the center of the chip to get to pads on the far side!
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

    # Seems this is important to make sure we connect to STRIPE and not pad
    setFlipChipMode -honor_bump_connect_target_constraint false

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
    # redraw; # good? --no not really, didn't work
}

proc gen_rdl_blockages {} {
    # [DEPRECATED]
    # Block of pad rings so power bumps cannot connect to them;
    # designed to force bumps to attach to "official" power-pad pads.
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
proc delete_rdl_blockages {} {
    # If you need to remove the pad blockages later
    deselectAll
    select_obj [get_db route_blockages -if { .layer == "layer:RV" }]
    deleteSelectedFromFPlan
}

proc fix_jtag {} {
    # Rip up and reroute JTAG wire that otherwise
    # shorts with sjk analog phy routing

    # Clean slate
    deselectAll
    
    # Delete old routes b/c default router runs wires over PHY rdl region
    set net pad_jtag_intf_i_phy_tck; editDelete -net $net
    set net pad_jtag_intf_i_phy_tdi; editDelete -net $net

    # Insert blockage over forbidden PHY rdl region
    create_route_blockage -layer AP  -name temp -box "3125 4690  3353 4900"
    redraw; sleep 1

    # Rebuild deleted routes for tck and tdi
    # Select tck and tdi bump(s)
    set bump1 Bump_668.26.18; select_obj $bump1
    set bump2 Bump_643.25.19; select_obj $bump2

    # Build new tck and tdi routes
    viewBumpConnection -selected; sleep 1
    myfcroute -incremental -selected_bump

    # Delete blockage
    deleteRouteBlk -name temp
    viewBumpConnection -remove
}

# E.g. "set load_but_dont_execute 1" to just load procs w/o executing;
# else do "unset load_but_dont_execute" to load and go.
# set load_but_dont_execute 1
if [info exists load_but_dont_execute] {
    puts "@file_info: WARNING var 'load_but_dont_execute' is set"
    puts "@file_info: WARNING loading but not executing script '[info script]'"
} else {
    route_bumps_main
}

