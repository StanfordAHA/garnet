# No translation needed for create_route_blockage
# Oop no I'm wrong dammit
# Looks like the supported command is..? 'createRouteBlk'...?
# But apparently create_route_blockage is also available, except
# there's no '-area' arg :( ... uses...? "-box" instead...?

# Legacy: create_route_blockage [-help] [-fills] [-inst <name>] {-layers <layer+>
# | -all <enum+>} {-box {x1 y1 x2 y2} | -rects {{x1 y1 x2 y2} ...}
# | -polygon {{x1 y1} {x2 y2} ...} | -cover } [-name <string>
# | -use_prefix ] [-except_pg_nets  | -pg_nets
# | -partial <integer>] [-spacing <value> | -design_rule_width <value>]

# Except hm probably not wise to try and redefine an existing command :(

proc create_route_blockage_stylus { args } {
    set a2 []
    foreach x $args {
        if { "$x" == "-area"   } { set x "-box"   }
        if { "$x" == "-layers" } { set x "-layer" }; # Oh so annoying!
        lappend a2 $x
    }
    echo createRouteBlk $a2
    eval createRouteBlk $a2
}


# create_inst [-help]
#   [-module verilogModule]
#   [-physical]
#   -cell cellName -inst instName
#   [-location {x y}
#   [-orient {r0 | r90 | r180 | r270 | mx | mx90 | my | my90}]]
#   [-status placementStatus]
# =>
# addInst  [-help]
#   [-moduleBased verilogModule]
#   [-physical]
#   -cell cellName -inst instName
#   [-loc {x y}
#   [-ori {R0 | R90 | R180 | R270 | MX | MX90 | MY | MY90}]]
#   [-status placementStatus]
# 
proc create_inst { args } { 
    set a2 []
    foreach x $args {
        if { "$x" == "-location" } { set x "-loc" }
        if { "$x" == "-orient"   } { set x "-ori" }
        lappend a2 $x
    }
    echo addInst $a2
    eval addInst $a2
}
proc create_inst_test {} { 
    set cell cellfoo; set inst instfoo; set ix 6; set iy 9
    create_inst -cell $cell -inst $fid_name \
        -location "$ix $iy" -orient R0 -physical -status fixed
}

proc place_inst { args } { eval placeInstance $args }

proc create_place_halo { args } {
    set halo_deltas {}
    set snap2site ""
    for {set i 0} {$i < [ llength $args ] } {incr i} {
        set x [ lindex $args $i ] 
              if { "$x" == "-insts" }       { set insts [ lindex $args [ incr i ] ]
        } elseif { "$x" == "-halo_deltas" } { continue
        } elseif { "$x" == "-snap_to_site"} { set snap2site "-snapToSite"
        } else                              { lappend halo_deltas $x }
    }
    echo addHaloToBlock $halo_deltas $snap2site $insts
    eval addHaloToBlock $halo_deltas $snap2site $insts
}
proc create_place_halo_test { } {
    set fid_name tree_fiddy; set halo_margin 10.0;
    create_place_halo -insts $fid_name \
        -halo_deltas $halo_margin $halo_margin $halo_margin $halo_margin \
        -snap_to_site
}

#  delete_inst [-help] -inst instName [-module moduleName] [-verbose]
#  deleteInst  [-help] instName [-moduleBased moduleName] [-verbose]
proc delete_inst { _inst instName } {
    if { $_inst != "-inst" } {
        puts stderr "ERROR: unexpected format for delete_inst"
        exit 13
    }
    eval deleteInst $instName
}


# add_io_fillers [-help] -cells {name_list} [-fill_any_gap]
# [-filler_orient r0 | r90 | r180 | r270 | mx | mx90 | my | my90]
# [-from coord] [-prefix prefix] [-side {top | bottom | left |
# right}] [-to coord] [-io_ring row_number]
# [-use_small_io_height] [-logic [-derive_connectivity ]]
# =>
# addIoFiller    [-help] -cell  {name_list} [-fillAnyGap]
# [-fillerOrient R0 | R90 | R180 | R270 | MX | MX90 | MY | MY90]
# [-from coord] [-prefix prefix] [-side {top | bottom | left |
# right}] [-to coord] [-row rowNumber] 
# [-useSmallIoHeight]  [-logic [-deriveConnectivity]]

