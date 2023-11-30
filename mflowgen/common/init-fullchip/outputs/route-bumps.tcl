proc route_bumps_main {} {
    # --- Power ring info
    # set pwr_ring_layer_obj     [dbGet -p head.layers.name gm0]
    # set pwr_ring_width         [dbGet $pwr_ring_layer_obj.maxWidth]
    # set pwr_ring_spacing       [expr 2 * [dbGet $pwr_ring_layer_obj.minSpacing]]
    # set pwr_ring_offset_top    -0.1
    # set pwr_ring_offset_bottom -0.1
    # set pwr_ring_offset_left   -0.1
    # set pwr_ring_offset_right  -0.1
    # set pwr_ring_info          [list $pwr_ring_width \
    #                                  $pwr_ring_spacing \
    #                                  $pwr_ring_offset_top \
    #                                  $pwr_ring_offset_bottom \
    #                                  $pwr_ring_offset_left \
    #                                  $pwr_ring_offset_right]

    # --- Disable nanoroute/viagen mode first
    #     (Deprecated: The router setting is now moved to later stage)
    # setNanoRouteMode -reset
    # setViaGenMode -reset

    # --- Add routing blockage as a guide
    #     (Deprecated: Use hacked LEF to create ports instead)
    # add_signal_route_blockage_on_pads $pwr_ring_info

    # --- Create power ring
    # add_power_rings $pwr_ring_info

    # --- Route signals from pads to bumps
    route_signal_bumps

    # --- Connect pads to power ring with stripes
    # add_stripes_from_pads_to_rings $pwr_ring_info
    # add_stripes_to_pads

    # --- Delete dangling stripes if there is any
    #     (Deprecated: there shouldn't be any dangling stripes
    #      if we add the stripes first and then route the signals)
    # editTrim 

    # --- Route power from bumps to power ring
    # add_cell_obs -cell supply/gpio cell -layer gmb -rects "block all except boundary"
    # route_power_bumps
    # elete_cell_obs -cell supply/gpio cell -layer gmb

    # --- I hate flip chip, nothing works
    #     Have to to manaual route here
    manual_power_route
}

proc manual_power_route {} {
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
    setFlipChipMode -layerChangeBotLayer                  gmb
    setFlipChipMode -routeWidth                           3.99
    setFlipChipMode -route_style                          45DegreeRoute
    setViaGenMode   -invoke_verifyGeometry                false
    setFlipChipMode -connectPowerCellToBump               false
    setFlipChipMode -honor_bump_connect_target_constraint false
    setFlipChipMode -ignore_pad_type_check                true
    # setFlipChipMode -prevent_via_under_bump             true
    # setFlipChipMode -lower_layer_prevent_45_routing       true
    # setFlipChipMode -allow_layer_change                   true
    setSrouteMode   -allowWrongWayRoute                   true

    # # select a portion of the signal bumps
    # set bump_select_regions {}
    # # only do routes in top/bottom for now
    # lappend bump_select_regions {0 0 4000 500}
    # lappend bump_select_regions {100 3680 3800 4000}
    # lappend bump_select_regions {0 330 420 3800}
    # lappend bump_select_regions {3500 330 4000 3500}
    # foreach region $bump_select_regions {
    #     select_bumps_within $region signal
    #     set bump_route_area [get_bump_region]
    #     fcroute \
    #         -type signal \
    #         -incremental \
    #         -selected_bump \
    #         -area $bump_route_area \
    #         -connectInsideArea \
    #         -verbose
    # }
    fcroute \
         -type signal \
         -incremental \
         -extraConfig /sim/pohan/garnet/mflowgen/common/init-fullchip/outputs/fcroute-extra-config.cfg
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
    addRing \
        -nets {VSS VDD VDDPST} \
        -layer $ring_layer \
        -width $ring_width \
        -spacing $ring_spacing \
        -offset "top $ring_offset_top bottom $ring_offset_bottom left $ring_offset_left right $ring_offset_right"
}

