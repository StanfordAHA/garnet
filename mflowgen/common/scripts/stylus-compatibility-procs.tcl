# No translation needed for
#    create_route_blockage

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
# 
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
proc assign_bumps { args } { 
    set a2 []
    foreach x $args {
        # OMG WHY
        if { "$x" == "-multi_bumps_to_multi_pads" } { set x "-multiBumpToMultiPad" }
        lappend a2 $x
    }
    echo assignBump $a2
    eval assignBump $a2
}

# -----
# get_legacy_command gui_show_bump_connections => viewBumpConnection
proc gui_show_bump_connections { args } { eval viewBumpConnection $args }