# connect_pin [-help]
#   -inst instName  -pin termName  -net netName
#   [-module verilogModule]
#   [-no_new_port]
#   [-hport portName]
#   [-reference_pin refInstName refPinName]
# 
# get_legacy_command connect_pin => attachTerm
# attachTerm [-help]
#   instName termName netName
#   [-moduleBased verilogModule]
#   [-noNewPort]
#   [-port portName]
#   [-pin refInstNamerefPinName]

proc check_floorplan   { args } { eval checkFPlan $args }

proc snap_floorplan    { args } { 
    set new_args {}
    for {set i 0} {$i < [ llength $args ] } {incr i} {
        set a [ lindex $args $i ] 
        if { "$a" == "-io_pad" } { set a "-ioPad" }
        lappend new_args $a
    }
    eval snapFPlan $new_args
}



proc snap_floorplan_io { args } { eval snapFPlanIO $args }

########################################################################
# gen_bumps procedures
proc delete_bumps { args } { eval deleteBumps $args }

# Really. "bump" vs. "bumps". Really.
proc   select_bumps { args } { eval   select_bump $args }
proc deselect_bumps { args } { eval deselect_bump $args }

# -----
# create_bump -cell $bumpCell   \
#         -edge_spacing "$bofsW $bofsS $bofsE $bofsN"   \
#         -location_type cell_center   \
#         -name_format "Bump_%i.%r.%c"   \
#         -orient r0   \
#         -pitch "$bp $bp"   \
#         -location "$bofsW $bofsS"   \
#         -pattern_array "$nb $nb"
# 
# same same 
# proc create_bump { args } { eval create_bump $args }
# 
# NOPE! Nothing's ever easy is it.
#   **ERROR: (IMPTCM-48): "-location_type" is not a legal option for
#   command "create_bump". Either the current option or an option prior
#   to it is not specified correctly.
# Haha still have to rename orig command "create_bump" => "create_bump_stylus" :(
proc create_bump_stylus { args } { 
    set a2 []
    foreach x $args {
        # OMG WHY
        if { "$x" == "-location"      } { set x "-loc" }
        if { "$x" == "-location_type" } { set x "-loc_type" }
        if { "$x" == "-orient"        } { set x "-orientation" }
        lappend a2 $x
    }
    echo create_bump $a2
    eval create_bump $a2
}
# -----
# stylus: assign_signal_to_bump -selected -net VSS
# common:
#    assignSigToBump - Assigns selected or specified bumps to the specified net or pin
#    assignSigToBump [-help] {{-net net_name | -top_pin port} {-bumps bump_name_list | -selected }}
proc assign_signal_to_bump { args } { eval assignSigToBump $args }

# -----
# assign_bumps -multi_bumps_to_multi_pads -selected -pg_only \
#     -pg_nets VSS -pg_insts ${io_root}*VDDPST_* \
#     -exclude_region {1050 1050 3840 3840}
# 
# Name
# assignBump - Assigns the bumps closest to the I/O cells...
# 
# Syntax
# assignBump  [-help]  [{-area  x1  y1  x2  y2  | -selected }]
#   [-constraint_file file_name] [-exclude_region llxllyurxury ...]  [-maxDistance distance]
#   [-multiBumpToMultiPad]
#   [{[[-pgnet net_list] | [-exclude_pgnet net_list]][-pginst instance_list]} [-pgonly]]
# 
# **ERROR: (IMPTCM-48):   "-pg_only" is not a legal option for command "assignBump". Either the current option or an option prior to it is not specified correctly.



proc assign_bumps { args } { 
    set a2 []
    foreach x $args {
        # OMG WHY
        if { "$x" == "-multi_bumps_to_multi_pads" } { set x "-multiBumpToMultiPad" }
        if { "$x" == "-exclude_pg_nets"  } { set x "-exclude_pgnet" }
        if { "$x" == "-pg_only"  } { set x "-pgonly" }
        if { "$x" == "-pg_insts" } { set x "-pginst" }
        if { "$x" == "-pg_nets"  } { set x "-pgnet"  }
        lappend a2 $x
    }
    echo assignBump $a2
    eval assignBump $a2
}

