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

    set ring_info [add_power_rings]
    add_stripes_from_pads_to_rings $ring_info
    route_signal_bumps
    # route_power_bumps

    ######################################################################
}

proc add_power_rings {} {
    # set the ring parameters
    # ring width: maximum width of the layer
    # ring spacing: 2x the minimum spacing of the layer
    set ring_layer gm0
    set ring_width [dbGet [dbGet -p head.layers.name $ring_layer].maxWidth]
    set ring_spacing [expr 2 * [dbGet [dbGet -p head.layers.name $ring_layer].minSpacing]]
    
    # # obtain the pads object on each side
    # set pads_top    [dbGet top.insts.name IOPAD_top*]
    # set pads_bottom [dbGet top.insts.name IOPAD_bottom*]
    # set pads_left   [dbGet top.insts.name IOPAD_left*]
    # set pads_right  [dbGet top.insts.name IOPAD_right*]
    # # compute the max/min x location of the top/bottom pads
    # # this values are used to compute the ring offset on left/right
    # set min_x 9999
    # set max_x 0
    # foreach obj [concat $pads_top $pads_bottom] {
    #     set pad_obj [dbGet -p top.insts.name $obj]
    #     set pad_llx [dbGet $pad_obj.box_llx]
    #     set pad_urx [dbGet $pad_obj.box_urx]
    #     if { $pad_llx < $min_x } {
    #         set min_x $pad_llx
    #     }
    #     if { $pad_urx > $max_x } {
    #         set max_x $pad_urx
    #     }
    # }
    # # compute the max/min y location of the left/right pads
    # # this values are used to compute the ring offset on top/bottom
    # set min_y 9999
    # set max_y 0
    # foreach obj [concat $pads_left $pads_right] {
    #     set pad_obj [dbGet -p top.insts.name $obj]
    #     set pad_lly [dbGet $pad_obj.box_lly]
    #     set pad_ury [dbGet $pad_obj.box_ury]
    #     if { $pad_lly < $min_y } {
    #         set min_y $pad_lly
    #     }
    #     if { $pad_ury > $max_y } {
    #         set max_y $pad_ury
    #     }
    # }
    # # compute the offset of the rings
    # # we have 3 rings (VDDPST, VSS, VDD), so we need to deduct 3 ring width and 2 ring spacing
    # set core_box_llx [dbGet top.fPlan.coreBox_llx]
    # set core_box_lly [dbGet top.fPlan.coreBox_lly]
    # set core_box_urx [dbGet top.fPlan.coreBox_urx]
    # set core_box_ury [dbGet top.fPlan.coreBox_ury]
    # set offset_top    [expr ($core_box_ury - $max_y) - (3 * $ring_width) - (2 * $ring_spacing)]
    # set offset_bottom [expr ($min_y - $core_box_lly) - (3 * $ring_width) - (2 * $ring_spacing)]
    # set offset_left   [expr ($min_x - $core_box_llx) - (3 * $ring_width) - (2 * $ring_spacing)]
    # set offset_right  [expr ($core_box_urx - $max_x) - (3 * $ring_width) - (2 * $ring_spacing)]

    set offset_top    40.0
    set offset_bottom 40.0
    set offset_left   44.0
    set offset_right  44.0

    # Create the rings
    # Note that we are creating rings inside the core, so we need to make the offset negative values
    # TODO: Do we need to snap the ring wires to the grid?
    #       -snap_wire_center_to_grid None | Grid | Half_Grid | Either
    addRing \
        -nets {VDDPST VSS VDD} \
        -layer $ring_layer \
        -width $ring_width \
        -spacing $ring_spacing \
        -offset "top -$offset_top bottom -$offset_bottom left -$offset_left right -$offset_right"
    
    # will be used to create the stripes
    return [list $ring_width $ring_spacing $offset_top $offset_bottom $offset_left $offset_right]
}

