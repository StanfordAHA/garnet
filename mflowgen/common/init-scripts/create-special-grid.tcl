#=========================================================================
# create-special-grid.tcl
#=========================================================================
# This script is used to create a special layer that is required by the
# technology.
# Author : 
# Date   : 

set chip_llx [dbGet top.fPlan.box_llx]
set chip_lly [dbGet top.fPlan.box_lly]
set chip_urx [dbGet top.fPlan.box_urx]
set chip_ury [dbGet top.fPlan.box_ury]

# Parameters borrowed from Intel reference flow
set step          $ADK_SPCL_LAYER_STEP
set width         $ADK_SPCL_LAYER_WIDTH
set margin_bottom $ADK_SPCL_LAYER_MARGIN_BOTTOM
set margin_top    $ADK_SPCL_LAYER_MARGIN_TOP

# delete existing deffCheck layer objects
editDelete -layer $ADK_SPCL_LAYER -net _NULL

# adding special layer to whole design
set loop_counter_y [expr $margin_bottom + $chip_lly]
while { $loop_counter_y < [expr $chip_ury - $margin_top] } {
  add_shape \
      -layer $ADK_SPCL_LAYER \
      -rect [list \
          $chip_llx \
          $loop_counter_y \
          $chip_urx \
          [expr $loop_counter_y + $ADK_SPCL_LAYER_WIDTH] \
      ]
  set loop_counter_y [expr $loop_counter_y + $step]
}

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

# carve out the special layer over macros
# get the list of macros in the design
set macro_list [get_db insts -if {.base_cell.base_class == block}]
foreach macro $macro_list {
  # macro may have hierarchy, so we need to get the last element and use it as the regex filter
  # ex: insts:top/all/the/way/down/to/this/macro
  # set macro [lindex [split $macro ":"] end]
  set split_list [split $macro "/"]
  set macro [join [lrange $split_list 1 end] "/"]
  puts "macro: $macro"

  # how it works?
  # "dbGet top.insts.name $macro": use $macro to filter out the instances that have the name "$macro"
  # "-p" option will take you back up one hierarchy (such that you can access other properties)
  # thus, "dbGet -p top.insts.name $macro" will give you the instance object that has a name $macro
  # Finally, .box can be used to access its bounding box property
  set macro_box [list \
    [dbGet [dbGet -p top.insts.name *$macro].box_llx] \
    [dbGet [dbGet -p top.insts.name *$macro].box_lly] \
    [dbGet [dbGet -p top.insts.name *$macro].box_urx] \
    [dbGet [dbGet -p top.insts.name *$macro].box_ury] \
  ]
  puts $macro_box
  carve_out_special_layer_in $macro_box $ADK_SPCL_LAYER $ADK_SPCL_LAYER_WIDTH
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