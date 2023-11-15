#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.

# Run this in floorplanning step to make io filler addition step happy
# (see add-io-fillers.tcl). Will be re-run in power step
delete_global_net_connections
# Standard cells
globalNetConnect VDD -type pgpin -pin vcc  -inst *
globalNetConnect VSS -type pgpin -pin vssx -inst *
# SRAMs
globalNetConnect VDD -type pgpin -pin vddp -inst *
globalNetConnect VSS -type pgpin -pin vss  -inst *
# IO Pads
globalNetConnect VDDPST -type pgpin -pin vccio -inst *
globalNetConnect VDD    -type pgpin -pin vcc   -inst *
globalNetConnect VSS    -type pgpin -pin vssp  -inst *
globalNetConnect VSS    -type pgpin -pin vssb  -inst *

set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set hori_pitch [dbGet top.fPlan.coreSite.size_x]

set fp_width          3924.72
set fp_height         4084.92
# set fp_margin_width   [expr 71.28 + 8 * $hori_pitch]
# set fp_margin_height  [expr 71.82 + 2 * $vert_pitch]
set die_ring_hori     16.2
set die_ring_vert     17.64
set prs_width         58.32
set prs_height        57.96
set fp_margin_width   [expr $die_ring_hori + $prs_width + 8 * $hori_pitch]
set fp_margin_height  [expr $die_ring_vert + $prs_height + 2 * $vert_pitch]

floorPlan \
    -coreMarginsBy die \
    -d ${fp_width} ${fp_height} ${fp_margin_width} ${fp_margin_height} ${fp_margin_width} ${fp_margin_height}

# loadIoFile inputs/io_file -noAdjustDieSize
source inputs/io_pad_placement.tcl

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

# check_floorplan
checkFPlan