# -----
# get_legacy_command gui_show_bump_connections => viewBumpConnection
proc gui_show_bump_connections { args } { eval viewBumpConnection $args }

##############################################################################
# Gen_power

proc add_endcaps { args } { eval addEndCap $args }

# -----
# create_place_blockage
#   -inst [get_db $inst .name]
#   -outer_ring_by_side {3.5 2.5 3.5 2.5}
#   -name TAPBLOCK
# 
# -outerRingBySide {<left> <bottom> <right> <top>}
proc create_place_blockage { args } { 
    set a2 []
    foreach x $args {
        # OMG WHY
        if { "$x" == "-outer_ring_by_side" } { set x "-outerRingBySide" }
        lappend a2 $x
    }
    echo createPlaceBlockage $a2
    eval createPlaceBlockage $a2
}

#     add_well_taps \
#       -cell_interval 10.08 \
#       -in_row_offset 5
proc add_well_taps { args } {
    set a2 []
    foreach a $args {
        # OMG WHY
        if { "$a" == "-cell_interval" } { set a "-cellInterval" }
        if { "$a" == "-in_row_offset" } { set a "-inRowOffset" }
        lappend a2 $a
    }
    echo addWellTap $a2
    eval addWellTap $a2
}

#    add_rings \
#       -type core_rings   \
#       -jog_distance 0.045   \
#       -threshold 0.045   \
#       -follow core   \
#       -layer {bottom M2 top M2 right M3 left M3}   \
#       -width 1.96   \
#       -spacing 0.84   \
#       -offset 1.4   \
#       -nets {VDD VSS VDD VSS VDD VSS}
proc add_rings { args } { eval addRing $args }

# -----
#    route_special -connect {pad_pin}  \
#       -layer_change_range { M2(2) M8(8) }  \
#       -pad_pin_port_connect {all_port one_geom}  \
#       -pad_pin_target {ring}  \
#       -delete_existing_routes  \
#       -pad_pin_layer_range { M3(3) M4(4) }  \
#       -crossover_via_layer_range { M2(2) M8(8) }  \
#       -nets { VSS VDD }  \
#       -allow_layer_change 1  \
#       -target_via_layer_range { M2(2) M8(8) } \
#       -inst [get_db [get_db insts *IOPAD*VDD_*] .name]
# TCR p. 2811
# omg sroute is route_special with *every switch transformed*
#
# after transform_underbars:
# sroute -connect pad_pin -layerChangeRange { M2(2) M8(8) }
#   -padPinPortConnect {all_port one_geom} -padPinTarget ring
#   -deleteExistingRoutes -padPinLayerRange { M3(3) M4(4) }
#   -crossoverViaLayerRange { M2(2) M8(8) } -nets { VSS VDD }
#   -allowLayerChange 1 -targetViaLayerRange { M2(2) M8(8) }
#   -inst {IOPAD_bottom_VDD_0 IOPAD_bottom_VDD_1 IOPAD_left_VDD_0
#     IOPAD_left_VDD_1 IOPAD_right_VDD_0 IOPAD_right_VDD_1
#     IOPAD_top_VDD_dom3}
# 
# **ERROR: (IMPTCM-23): "pad_pin" is not a valid enum for "-connect",
#   the allowed values are {blockPin corePin padPin padRing
#   floatingStripe secondaryPowerPin}.
proc route_special { args } {
    set a1 []
    foreach a $args {
        lappend a1 [transform_underbars $a]
    }
    set a2 []
    foreach a $a1 {
        set a [fix_stylus_sublist $a]
        lappend a2 $a
    }
    echo sroute $a2
    eval sroute $a2
}
proc fix_stylus_sublist { L_in } {
    set L_out []
    foreach a $L_in {
        if { "$a" == "pad_pin" }  { set a "padPin" }
        if { "$a" == "all_port" } { set a "allPort" }
        if { "$a" == "one_geom" } { set a "oneGeom" }
        lappend L_out $a
    }
    return $L_out
}
# set a { all_port one_geom }
# fix_stylus_sublist $a
# fix_stylus_sublist foo