proc add_stripes_from_pads_to_rings { ring_info } {

    # Configure stripe adding mode
    setAddStripeMode                           -reset
    setAddStripeMode -ignore_DRC               true
    setAddStripeMode -stacked_via_bottom_layer gm0
    setAddStripeMode -stacked_via_top_layer    gmb

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
    set ring_offset_top    [expr [lindex $ring_info 2] + 8.820]
    set ring_offset_bottom [expr [lindex $ring_info 3] + 8.820]
    set ring_offset_left   [expr [lindex $ring_info 4] + 7.344]
    set ring_offset_right  [expr [lindex $ring_info 5] + 7.344]
    # top bottom left right
    foreach side { top bottom left right } {
        set pad_objs [dbGet -p top.insts.name IOPAD_$side*]
        # set pad_objs [dbGet -p top.insts.name IOPAD_bottom_TLX_FWD_PAYLOAD_TDATA_HI_0]
        foreach pad_obj $pad_objs {
            set pad_inst_name [dbGet $pad_obj.name]
            set pad_cell_name [dbGet $pad_obj.cell.name]
            set pad_llx [dbGet $pad_obj.box_llx]
            set pad_lly [dbGet $pad_obj.box_lly]
            set pad_urx [dbGet $pad_obj.box_urx]
            set pad_ury [dbGet $pad_obj.box_ury]
            set pad_orient [dbGet $pad_obj.orient]
            set i 0
            foreach port { vssp pad vcc vccio } {
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
                # dont need extend if we are doing signal pad
                if {$port eq "pad"} {
                    set sbox_llx $pad_llx
                    set sbox_lly $pad_lly
                    set sbox_urx $pad_urx
                    set sbox_ury $pad_ury
                }
                # pad orientation
                if { $side eq "top" || ($side eq "left" && $pad_orient eq "R0") || ($side eq "right" && $pad_orient eq "MY") } {
                    set reverse 0
                } else {
                    set reverse 1
                }
                # compute the stripe width and offset
                if {[string match "*SUPPLY*" $pad_inst_name]} {
                    # SUPPLY pad
                    if {$port eq "pad"} {
                        # supply pad will not have signal pad
                        continue
                    }
                    set space [expr ($pad_length - $stripe_width*3) / 2]
                    # compute the offset
                    if { $reverse == 1 } {
                        if {$port eq "vssp"} {
                            set stripe_net VSS
                            set stripe_width 12.0
                            set stripe_offset [expr 0 * (12.0 + $space)]
                        } elseif {$port eq "vcc"} {
                            set stripe_net VDD
                            set stripe_width 12.0
                            set stripe_offset [expr 1 * (12.0 + $space)]
                        } elseif {$port eq "vccio"} {
                            set stripe_net VDDPST
                            set stripe_width 12.0
                            set stripe_offset [expr 2 * (12.0 + $space)]
                        }
                    } else {
                        if {$port eq "vccio"} {
                            set stripe_net VSS
                            set stripe_width 12.0
                            set stripe_offset [expr 0 * (12.0 + $space)]
                        } elseif {$port eq "vcc"} {
                            set stripe_net VDD
                            set stripe_width 12.0
                            set stripe_offset [expr 1 * (12.0 + $space)]
                        } elseif {$port eq "vssp"} {
                            set stripe_net VDDPST
                            set stripe_width 12.0
                            set stripe_offset [expr 2 * (12.0 + $space)]
                        }
                    }
                } else {
                    # SIGNAL pad
                    set param_pwr_stripe_width 12.0
                    set param_pad_stripe_width 3.99
                    set space [expr ($pad_length - 3 * $param_pwr_stripe_width - $param_pad_stripe_width) / 3.0]
                    # compute the offset
                    if { $reverse == 0 } {
                        if {$port eq "vssp"} {
                            set stripe_net VSS
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 0 * ($param_pwr_stripe_width + $space)]
                        } elseif {$port eq "pad"} {
                            set term_obj [dbGet -p $pad_obj.instTerms.name *$port]
                            set stripe_net [dbGet $term_obj.net.name]
                            set stripe_width $param_pad_stripe_width
                            set stripe_offset [expr 1 * ($param_pwr_stripe_width + $space)]
                        } elseif {$port eq "vcc"} {
                            set stripe_net VDD
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 1 * ($param_pwr_stripe_width + $space) + ($param_pad_stripe_width + $space)]
                        } elseif {$port eq "vccio"} {
                            set stripe_net VDDPST
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 2 * ($param_pwr_stripe_width + $space) + ($param_pad_stripe_width + $space)]
                        }
                    } else {
                        if {$port eq "vccio"} {
                            set stripe_net VDDPST
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 0 * ($param_pwr_stripe_width + $space)]
                        } elseif {$port eq "vcc"} {
                            set stripe_net VDD
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 1 * ($param_pwr_stripe_width + $space)]
                        } elseif {$port eq "pad"} {
                            set term_obj [dbGet -p $pad_obj.instTerms.name *$port]
                            set stripe_net [lindex [dbGet $term_obj.net.name] 0]
                            set stripe_width $param_pad_stripe_width
                            set stripe_offset [expr 2 * ($param_pwr_stripe_width + $space)]
                        } elseif {$port eq "vssp"} {
                            set stripe_net VSS
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 2 * ($param_pwr_stripe_width + $space) + ($param_pad_stripe_width + $space)]
                        }
                    }
                }
                
                if {$port != "pad"} {
                    # add the stripe
                    addStripe \
                        -area "$sbox_llx $sbox_lly $sbox_urx $sbox_ury" \
                        -direction $stripe_direction \
                        -layer gmb \
                        -nets $stripe_net \
                        -width $stripe_width \
                        -start_offset $stripe_offset \
                        -number_of_sets 1
                    # advance i
                    incr i
                }
            }
        }
    }
}

