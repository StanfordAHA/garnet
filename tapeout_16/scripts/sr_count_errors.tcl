# Count all DRC errors in the design

# read_db final.db

# Seal ring causes literally millions of DRC errors.
# That's kind of its thing.
# So if sealring exists, must remove it (and then restore later)
# Note sealring currently added at end of chip_finishing.tcl like so:
# eval_legacy {
#     addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring \
#     -physical -loc {-52.344 -53.7}
# }
set had_sealring 0
if { [get_db insts sealring] ne "" } {
    set had_sealring 1
    set sr [get_db insts sealring]
    set sr_cell [get_db [get_db $sr .base_cell] .name]; puts $sr_cell
    set sr_locx [get_db $sr .location.x]; puts $sr_locx
    set sr_locy [get_db $sr .location.y]; puts $sr_locy

    puts "@file_info WARNING Found existing sealring $sr_cell at loc $sr_locx $sr_locy"
    puts "@file_info WARNING Deleteing sealring, will restore later"
    puts "#file_info delete_inst -inst sealring"
    delete_inst -inst sealring; # gui_redraw
}

# FIXME Tile_id straps cause DRC errors b/c insufficient precautions
# taken when blocakges were build for tile std cells, see github issue.
# For now, we "fix" this by deleting (and later restoring) the straps.
set had_straps 0
set mynets [get_db nets *tile_id*]
if {[llength $mynets]} {
    # Delete all tile_id straps
    set had_straps 1
    set nstraps [llength $mynets]; # Should be 8192 straps
    puts "@file_info WARNING found $nstraps tile_id straps (should be 8192)"
    puts "@file_info WARNING will delete straps and restore again later"
    #
    # To restore them again later will need: netname, layer, rectangle
    # Layer is M4, defined in floorplan.tcl as var $connection_layer
    # Can get netname and rectangle as shown:
    set straps ""
    foreach sw [get_db $mynets .special_wires] {
        # set connection_layer M4        
        # puts $sw
        # name should look like "core_cgra_subsystem/Interconnect_inst0_Tile_X00_Y10__tile_id[14]"
        set name [get_db [get_db $sw .net] .name]
        set rect [get_db $sw .rect]
        lappend straps "$name $rect"
        set n_straps [llength $straps]
        # puts $n_straps
        if { $n_straps < 10 } {
            # "core_cgra_subsystem/Interconnect_inst0_Tile_X00_Y10__tile_id[14]"
            # => "Tile_X00_Y10__tile_id[14]"
            set abbrev [string range $name 39 end]
            puts "@file_info Deleting strap $abbrev $rect"
        } elseif { $n_straps == 10 } { 
            puts eq10
            puts "@file_info ..." 
        }
        delete_obj $sw
    }
}

########################################################################
# 320 errors arising from m8 blockage over top of chip
# 
# > get_db selected
# route_blockage:0x7f9e8cce6160
# > get_db selected .rects
# {0.0 4099.584 4899.96 4899.984}
# > llength [ get_db route_blockages -if { .layer == layer:M8 && (.rects.ll.x == 0) && (.rects.ll.y > 4000) } ]
# 1
# > get_db route_blockages -if { .layer == layer:M8 && (.rects.ll.x == 0) && (.rects.ll.y > 4000) }
# route_blockage:0x7f9e8cce6160
puts "@file_info Deleting M8 blockage across top of chip, it caused 320 DRC errors"
set rb [
        get_db route_blockages -if {
            .layer == layer:M8 && 
            (.rects.ll.x == 0) && (.rects.ll.y > 4000)
        }
       ]
delete_obj $rb

########################################################################
# No more weird blockages I got rid of em [sr 1912]
# # Delete weird icovl 17.03 halos
# delete_obj [
#   get_db route_blockages ifid_icovl_* -expr {$obj(.spacing) eq {17.03}}
# ]


########################################################################
# Get rid of blockages over iphy cell.
# It's analog guys' problem now!!!
# 
# > get_db inst:GarnetSOC_pad_frame/iphy .bbox
#   {1813.05 4099.584 2393.1 4800.0}
# > get_db route_blockage:0x7f27052c61d8 .rects
#   {1813.05 4099.584 2393.1 4800.0}

