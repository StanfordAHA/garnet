# Compatibility commands defined so far
#    create_inst      
#    create_place_halo
#    place_inst       

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
    array set a2 {}
    foreach x $args {
        if { "$x" == "-location" } { set x "-loc" }
        if { "$x" == "-orient"   } { set x "-ori" }
        lappend a2 $x
    }
    echo addInst $a2
    eval addInst $a2
}
# set cell cellfoo; set inst instfoo; set ix 6; set iy 9
# create_inst -cell $cell -inst $fid_name \
#         -location "$ix $iy" -orient R0 -physical -status fixed
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

proc test_cph {} {
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
proc snap_floorplan    { args } { eval snapFPlan $args }
proc snap_floorplan_io { args } { eval snapFPlanIO $args }
