proc route_bumps_main {} {
    # 0. power ring info
    set pwr_ring_layer_obj     [dbGet -p head.layers.name gm0]
    set pwr_ring_width         [dbGet $pwr_ring_layer_obj.maxWidth]
    set pwr_ring_spacing       [expr 2 * [dbGet $pwr_ring_layer_obj.minSpacing]]
    set pwr_ring_offset_top    40.0
    set pwr_ring_offset_bottom 40.0
    set pwr_ring_offset_left   44.0
    set pwr_ring_offset_right  44.0
    set pwr_ring_info          [list $pwr_ring_width \
                                     $pwr_ring_spacing \
                                     $pwr_ring_offset_top \
                                     $pwr_ring_offset_bottom \
                                     $pwr_ring_offset_left \
                                     $pwr_ring_offset_right]



    # 0. disable nanoroute/viagen mode first
    # setNanoRouteMode -reset
    # setViaGenMode -reset

    # 1. add routing guide
    add_signal_route_blockage_on_pads $pwr_ring_info

    # 2. route signal bumps
    # route_signal_bumps

    # 3. create power ring
    add_power_rings $pwr_ring_info

    # 4. connect pads to ring with stripes
    add_stripes_from_pads_to_rings $pwr_ring_info

    # 4.1 Some stripes may be blocked by the snacky signal routes
    #     There is no good solution at this point
    #     So just trim the dangling stripes
    # editTrim 

    # 5. route power bumps
    # route_power_bumps

    # 6. remove the temporary obstruction in the IO pads
    # delete route blockage
}

proc add_signal_route_blockage_on_pads { ring_info } {
    # Add routing blockage on the pads to form a signal route channel
    # This can prevent the signal route into the reserved area for power routing
    # --- well, guess what?
    #     Innovus fcroute will break through the blockage!
    #     What can you do? No, nothing you can do. Maybe cry.

    set vert_pitch         [dbGet top.fPlan.coreSite.size_y]
    set hori_pitch         [dbGet top.fPlan.coreSite.size_x]
    set ring_width         [lindex $ring_info 0]
    set ring_spacing       [lindex $ring_info 1]
    # ring offset is relative to the core box
    # but here we need to compute the offset relative to the pads
    # and there is a small pitch gap between the pads and the core box
    # (this is defined in the floorplan.tcl)
    set ring_offset_top    [expr [lindex $ring_info 2] + 2 * $vert_pitch]
    set ring_offset_bottom [expr [lindex $ring_info 3] + 2 * $vert_pitch]
    set ring_offset_left   [expr [lindex $ring_info 4] + 8 * $hori_pitch]
    set ring_offset_right  [expr [lindex $ring_info 5] + 8 * $hori_pitch]

    foreach side {top bottom left right} {
        set pad_objs [dbGet -p top.insts.name IOPAD_$side*]
        foreach pad_obj $pad_objs {
            set pad_inst_name [dbGet $pad_obj.name]
            set pad_cell_name [dbGet $pad_obj.cell.name]
            set pad_llx [dbGet $pad_obj.box_llx]
            set pad_lly [dbGet $pad_obj.box_lly]
            set pad_urx [dbGet $pad_obj.box_urx]
            set pad_ury [dbGet $pad_obj.box_ury]
            set sbox_llx $pad_llx
            set sbox_lly $pad_lly
            set sbox_urx $pad_urx
            set sbox_ury $pad_ury
            if {$side eq "top"} {
                set sbox_lly [expr $sbox_lly - $ring_offset_top - 3*$ring_width - 2*$ring_spacing]
                set stripe_direction "vertical"
                set pad_length [dbGet $pad_obj.box_sizex]
            } elseif {$side eq "bottom"} {
                set sbox_ury [expr $sbox_ury + $ring_offset_bottom + 3*$ring_width + 2*$ring_spacing]
                set stripe_direction "vertical"
                set pad_length [dbGet $pad_obj.box_sizex]
            } elseif {$side eq "left"} {
                set sbox_urx [expr $sbox_urx + $ring_offset_left + 3*$ring_width + 2*$ring_spacing]
                set stripe_direction "horizontal"
                set pad_length [dbGet $pad_obj.box_sizey]
            } elseif {$side eq "right"} {
                set sbox_llx [expr $sbox_llx - $ring_offset_right - 3*$ring_width - 2*$ring_spacing]
                set stripe_direction "horizontal"
                set pad_length [dbGet $pad_obj.box_sizey]
            }
            # compute the stripe width and offset
            if {[string match "*SUPPLY*" $pad_inst_name]} {
                # SUPPLY pad: one block the whole pad + the ring region
                createRouteBlk \
                    -layer gmb \
                    -box "$sbox_llx $sbox_lly $sbox_urx $sbox_ury" \
                    -exceptpgnet
            } else {
                # SIGNAL pad: 2 blocks and a channel sandwidched in between
                if {$side eq "top" || $side eq "bottom"} {
                    set sbox_a_llx $sbox_llx
                    set sbox_a_lly $sbox_lly
                    set sbox_a_urx [expr $sbox_llx + 2*8 + 1.3 + 1.0]
                    set sbox_a_ury $sbox_ury
                    createRouteBlk \
                        -layer gmb \
                        -box "$sbox_a_llx $sbox_a_lly $sbox_a_urx $sbox_a_ury" \
                        -exceptpgnet
                    set sbox_b_llx [expr $sbox_urx - 12.0 - 1.0]
                    set sbox_b_lly $sbox_lly
                    set sbox_b_urx $sbox_urx
                    set sbox_b_ury $sbox_ury
                    createRouteBlk \
                        -layer gmb \
                        -box "$sbox_b_llx $sbox_b_lly $sbox_b_urx $sbox_b_ury" \
                        -exceptpgnet
                } elseif {$side eq "left" || $side eq "right"} {
                    set sbox_a_llx $sbox_llx
                    set sbox_a_lly $sbox_lly
                    set sbox_a_urx $sbox_urx
                    set sbox_a_ury [expr $sbox_lly + 2*8 + 2.47 + 1.0]
                    createRouteBlk \
                        -layer gmb \
                        -box "$sbox_a_llx $sbox_a_lly $sbox_a_urx $sbox_a_ury" \
                        -exceptpgnet
                    set sbox_b_llx $sbox_llx
                    set sbox_b_lly [expr $sbox_ury - 12.0 - 1.0]
                    set sbox_b_urx $sbox_urx
                    set sbox_b_ury $sbox_ury
                    createRouteBlk \
                        -layer gmb \
                        -box "$sbox_b_llx $sbox_b_lly $sbox_b_urx $sbox_b_ury" \
                        -exceptpgnet
                }
            }
        }
    }
}

