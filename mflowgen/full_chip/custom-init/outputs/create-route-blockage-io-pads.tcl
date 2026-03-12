# create routing blockage for the pads
set blockage_width_left   [expr 15 * $hori_pitch]
set blockage_width_right  [expr 15 * $hori_pitch]
set blockage_width_top    [expr 3 * $vert_pitch]
set blockage_width_bottom [expr 3 * $vert_pitch]

# ------------ left: signals on m2/m4
set rbox_llx [dbGet [dbGet -p top.insts.name ring_terminator_left].box_urx]
set rbox_lly [dbGet [dbGet -p top.insts.name ring_terminator_left].box_lly]
set rbox_urx [expr $rbox_llx + $blockage_width_left]
set rbox_ury [dbGet [dbGet -p top.insts.name corner_ul].box_lly]
createRouteBlk \
    -name pad_route_block_left \
    -layer {m1 m2 m3 m5 m6 m7 m8} \
    -box "$rbox_llx $rbox_lly $rbox_urx $rbox_ury"

# ------------ right: signals on m2/m4
set rbox_llx [expr [dbGet [dbGet -p top.insts.name corner_lr].box_llx] - $blockage_width_right]
set rbox_lly [dbGet [dbGet -p top.insts.name corner_lr].box_ury]
set rbox_urx [dbGet [dbGet -p top.insts.name ring_terminator_right].box_llx]
set rbox_ury [dbGet [dbGet -p top.insts.name ring_terminator_right].box_ury]
createRouteBlk \
    -name pad_route_block_right \
    -layer {m1 m2 m3 m5 m6 m7 m8} \
    -box "$rbox_llx $rbox_lly $rbox_urx $rbox_ury"

# ------------ top: signals on m3/m5
set rbox_llx [dbGet [dbGet -p top.insts.name corner_ul].box_urx]
set rbox_lly [expr [dbGet [dbGet -p top.insts.name corner_ul].box_lly] - $blockage_width_top]
set rbox_urx [dbGet [dbGet -p top.insts.name ring_terminator_top].box_urx]
set rbox_ury [dbGet [dbGet -p top.insts.name ring_terminator_top].box_lly]
createRouteBlk \
    -name pad_route_block_top \
    -layer {m1 m2 m3 m4 m6 m7 m8} \
    -box "$rbox_llx $rbox_lly $rbox_urx $rbox_ury"

# ------------ bottom: signals on m3/m5
set rbox_llx [dbGet [dbGet -p top.insts.name ring_terminator_bottom].box_llx]
set rbox_lly [dbGet [dbGet -p top.insts.name ring_terminator_bottom].box_ury]
set rbox_urx [dbGet [dbGet -p top.insts.name corner_lr].box_llx]
set rbox_ury [expr [dbGet [dbGet -p top.insts.name corner_lr].box_ury] + $blockage_width_bottom]
createRouteBlk \
    -name pad_route_block_bottom \
    -layer {m1 m2 m3 m4 m6 m7 m8} \
    -box "$rbox_llx $rbox_lly $rbox_urx $rbox_ury"

foreach_in_collection x [get_nets pad_*] {
  setAttribute -net [get_property $x full_name] -skip_routing true
}