#     add_stripes \
#       -pin_layer M1   \
#       -over_pins 1   \
#       -block_ring_top_layer_limit M1   \
#       -max_same_layer_jog_length 3.6   \
#       -pad_core_ring_bottom_layer_limit M1   \
#       -pad_core_ring_top_layer_limit M1   \
#       -spacing 1.8   \
#       -master "TAPCELL* BOUNDARY*"   \
#       -merge_stripes_value 0.045   \
#       -direction horizontal   \
#       -layer M1   \
#       -area {} \
#       -block_ring_bottom_layer_limit M1   \
#       -width pin_width   \
#       -nets {VSS VDD}
# same same?
# No! Mostly same except for stupid gratuitous $#!!
proc add_stripes { args } {
    set a2 []
    foreach a $args {
        if { "$a" == "-pad_core_ring_bottom_layer_limit"  } { 
               set a "-padcore_ring_bottom_layer_limit" }
        if { "$a" == "-pad_core_ring_top_layer_limit"  } { 
               set a "-padcore_ring_top_layer_limit" }
        lappend a2 $a
    }
    echo addStripe $a2
    eval addStripe $a2
}


# Usage: addStripe [-help] [-all_blocks <0|1>] [-area <x1 y1 x2 y2 ...>] [-area_blockage < {x1 y1 x2 y2}... {x1 y1 x2 y2 x3 y3 x4 y4 ...} ...>]
# [-between_bumps <0|1>] [-block_ring_bottom_layer_limit <layer>] [-block_ring_top_layer_limit <layer>] [-create_pins <0|1>]
# [-direction {horizontal vertical}] [-extend_to {design_boundary first_padring last_padring all_domains}] [-insts <instance_name>]
# -layer <layer> [-master <master_cell>] [-max_same_layer_jog_length <real_value>] [-merge_stripes_value <auto|value>] [-narrow_channel <0|1>]
# -nets <list_of_nets> [-number_of_sets <integer_value>] [-over_bumps <0|1>] [-over_physical_pins <0|1>] [-over_pins <0|1>]
# [-over_power_domain <0|1>]
# [-padcore_ring_bottom_layer_limit <layer>]
# [-padcore_ring_top_layer_limit <layer>] [-pin_layer <layer>]
# [-pin_offset <real_value>] [-pin_width <min_value max_value>] [-power_domains <domain_name>] [-report_cut_stripe <log name>]
# [-same_layer_target_only <0|1>] [-set_to_set_distance <real_value>] [-spacing <name_or_value>]
# [-stapling <stripe_length>|auto {<ref_offeset ref_pitch:pitch_num> | <ref_layer1>} [ref_layer2]>] [-start <real_value>]
# [-start_from {left right bottom top}] [-start_offset <real_value>] [-stop <real_value>] [-stop_offset <real_value>]
# [-switch_layer_over_obs <0|1>] [-uda <subclass_string>] [-use_interleaving_wire_group <0|1>] [-use_wire_group {-1 0 1}]
# [-use_wire_group_bits <integer_value>] [-via_columns <integer>] [-via_rows <integer>] -width <name_or_value> [-snap_wire_center_to_grid {None Grid Mask1_Grid Mask2_Grid Half_Grid Either} ]
# 
# **ERROR: (IMPTCM-48):   "-pad_core_ring_bottom_layer_limit" is not a legal option for command "addStripe". Either the current option or an option prior to it is not specified correctly.





proc transform_underbars { s } {
    # set a_val [scan "a" %c]; # 97
    # set z_val [scan "z" %c]
    # set A_val [scan "A" %c]; # 65
    # set upperdiff [expr $a_val - $A_val] 
    # for { set i $a_val } { $i <= $z_val } { incr i } {
    #     set a [format %c $i]
    #     set A [format %c [expr $i - 32]]
    #     echo "regsub {_$a} \$s {$A}" s
    # }

    # Only transform strings that start with a dash character
    set first_char [string index $s 0]
    if { $first_char != "-" } { return $s }
    # else
    regsub -all {_a} $s {A} s
    regsub -all {_b} $s {B} s
    regsub -all {_c} $s {C} s
    regsub -all {_d} $s {D} s
    regsub -all {_e} $s {E} s
    regsub -all {_f} $s {F} s
    regsub -all {_g} $s {G} s
    regsub -all {_h} $s {H} s
    regsub -all {_i} $s {I} s
    regsub -all {_j} $s {J} s
    regsub -all {_k} $s {K} s
    regsub -all {_l} $s {L} s
    regsub -all {_m} $s {M} s
    regsub -all {_n} $s {N} s
    regsub -all {_o} $s {O} s
    regsub -all {_p} $s {P} s
    regsub -all {_q} $s {Q} s
    regsub -all {_r} $s {R} s
    regsub -all {_s} $s {S} s
    regsub -all {_t} $s {T} s
    regsub -all {_u} $s {U} s
    regsub -all {_v} $s {V} s
    regsub -all {_w} $s {W} s
    regsub -all {_x} $s {X} s
    regsub -all {_y} $s {Y} s
    regsub -all {_z} $s {Z} s
    # echo $s
    return $s
}