proc select_bumps_within { area type } {
    deselect_bump
    select_bump -area $area -type $type
    deselect_bump -floating
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

proc route_signal_bumps {} {

    # fcroute configuration (manhattan, 45DegreeRoute)
    setFlipChipMode -reset
    setFlipChipMode -layerChangeTopLayer                  gmb
    setFlipChipMode -layerChangeBotLayer                  gm0
    setFlipChipMode -routeWidth                           4.00
    setFlipChipMode -route_style                          manhattan
    setViaGenMode   -invoke_verifyGeometry                false
    # setFlipChipMode -connectPowerCellToBump             true
    setFlipChipMode -honor_bump_connect_target_constraint true
    setFlipChipMode -ignore_pad_type_check                true
    # setFlipChipMode -prevent_via_under_bump             true
    setFlipChipMode -lower_layer_prevent_45_routing       true
    setFlipChipMode -allow_layer_change                   true
    setSrouteMode   -allowWrongWayRoute                   true

    # select a portion of the signal bumps
    set bump_select_regions {}
    # only do routes in top/bottom for now
    lappend bump_select_regions {0 0 4000 500}
    lappend bump_select_regions {100 3680 3800 4000}
    lappend bump_select_regions {0 330 420 3800}
    lappend bump_select_regions {3500 330 4000 3500}
    foreach region $bump_select_regions {
        select_bumps_within $region signal
        set bump_route_area [get_bump_region]
        fcroute \
            -type signal \
            -incremental \
            -selected_bump \
            -area $bump_route_area \
            -connectInsideArea \
            -verbose
    }
    fillNotch
}

proc add_power_rings { ring_info } {

    set vert_pitch         [dbGet top.fPlan.coreSite.size_y]
    set hori_pitch         [dbGet top.fPlan.coreSite.size_x]
    set ring_layer         gm0
    set ring_width         [lindex $ring_info 0]
    set ring_spacing       [lindex $ring_info 1]
    set ring_offset_top    [lindex $ring_info 2]
    set ring_offset_bottom [lindex $ring_info 3]
    set ring_offset_left   [lindex $ring_info 4]
    set ring_offset_right  [lindex $ring_info 5]

    # Create the rings
    # Note that we are creating rings inside the core, so we need to make the offset negative values
    # TODO: Do we need to snap the ring wires to the grid?
    #       -snap_wire_center_to_grid None | Grid | Half_Grid | Either
    addRing \
        -nets {VSS VDDPST VDD} \
        -layer $ring_layer \
        -width $ring_width \
        -spacing $ring_spacing \
        -offset "top -$ring_offset_top bottom -$ring_offset_bottom left -$ring_offset_left right -$ring_offset_right"
}

proc add_stripes_from_pads_to_rings { ring_info } {
    # Add power stripes to connect the power rails
    # in the pads to the power ring:
    set vert_pitch [dbGet top.fPlan.coreSite.size_y]
    set hori_pitch [dbGet top.fPlan.coreSite.size_x]

    set ring_width         [lindex $ring_info 0]
    set ring_spacing       [lindex $ring_info 1]
    # ring offset is relative to the core box
    # but here we need to compute the offset relative to the pads
    # and there is a small pitch gap between the pads and the core box
    # (this is defined in the floorplan.tcl)
    set ring_offset_top    [expr [lindex $ring_info 2] + 2 * $vert_pitch]
    set ring_offset_bottom [expr [lindex $ring_info 3] + 2 * $vert_pitch]
    set ring_offset_left   [expr [lindex $ring_info 4] + 8 * $hori_pitch]
    set ring_offset_right  [expr [lindex $ring_info 5] + 8 * $hori_pitch]
    foreach side {top bottom left right} {
        set pad_objs [dbGet -p top.insts.name IOPAD_$side*]
        foreach pad_obj $pad_objs {
            set pad_inst_name [dbGet $pad_obj.name]
            set pad_cell_name [dbGet $pad_obj.cell.name]
            set pad_llx [dbGet $pad_obj.box_llx]
            set pad_lly [dbGet $pad_obj.box_lly]
            set pad_urx [dbGet $pad_obj.box_urx]
            set pad_ury [dbGet $pad_obj.box_ury]
            set i 0
            foreach pwr_io { vss* vccio vcc } {
                set sbox_llx $pad_llx
                set sbox_lly $pad_lly
                set sbox_urx $pad_urx
                set sbox_ury $pad_ury
                if {$side eq "top"} {
                    set sbox_lly [expr $sbox_lly - $ring_offset_top - ($i+1)*$ring_width - $i*$ring_spacing]
                    set stripe_direction "vertical"
                    set pad_length [dbGet $pad_obj.box_sizex]
                } elseif {$side eq "bottom"} {
                    set sbox_ury [expr $sbox_ury + $ring_offset_bottom + ($i+1)*$ring_width + $i*$ring_spacing]
                    set stripe_direction "vertical"
                    set pad_length [dbGet $pad_obj.box_sizex]
                } elseif {$side eq "left"} {
                    set sbox_urx [expr $sbox_urx + $ring_offset_left + ($i+1)*$ring_width + $i*$ring_spacing]
                    set stripe_direction "horizontal"
                    set pad_length [dbGet $pad_obj.box_sizey]
                } elseif {$side eq "right"} {
                    set sbox_llx [expr $sbox_llx - $ring_offset_right - ($i+1)*$ring_width - $i*$ring_spacing]
                    set stripe_direction "horizontal"
                    set pad_length [dbGet $pad_obj.box_sizey]
                }
                # compute the stripe width and offset
                if {[string match "*SUPPLY*" $pad_inst_name]} {
                    # SUPPLY pad
                    if {$pwr_io eq "vss*"} {
                        set stripe_net VSS
                    } elseif {$pwr_io eq "vccio"} {
                        set stripe_net VDDPST
                    } elseif {$pwr_io eq "vcc"} {
                        set stripe_net VDD
                    }
                    # based on i, compute the offset
                    set stripe_width 12.0
                    set space [expr ($pad_length - $stripe_width*3) / 2]
                    set stripe_offset [expr $i*($space + $stripe_width)]
                } else {
                    # SIGNAL pad
                    set param_vss_stripe_width 8.0
                    set param_vcc_stripe_width 12.0
                    if {$side eq "top" || $side eq "bottom"} {
                        set param_space 1.3
                    } elseif {$side eq "left" || $side eq "right"} {
                        set param_space 2.47
                    }
                    if {$pwr_io eq "vss*"} {
                        set stripe_net VSS
                        set stripe_width 8.0
                        set stripe_offset 0
                    } elseif {$pwr_io eq "vccio"} {
                        set stripe_net VDDPST
                        set stripe_width 8.0
                        set stripe_offset [expr $param_vss_stripe_width + $param_space]
                    } elseif {$pwr_io eq "vcc"} {
                        set stripe_net VDD
                        set stripe_width 12.0
                        set stripe_offset [expr $pad_length - $param_vcc_stripe_width]
                    }
                }
                
                # add the stripe
                addStripe \
                    -area "$sbox_llx $sbox_lly $sbox_urx $sbox_ury" \
                    -direction $stripe_direction \
                    -layer gmb \
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

proc route_power_bumps {} {

    # fcroute configuration
    setFlipChipMode -reset
    setFlipChipMode -layerChangeTopLayer                  gmb
    setFlipChipMode -layerChangeBotLayer                  gm0
    setFlipChipMode -routeWidth                           4.00
    setFlipChipMode -route_style                          45DegreeRoute
    setFlipChipMode -honor_bump_connect_target_constraint true
    setFlipChipMode -ignore_pad_type_check                true
    setFlipChipMode -lower_layer_prevent_45_routing       true
    setFlipChipMode -allow_layer_change                   true
    setSrouteMode   -allowWrongWayRoute                   true

    # route power bumps to ring
    deselect_bump
    select_bump -area {380 370 3630 520} -type ground
    select_bump -area {380 370 3630 520} -type power
    deselect_bump -floating
    set xmin [tcl::mathfunc::min {*}[get_db selected .bbox.ll.x]]
    set xmax [tcl::mathfunc::max {*}[get_db selected .bbox.ur.x]]
    set ymin [tcl::mathfunc::min {*}[get_db selected .bbox.ll.y]]
    set ymax [tcl::mathfunc::max {*}[get_db selected .bbox.ur.y]]
    set xmin [expr $xmin - 100]
    set xmax [expr $xmax + 100]
    set ymin [expr $ymin - 1000]
    set ymax [expr $ymax + 100]
    fcroute \
        -type power \
        -incremental \
        -selected_bump \
        -area "$xmin $ymin $xmax $ymax" \
        -extraConfig inputs/fcroute-extra-config.cfg \
        -verbose
    
    # route power bumps to ring
    deselect_bump
    select_bump -area {300 3550 3650 3700} -type ground
    select_bump -area {300 3550 3650 3700} -type power
    deselect_bump -floating
    set xmin [tcl::mathfunc::min {*}[get_db selected .bbox.ll.x]]
    set xmax [tcl::mathfunc::max {*}[get_db selected .bbox.ur.x]]
    set ymin [tcl::mathfunc::min {*}[get_db selected .bbox.ll.y]]
    set ymax [tcl::mathfunc::max {*}[get_db selected .bbox.ur.y]]
    set xmin [expr $xmin - 100]
    set xmax [expr $xmax + 100]
    set ymin [expr $ymin - 100]
    set ymax [expr $ymax + 1000]
    fcroute \
        -type power \
        -incremental \
        -selected_bump \
        -area "$xmin $ymin $xmax $ymax" \
        -connectInsideArea \
        -extraConfig inputs/fcroute-extra-config.cfg \
        -verbose

    fillNotch
}

route_bumps_main