proc add_stripes_to_pads {} {

    # Configure stripe adding mode
    setAddStripeMode                           -reset
    setAddStripeMode -ignore_DRC               false
    setAddStripeMode -stacked_via_bottom_layer gm0
    setAddStripeMode -stacked_via_top_layer    gmb

    # Add power stripes to connect the power rails
    # in the pads to the power ring:
    set vert_pitch [dbGet top.fPlan.coreSite.size_y]
    set hori_pitch [dbGet top.fPlan.coreSite.size_x]

    # top bottom left right
    foreach side { top bottom left right } {
        set pad_objs [dbGet -p top.insts.name IOPAD_$side*]
        foreach pad_obj $pad_objs {
            set pad_inst_name [dbGet $pad_obj.name]
            set pad_cell_name [dbGet $pad_obj.cell.name]
            set pad_llx [dbGet $pad_obj.box_llx]
            set pad_lly [dbGet $pad_obj.box_lly]
            set pad_urx [dbGet $pad_obj.box_urx]
            set pad_ury [dbGet $pad_obj.box_ury]
            set pad_orient [dbGet $pad_obj.orient]
            set i 0
            foreach port { vssp vcc vccio } {
                set sbox_llx $pad_llx
                set sbox_lly $pad_lly
                set sbox_urx $pad_urx
                set sbox_ury $pad_ury
                if {$side eq "top"} {
                    set stripe_direction "vertical"
                    set pad_length [dbGet $pad_obj.box_sizex]
                } elseif {$side eq "bottom"} {
                    set stripe_direction "vertical"
                    set pad_length [dbGet $pad_obj.box_sizex]
                } elseif {$side eq "left"} {
                    set stripe_direction "horizontal"
                    set pad_length [dbGet $pad_obj.box_sizey]
                } elseif {$side eq "right"} {
                    set stripe_direction "horizontal"
                    set pad_length [dbGet $pad_obj.box_sizey]
                }
                # pad orientation
                if { $side eq "top" || ($side eq "left" && $pad_orient eq "R0") || ($side eq "right" && $pad_orient eq "MY") } {
                    set reverse 0
                } else {
                    set reverse 1
                }
                # compute the stripe width and offset
                set stripe_width 8.0
                if {[string match "*SUPPLY*" $pad_inst_name]} {
                    set space [expr ($pad_length - $stripe_width*3) / 2]
                    # compute the offset
                    if { $reverse == 1 } {
                        if {$port eq "vssp"} {
                            set stripe_net VSS
                            set stripe_offset [expr 0 * (8.0 + $space)]
                        } elseif {$port eq "vcc"} {
                            set stripe_net VDD
                            set stripe_offset [expr 1 * (8.0 + $space)]
                        } elseif {$port eq "vccio"} {
                            set stripe_net VDDPST
                            set stripe_offset [expr 2 * (8.0 + $space)]
                        }
                    } else {
                        if {$port eq "vccio"} {
                            set stripe_net VSS
                            set stripe_offset [expr 0 * (8.0 + $space)]
                        } elseif {$port eq "vcc"} {
                            set stripe_net VDD
                            set stripe_offset [expr 1 * (8.0 + $space)]
                        } elseif {$port eq "vssp"} {
                            set stripe_net VDDPST
                            set stripe_offset [expr 2 * (8.0 + $space)]
                        }
                    }
                } else {
                    # SIGNAL pad
                    set param_pwr_stripe_width 8.0
                    set param_pad_stripe_width 3.99
                    set space [expr ($pad_length - 3 * $param_pwr_stripe_width - $param_pad_stripe_width) / 3.0]
                    # compute the offset
                    if { $reverse == 0 } {
                        if {$port eq "vssp"} {
                            set stripe_net VSS
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 0 * ($param_pwr_stripe_width + $space)]
                        } elseif {$port eq "vcc"} {
                            set stripe_net VDD
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 1 * ($param_pwr_stripe_width + $space) + ($param_pad_stripe_width + $space)]
                        } elseif {$port eq "vccio"} {
                            set stripe_net VDDPST
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 2 * ($param_pwr_stripe_width + $space) + ($param_pad_stripe_width + $space)]
                        }
                    } else {
                        if {$port eq "vccio"} {
                            set stripe_net VDDPST
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 0 * ($param_pwr_stripe_width + $space)]
                        } elseif {$port eq "vcc"} {
                            set stripe_net VDD
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 1 * ($param_pwr_stripe_width + $space)]
                        } elseif {$port eq "vssp"} {
                            set stripe_net VSS
                            set stripe_width $param_pwr_stripe_width
                            set stripe_offset [expr 2 * ($param_pwr_stripe_width + $space) + ($param_pad_stripe_width + $space)]
                        }
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
            }
        }
    }
}