set bbox [get_db inst:GarnetSOC_pad_frame/iphy .bbox]
set bbox [lindex $bbox 0]
set b0 [lindex $bbox 0]
set b1 [lindex $bbox 1]
set b2 [lindex $bbox 2]
set b3 [lindex $bbox 3]
set rb [
        get_db route_blockages -if {
            .rects.ll.x == $b0 &&
            .rects.ll.y == $b1 &&
            .rects.ur.x == $b2 &&
            .rects.ur.y == $b3
        }
       ]
echo $rb
delete_obj $rb


# Fix last few routing errors
source ../../scripts/sr_finalfix.tcl

# Count the DRC errors. This will maybe take 45 min?
# begin: 1608...1643...

date
check_drc -limit 10000 > tmp
date

set n_errors [ llength [ get_db markers ] ]
puts "@file_info 'sr_count_errors.tcl' found $n_errors DRC problems"

if { $had_straps } {
    # Rebuild tile_id straps
    set connection_layer M4
    set n_printed 0
    foreach strap $straps {
        set name [lindex $strap 0]
        set rect [lindex $strap 1]
        set abbrev [string range $name 39 end]
        if { $n_printed < 10 } {
            puts "@file_info Creating strap $abbrev {$rect}"
            incr n_printed
        } elseif { $n_printed == 10 } {
            puts "@file_info ..."
            incr n_printed
        }
        create_shape -net $name -layer $connection_layer -rect $rect
    }
}


# ???
# # create_shape -net $id_net_name \
# #      -layer $connection_layer -rect $llx $lly $urx $ury
# delete_obj $sw
# set connection_layer M4
# create_shape -net $name -layer $connection_layer -rect $rect
# 
# 
#     
# 
#     #
#     deselect_obj -all
#     # select_obj [get_db $mynets .special_wires]; # If you want to see them
#     delete_obj [get_db $mynets .special_wires]
# } else {
#     puts "@file_info WARNING Found no tile_id straps in the design"
# }
# 
# set strap net:GarnetSOC_pad_frame/core_cgra_subsystem/Interconnect_inst0_Tile_X00_Y10__tile_id[15]
# set mylist [get_db $strap .name]
# 
# GarnetSOC_pad_frame/core_cgra_subsystem/Interconnect_inst0_Tile_X16_Y05__tile_id[3]
# 
# get_db special_wires -if {.net == *tile_id*}
# 
# lappend strap_names "foo"
# aka
# append strap_names " " "foo"
# 
# lappend straps {a b c}
# lappend straps {d e f}
# lindex $straps 1; # => {d e f}
# 
# for {set i 0} {$i<[llength straps} {incr x} {
#     puts "x is $x"
# }
# 
# # Restore straps if necessary
# # Straps were originally placed in floorplan.tcl
# #   create_shape \
# #     -net $id_net_name \
# #     -layer $connection_layer \
# #     -rect $llx $lly $urx $ury
# 
# 
#       set id_net [get_net -of_objects $id_pin]
#       set id_net_name [get_property $id_net hierarchical_name]
# get_property $strap hierarchical_name
# core_cgra_subsystem/Interconnect_inst0_Tile_X00_Y10__tile_id[14]

# Restore sealring if necessary
if { $had_sealring } {
    # addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring
    # -physical -loc {-52.344 -53.7}
    puts "@file_info WARNING restoring sealring"
    puts "@file_info addInst -cell $sr_cell -inst sealring -physical -loc {$sr_locx $sr_locy}"
    # haha $sr_cell cannot survive the eval_legacy wrapper haha :( :(
    set ::env(TMP1) $sr_cell
    set ::env(TMP2) $sr_locx
    set ::env(TMP3) $sr_locy
    eval_legacy {
        set sr_cell $::env(TMP1)
        set sr_locx $::env(TMP2)
        set sr_locy $::env(TMP3)
        puts "addInst -cell $sr_cell -inst sealring -physical -loc {$sr_locx $sr_locy}"
        # addInst -cell $sr_cell -inst sealring -physical -loc {$sr_locx $sr_locy} NOPE!
        addInst -cell $sr_cell -inst sealring -physical -loc [list $sr_locx $sr_locy]
    }
}