# transform_underbars -foo_bar_baz_mumble_bar_baz_bumble
# -fooBarBazMumbleBarBazBumble

# get_legacy_command delete_global_net_connections
proc delete_global_net_connections { args } { eval clearGlobalNets $args }
proc connect_global_net { args } { eval globalNetConnect $args }

# Needs verified (below)
proc add_power_mesh_colors { args } { eval colorizePowerMesh $args }


# stylus command:
# colorizePowerMesh [-help] [-reverse_with_nondefault_width {0 | 1}]
# 
# You can use this command to colorize power structures, including power
# wires and power via metals. This command also fixes color violations
# of power metals including via metals. It is recommended to use this
# command once all the power mesh is built.
# 
# Note: The command does not fix via cut colors. For cut violation, use
# fixVia -cutSpacing (hidden option in this release) to fix cut color or
# trim cut with violation.


########################################################################
# BUMPS/FLIPCHIP

proc select_routes { args } {
    set a2 []
    foreach a $args {
        if { "$a" == "-shapes" } { set a "-shape"  }
        if { "$a" == "Regular" } { set a "regular" }
        if { "$a" == "Special" } { set a "special" }
        if { "$a" == "Patch"   } { set a "patch"   }
        lappend a2 $a
    }
    echo editSelect $a2
    eval editSelect $a2
}

# fcroute
# [-help]
# -type {power | signal}
# [-area {x1 y1 x2 y2}]
# [-connectInsideArea]
# [-connectTsvToBump] | [-connectTsvToPad] | [-connectTsvToRingStripe]
# [-constraintFile filename]
# [-deleteExistingRoutes]
# [-designStyle {aio | pio}]
# [-doubleBendRoute]
# [-eco | -incremental]
# [-extraConfig fileName]
# [-globalOnly]
# [-jogControl {preferWithChanges | preferSameLayer | preferDifferentLayer}]
# [-keepDRC]
# [-layerChangeBotLayer layerName]
# [-layerChangeTopLayer layerName]
# [-minEscapeDistance unit]
# [-msgRate int]
# [-nets {net_name_list | <filename | ~<filename} | -selected_bump]
# [-overflowMap]
# [-route_pg_style {none finger}]
# [-routeWidth real]
# [-spreadWiresFactor value]
# [-straightConnections [[straightWithDrcClean] [straightWithChanges]]
# [-subclass subclass_string]
# [-verbose]