proc route_power_bumps {} {

    # fcroute configuration
    setFlipChipMode -reset
    setFlipChipMode -layerChangeTopLayer                  gmb
    setFlipChipMode -layerChangeBotLayer                  gmb
    setFlipChipMode -routeWidth                           8.0
    setFlipChipMode -route_style                          manhattan
    setFlipChipMode -connectPowerCellToBump               true
    setFlipChipMode -honor_bump_connect_target_constraint false
    setFlipChipMode -ignore_pad_type_check                true
    # setFlipChipMode -drop_via_on_all_geometries           true
    # setFlipChipMode -multi_pad_routing_style              star
    # setFlipChipMode -multipleConnection                   multiPadsToBump
    # setFlipChipMode -lower_layer_prevent_45_routing       true
    # setFlipChipMode -allow_layer_change                   true
    setSrouteMode   -allowWrongWayRoute                   true

    # route power bumps to ring
    # deselect_bump
    # select_bump -area {380 370 3630 520} -type ground
    # select_bump -area {380 370 3630 520} -type power
    # deselect_bump -floating
    # set xmin [tcl::mathfunc::min {*}[get_db selected .bbox.ll.x]]
    # set xmax [tcl::mathfunc::max {*}[get_db selected .bbox.ur.x]]
    # set ymin [tcl::mathfunc::min {*}[get_db selected .bbox.ll.y]]
    # set ymax [tcl::mathfunc::max {*}[get_db selected .bbox.ur.y]]
    # set xmin [expr $xmin - 100]
    # set xmax [expr $xmax + 100]
    # set ymin [expr $ymin - 1000]
    # set ymax [expr $ymax + 100]
    fcroute \
        -type signal \
        -incremental \
        -nets {VDD VSS VDDPST} \
        -verbose
    
    fillNotch
}

# add_cell_obs -cell spacer_2lego_n1 -layer gmb -rects "0 0 2.16 47.88"
# add_cell_obs -cell spacer_2lego_e1 -layer gmb -rects "0 0 45.36 2.52"

route_bumps_main

# delete_cell_obs -cell spacer_2lego_n1 -layer gmb
# delete_cell_obs -cell spacer_2lego_e1 -layer gmb