proc get_pad_shape_bound { pad_module_name pad_pin_name x_or_y min_or_max } {
    set pad_obj [dbGet -p head.allCells.name $pad_module_name]
    set pin_obj [dbGet -p $pad_obj.pgTerms.name $pad_pin_name]
    if {$x_or_y eq "x"} {
        set collection [concat [dbGet $pin_obj.pins.allShapes.shapes.rect_llx] \
                               [dbGet $pin_obj.pins.allShapes.shapes.rect_urx]]
    } elseif {$x_or_y eq "y"} {
        set collection [concat [dbGet $pin_obj.pins.allShapes.shapes.rect_lly] \
                               [dbGet $pin_obj.pins.allShapes.shapes.rect_ury]]
    } else {
        puts "Invalid selection"
    }
    
    set collection [lsort -real $collection]
    set max_value [lindex $collection end]
    set min_value [lindex $collection 0]

    if {$min_or_max eq "min"} {
        set value $min_value
    } elseif {$min_or_max eq "max"} {
        set value $max_value
    } else {
        set value "Invalid"
    }
    return $value
}

proc add_stripes_from_pads_to_rings { ring_info } {
    # Add power stripes to connect the power rails
    # in the pads to the power ring:
    #
    #  power  -----------------X----- vcc
    #  rings  -----------X-----|----- vss
    #         ------X----|-----|----- vccio
    #               |    |     |                            
    #               |    |     |               
    #   IO    ------|----|-----X----- vcc
    #   Pad   ------|----X----------- vss
    #   Rings ------X----|----------- vccio
    #         ------|----X----------- vss
    #         ------X----|----------- vccio
    #         ------|----X----------- vss
    #         ------X----|----------- vccio
    #         ------|----X----------- vss
    #         ------X---------------- vccio
    set ring_width         [lindex $ring_info 0]
    set ring_spacing       [lindex $ring_info 1]
    set ring_offset_top    [lindex $ring_info 2]
    set ring_offset_bottom [lindex $ring_info 3]
    set ring_offset_left   [lindex $ring_info 4]
    set ring_offset_right  [lindex $ring_info 5]
    
    set stripe_layer gmb

    foreach side {top bottom left right} {
        set pad_objs [dbGet -p top.insts.name IOPAD_$side*]
        foreach pad_obj $pad_objs {
            set pad_inst_name [dbGet $pad_obj.name]
            set pad_cell_name [dbGet $pad_obj.cell.name]
            set pad_box_llx [dbGet $pad_obj.box_llx]
            set pad_box_lly [dbGet $pad_obj.box_lly]
            set pad_box_urx [dbGet $pad_obj.box_urx]
            set pad_box_ury [dbGet $pad_obj.box_ury]
            set i 0
            foreach pwr_io { vccio vss* vcc } {
                if {$side eq "top"} {
                    set port_bound [get_pad_shape_bound $pad_cell_name $pwr_io y max]
                    set sbox_llx [expr $pad_box_llx]
                    set sbox_lly [expr $pad_box_lly - $ring_offset_top - ($i+1)*$ring_width - $i*$ring_spacing]
                    set sbox_urx [expr $pad_box_urx]
                    set sbox_ury [expr $pad_box_lly + $port_bound]
                    set stripe_direction "vertical"
                    set pad_length [dbGet $pad_obj.box_sizex]
                } elseif {$side eq "bottom"} {
                    set port_bound [get_pad_shape_bound $pad_cell_name $pwr_io y max]
                    set sbox_llx [expr $pad_box_llx]
                    set sbox_lly [expr $pad_box_ury - $port_bound]
                    set sbox_urx [expr $pad_box_urx]
                    set sbox_ury [expr $pad_box_ury + $ring_offset_bottom + ($i+1)*$ring_width + $i*$ring_spacing]
                    set stripe_direction "vertical"
                    set pad_length [dbGet $pad_obj.box_sizex]
                } elseif {$side eq "left"} {
                    set port_bound [get_pad_shape_bound $pad_cell_name $pwr_io x min]
                    set sbox_llx [expr $pad_box_llx + $port_bound]
                    set sbox_lly [expr $pad_box_lly]
                    set sbox_urx [expr $pad_box_urx + $ring_offset_left + ($i+1)*$ring_width + $i*$ring_spacing]
                    set sbox_ury [expr $pad_box_ury]
                    set stripe_direction "horizontal"
                    set pad_length [dbGet $pad_obj.box_sizey]
                } elseif {$side eq "right"} {
                    set port_bound [get_pad_shape_bound $pad_cell_name $pwr_io x min]
                    set sbox_llx [expr $pad_box_llx - $ring_offset_right - ($i+1)*$ring_width - $i*$ring_spacing]
                    set sbox_lly [expr $pad_box_lly]
                    set sbox_urx [expr $pad_box_urx - $port_bound]
                    set sbox_ury [expr $pad_box_ury]
                    set stripe_direction "horizontal"
                    set pad_length [dbGet $pad_obj.box_sizey]
                }
                # compute the stripe net
                if {$pwr_io eq "vccio"} {
                    set stripe_net VDDPST
                } elseif {$pwr_io eq "vss*"} {
                    set stripe_net VSS
                } elseif {$pwr_io eq "vcc"} {
                    set stripe_net VDD
                }
                # compute the stripe width and offset
                if {[string match "*SUPPLY*" $pad_inst_name]} {
                    set stripe_width [expr 2 * [dbGet [dbGet -p head.layers.name $stripe_layer].maxWidth] / 3]
                    set interval [expr $pad_length / 4]
                    set stripe_offset [expr ($i+1)*($interval) - ($stripe_width/2)]
                } else {
                    set stripe_width [expr [dbGet [dbGet -p head.layers.name $stripe_layer].maxWidth] / 3]
                    set interval [expr $pad_length / 5]
                    if {$pwr_io eq "vccio"} {
                        set stripe_offset [expr ($i+1)*($interval) - ($stripe_width/2)]
                    } else {
                        set stripe_offset [expr ($i+1)*($interval) - ($stripe_width/2) + $interval]
                    }
                }
                # add the stripe
                addStripe \
                    -area "$sbox_llx $sbox_lly $sbox_urx $sbox_ury" \
                    -direction $stripe_direction \
                    -layer $stripe_layer \
                    -nets $stripe_net \
                    -width $stripe_width \
                    -start_offset $stripe_offset \
                    -number_of_sets 1
                # advanced to the next power net
                incr i
            }
        }
    }
}

