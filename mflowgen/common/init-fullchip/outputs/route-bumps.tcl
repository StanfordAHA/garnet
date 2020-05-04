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
}

proc route_bumps_to_rings {} {
    # Route signal bumps to pad pins, power bumps to pad rings
    # This works well, routes all bumps fairly easily

    # Easier to route signals first, then power, in each section
    # route_bumps route_sig_then_pwr

    # Better result (but slightly trickier) to route them all at once
    set_proc_verbose route_bumps_within_region; # For debugging
    route_bumps route_bumps_within_region
}
proc route_bumps_to_pads {} {
    # [DEPRECATED b/s routing to rings does so much better...]
    # Attempt to route all power bumps to power pad pins.
    # Routes all signal bumps just fine, but leaves about 65 power bumps unrouted.

    # The rdl blockages below cover the pad rings, thus forcing all
    # routes to pads. Needless to say, that makes things quite difficult.
    gen_rdl_blockages

    # In "route_bumps, use the algorithm that routes all bumps
    # within a given region before moving on to the next region
    set_proc_verbose route_bumps_within_region; # For debugging
    route_bumps route_bumps_within_region
    # FIXME lots of this kind of warnings:
    # **WARN: (IMPSR-187):    Net 'pad_tlx_fwd_tdata_hi_p_o[14]' does not have bump or pad to connect.

    # Result: "Routed 223/288 bumps, 65 remain unconnected"
    # Pretty sure that's the best we can do.

    #############################################################################
    # This (cleanup below) seems to do more harm than good so leaving off for now
    # With more time I think I could make it work and it would be helpful
    # Unrouted power bumps leave a mess; this should clean it up
    # 
    # Clean up power bumps only?
    # set rw "-routeWidth 3.6"
    # fcroute -type signal -eco -selected_bump $rw; # Clean up dangling wires etc
    # 
    # Nope, just do all of them, I think this works better
    # fcroute -type signal -eco -routeWidth 3.6;    # Clean up dangling wires etc
    #############################################################################
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

    puts "@file_info: Route bumps group 1b: left half of bottom row, 91 bumps"
    select_bumpring_section  1 6  1 19; sleep 1; $route_cmd; # rows 1-6, cols 1-ALL

    puts "@file_info: Route bumps group 2a: left center, 59 bumps"
    select_bumpring_section  7 23  1  4; sleep 1; $route_cmd; # left center

    # This overlaps prev section but maybe that's okay
    puts "@file_info: Route bumps group 2b: top left corner"
    select_bumpring_section  20 26  1  4; sleep 1; $route_cmd; # top left corner

    puts "@file_info: Skipping PHY region in top center area"
    #     puts "@file_info: Route bumps group 3: top row exc. right corner, 37 bumps"
    #     select_bumpring_section  24 99 1 22
    #     deselect_obj Bump_619.24.21; # Remove this,
    #     select_obj   Bump_673.26.23; # add that...
    #     sleep 1; $route_cmd

    puts "@file_info: Route bumps group 3: top right, 12 bumps inc. phy jtag"
    select_bumpring_section  24 99 17 22
    deselect_obj Bump_619.24.21; # Remove this,
    select_obj   Bump_673.26.23; # add that...
    sleep 1; $route_cmd

    # Top right corner is tricky b/c logo displaces a bunch of pads
    # FIXME/TODO should do this section FIRST?
    puts "@file_info: Route bumps group 4a: top right corner, 50 bumps"
    select_bumpring_section 15 99 21 99; sleep 1; $route_cmd; # top right corner

    puts "@file_info: Route bumps group 4b: right center top, 16 bumps"
    select_bumpring_section 11 14 21 99; sleep 1; $route_cmd; # right center top

    puts "@file_info: Route bumps group 4c: right center bottom, 15 bumps"
    select_bumpring_section  7 10 21 99; sleep 1; $route_cmd;  # right center bottom

    ########################################################################
    # Final check. Expect "all bumps connected (288/288)"
    select_bumpring_section 0 99 0 99
    set bumps [get_unconnected_bumps -all]
    # To see unconnected bumps highlighted in gui:
    # deselect_obj -all; select_obj $bumps
    report_unconnected_bumps $bumps; # "STILL UNCONNECTED: $bumps"
    check_all_bumps;                 # "Routed 223/288 bumps, 65 remain unconnected"

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
}

proc route_sig_then_power {} { route_sig_then_pwr }; # convenient alias
proc route_sig_then_pwr {} {
    # DEPRECATED - better to route all the bumps together
    # Bumps must already be selected before calling this proc.
    # Route signal bumps to pad pins, power bumps to pad rings.

    # Find names of nets associated with selected bumps
    get_selected_bump_nets

    # Route signal bumps FIRST b/c they're the hardest
    # (when we allow power bumps to connect to pad ring stripes).
    # Note: can add '-verbose' for debugging
    if [llength $signal_nets] {
        myfcroute -incremental -nets $signal_nets
    }
    # Now route remaining selected bumps
    echo d $power_nets
    if [llength $power_nets] {
        myfcroute -incremental -selected_bump
    }
    check_selected_bumps
}

proc route_signals {} {
    # Route signal bumps only
    # DEPRECATED - better to route all the bumps together
    # This proc currently unused as of 04/2020
    get_selected_bump_nets; # Find names of nets associated with selected bumps
    if [llength $signal_nets] { myfcroute -incremental -nets $signal_nets }
    check_selected_bumps
}
proc get_selected_bump_nets { } {
    # DEPRECATED - better to route all the bumps together
    # Bumps must already be selected before calling this proc.
    # Finds names of nets associated with the bumps
    # Via upvar, calling program can magically access nets as vars $power_nets and $signal_nets
    upvar power_nets  Lpower_nets
    upvar signal_nets Lsignal_nets

    set design_name [dbGet top.name]

    set signal_bumps [ get_db selected -if { .net != "net:$design_name/V*" } ]
    set power_bumps  [ get_db selected -if { .net == "net:$design_name/V*" } ]

    set Lsignal_nets [ get_db $signal_bumps .net.name ]
    set Lpower_nets  [ get_db $power_bumps  .net.name ]
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

############################################################################
# MAIN executable portion of script
# 
# Do e.g. "set load_but_dont_execute 1"
# to just load the procs w/o executing them;
# else do "unset load_but_dont_execute" to load and go.
if [info exists load_but_dont_execute] {
    puts "@file_info: WARNING var 'load_but_dont_execute' is set"
    puts "@file_info: WARNING loading but not executing script '[info script]'"
} else {
    # Do analog bumps FIRST I guess
    # source inputs/{route-phy-bumps,build-phy-nets}.tcl
    route_phy_bumps
    
    # [DEPRECATED]
    # This works poorly, leaves more than 60 bumps unrouted
    # set_proc_verbose route_bumps_to_pads;  # For debugging
    # route_bumps_to_pads

    # [USE THIS ONE INSTEAD]
    # This works well, routes all bumps fairly easily
    route_bumps_to_rings
}
