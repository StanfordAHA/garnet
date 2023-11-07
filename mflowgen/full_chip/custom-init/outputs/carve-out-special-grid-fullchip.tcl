#=========================================================================
# carve-out-special-grid-fullchip.tcl
#=========================================================================
# This script is used to carve out the special layer on the pads and die-
# ring area.
# Author : 
# Date   : 

# This process is used to carve out the special layer within a given box area
# box: a list of 4 elements, representing the bounding box of the area
# layer_width: the width of the special layer
proc carve_out_special_layer_in { box layer_name layer_width } {
  set box_extended [list \
    [expr [lindex $box 0] - $layer_width] \
    [expr [lindex $box 1] - $layer_width] \
    [expr [lindex $box 2] + $layer_width] \
    [expr [lindex $box 3] + $layer_width] \
  ]
  # --- select the shapes
  editSelect -layer $layer_name -net _NULL
  # --- cut the shapes, such that they can be deleted without affecting others
  editCutWire -selected -box $box
  # --- delete the shapes inside the box area
  editDelete -layer $layer_name -net _NULL -area $box_extended
}

# carve out the diff check on die ring & PRS
# TODO: add an if-else check because this is only need in top level
set die_width [dbGet top.fPlan.box_urx]
set die_height [dbGet top.fPlan.box_ury]
set die_ring_hori 16.2
set die_ring_vert 17.64
set prs_width     58.32
set prs_height    57.96

# die ring
set die_ring_box_left [list \
  [expr 0                           ] \
  [expr 0                           ] \
  [expr $die_ring_hori              ] \
  [expr $die_height                 ] \
]
set die_ring_box_right [list \
  [expr $die_width - $die_ring_hori ] \
  [expr 0                           ] \
  [expr $die_width                  ] \
  [expr $die_height                 ] \
]
set die_ring_box_bottom [list \
  [expr 0                           ] \
  [expr 0                           ] \
  [expr $die_width                  ] \
  [expr $die_ring_vert              ] \
]
set die_ring_box_top [list \
  [expr 0                           ] \
  [expr $die_height - $die_ring_vert] \
  [expr $die_width                  ] \
  [expr $die_height                 ] \
]
carve_out_special_layer_in $die_ring_box_left   $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
carve_out_special_layer_in $die_ring_box_right  $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
carve_out_special_layer_in $die_ring_box_bottom $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
carve_out_special_layer_in $die_ring_box_top    $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH

# PRS
set prs_box_ll [list \
  [expr $die_ring_hori] \
  [expr $die_ring_vert] \
  [expr $die_ring_hori + $prs_width] \
  [expr $die_ring_vert + $prs_height] \
]
set prs_box_ur [list \
  [expr $die_width - $die_ring_hori - $prs_width] \
  [expr $die_height - $die_ring_vert - $prs_height] \
  [expr $die_width - $die_ring_hori] \
  [expr $die_height - $die_ring_vert] \
]
carve_out_special_layer_in $prs_box_ll $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
carve_out_special_layer_in $prs_box_ur $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH

# Pads
set pad_box_bottom [list \
  [expr [dbGet [dbGet -p top.insts.name ring_terminator_bottom].box_llx] ] \
  [expr [dbGet [dbGet -p top.insts.name ring_terminator_bottom].box_lly] ] \
  [expr [dbGet [dbGet -p top.insts.name corner_lr].box_urx] ] \
  [expr [dbGet [dbGet -p top.insts.name corner_lr].box_ury] ] \
]
set pad_box_left [list \
  [expr [dbGet [dbGet -p top.insts.name ring_terminator_left].box_llx] ] \
  [expr [dbGet [dbGet -p top.insts.name ring_terminator_left].box_lly] ] \
  [expr [dbGet [dbGet -p top.insts.name corner_ul].box_urx] ] \
  [expr [dbGet [dbGet -p top.insts.name corner_ul].box_ury] ] \
]
set pad_box_right [list \
  [expr [dbGet [dbGet -p top.insts.name corner_lr].box_llx] ] \
  [expr [dbGet [dbGet -p top.insts.name corner_lr].box_lly] ] \
  [expr [dbGet [dbGet -p top.insts.name ring_terminator_right].box_urx] ] \
  [expr [dbGet [dbGet -p top.insts.name ring_terminator_right].box_ury] ] \
]
set pad_box_top [list \
  [expr [dbGet [dbGet -p top.insts.name corner_ul].box_llx] ] \
  [expr [dbGet [dbGet -p top.insts.name corner_ul].box_lly] ] \
  [expr [dbGet [dbGet -p top.insts.name ring_terminator_top].box_urx] ] \
  [expr [dbGet [dbGet -p top.insts.name ring_terminator_top].box_ury] ] \
]
carve_out_special_layer_in $pad_box_bottom $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
carve_out_special_layer_in $pad_box_left   $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
carve_out_special_layer_in $pad_box_right  $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
carve_out_special_layer_in $pad_box_top    $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