proc select_signal_bumps_within { area } {
    deselect_bump
    select_bump -area $area -type signal
    deselect_bump -floating
}

proc route_signal_bumps {} {

    # fcroute configuration
    setFlipChipMode -reset
    setFlipChipMode -layerChangeTopLayer                  gmb
    setFlipChipMode -layerChangeBotLayer                  gm0
    setFlipChipMode -routeWidth                           4.0
    setFlipChipMode -route_style                          manhattan
    setFlipChipMode -allow_layer_change                   true
    setFlipChipMode -connectPowerCellToBump               true
    setFlipChipMode -honor_bump_connect_target_constraint true
    setFlipChipMode -prevent_via_under_bump               true

    # select a portion of the signal bumps
    select_signal_bumps_within {0 0 1000 1000}
    set bump_route_area [get_bump_region];
    fcroute -type signal -incremental -selected_bump -area $bump_route_area -connectInsideArea
}

proc route_bumps { route_cmd } {
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

    puts "@file_info: Route bumps group 3: top middle, 39 bumps"
    select_bumpring_section  24 99 5 17; sleep 1; $route_cmd;

    puts "@file_info: Route bumps group 3: top right, 12 bumps"
    select_bumpring_section  24 99 18 22; sleep 1; $route_cmd

    puts "@file_info: Route bumps group 4a: top right corner"
    select_bumpring_section 14 99 23 99; sleep 1; $route_cmd; # top right corner

    puts "@file_info: Route bumps group 4b: right center top"
    select_bumpring_section 11 13 21 99; sleep 1; $route_cmd; # right center top

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
    setFlipChipMode -layerChangeBotLayer LB
    setFlipChipMode -layerChangeTopLayer LB
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
        -layerChangeBotLayer LB \
        -layerChangeTopLayer LB \
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