# Usage: setNanoRouteMode
# [-help] [-reset] [-dbAdjustAutoViaWeight {true|false}]
# [-dbAllowInstanceOverlaps {true|false}]
# [-dbIgnoreFollowPinShape {true|false}]
# [-dbProcessNode <value>]
# [-dbRcExtractionCorner <value>]
# [-dbSkipAnalog {true|false}]
# [-dbViaWeight <value>]
# [-drouteAddPassiveFillOnlyOnLayers <value>]
# [-drouteAntennaEcoListFile <value>] [-drouteAutoStop {true|false}]
# [-drouteEndIteration <value>] [-drouteFixAntenna {true|false}] [-drouteMaskOnlyOnLayer <value>]
# [-drouteMinLengthForWireSpreading <value>] [-drouteMinLengthForWireWidening <value>] [-drouteMinSlackForWireOptimization <value>]
# [-drouteNoTaperInLayers <value>] [-drouteNoTaperOnOutputPin <value>] [-drouteOnGridOnly <value>]
# [-droutePostRouteLithoRepair {true|false}] [-droutePostRouteSpreadWire <value>] [-droutePostRouteSwapVia <value>]
# [-droutePostRouteSwapViaPriority <value>] [-droutePostRouteViaPillarEffort <value>] [-droutePostRouteWidenWire <value>]
# [-droutePostRouteWidenWireRule <value>] [-drouteSearchAndRepair {true|false}] [-drouteSignOffEffort <value>]
# [-drouteUseMultiCutViaEffort <value>] [-envNumberFailLimit <value>] [-envNumberProcessor <value>] [-envNumberWarningLimit <value>]
# [-envThirdPartyData {true|false}] [-hfrouteConstraintGroups <value>] [-hfrouteMatchReportFile <value>]
# [-hfrouteNumReserveLayers <value>] [-hfrouteRemoveFloatingShield {true|false}] [-hfrouteSearchRepair <value>]
# [-hfrouteShieldTrimLength <value>] [-routeAddAntennaInstPrefix <value>]
# [-routeAllowPinAsFeedthrough {true|TRUE|false|FALSE|none|NONE|output|input|inout}]
# [-routeAntennaCellName <value>]
# [-routeBottomRoutingLayer <value>] [-routeConcurrentMinimizeViaCountEffort <value>] [-routeConnectToBump {true|false}]
# [-routeDesignFixClockNets {true|false}] [-routeDesignRouteClockNetsFirst {true|false}] [-routeEnableNdrSiLimitLength <value>]
# [-routeEnforceNdrOnSpecialNetWire <value>] [-routeExtraViaEnclosure <value>] [-routeHonorPowerDomain {true|false}]
# [-routeIgnoreAntennaTopCellPin {true|false}]
# [-routeInsertAntennaDiode {true|false}]
# [-routeInsertDiodeForClockNets {true|false}]
# [-routeRelaxedNdrSpacingToPGNets <value>] [-routeReserveSpaceForMultiCut {true|false}] [-routeReverseDirection <value>]
# [-routeSelectedNetOnly {true|false}] [-routeShieldCrosstieOffset <value>] [-routeStrictlyHonorNonDefaultRule <value>]
# [-routeStripeLayerRange <value>] [-routeTieNetToShape <value>] [-routeTopRoutingLayer <value>]
# [-routeTrimPullBackDistanceFromBoundary <value>] [-routeTrunkWithClusterTargetSize <value>] [-routeUnconnectedPorts {true|false}]
# [-routeUseAutoVia <value>] [-routeWithEco {true|false}] [-routeWithLithoDriven {true|false}] [-routeWithSiDriven {true|false}]
# [-routeWithTimingDriven {true|false}] [-routeWithTrimMetal <value>] [-routeWithViaInPin <value>]
# [-routeWithViaOnlyForMacroCellPin <value>] [-routeWithViaOnlyForStandardCellPin <value>]

# setFlipChipMode ​ ​
# [-help]
# [-reset]
# [-allow_layer_change {true | false}]
# [-auto_pairing_file fileName]
# [-bump_use_oct_shape {true | false}]
# [-compaction {true | false}]
# [-connectPowerCellToBump {true | false}]
# [-constraintFile fileName]
# [-drop_via_on_all_geometries {true | false}]
# [-drop_via_on_power_mesh layerName]
# [-extraConfig fileName]
# [-finger_direction {N|E|S|W}]
# [-finger_max_width real_value]
# [-finger_min_width real_value]
# [-finger_target_mesh_layer_range {topLayer [bottomLayer]}]
# [-honor_bump_connect_target_constraint {true | false}]
# [-ignore_pad_type_check {true | false}]
# [-layerChangeBotLayer layerName]
# [-layerChangeTopLayer layerName]
# [-lower_layer_prevent_45_routing {true | false}]
# [-lower_layer_route_width value]
# [-multi_pad_routing_style {default|serial|star}]
# [-multipleConnection {multiPadsToBump | multiBumpsToPad | default}]
# [-prevent_via_under_bump {true | false}]
# [-route_pg_style {none |finger}]
# [-route_style {manhattan | 45DegreeRoute}]
# [-routeWidth real_value]

