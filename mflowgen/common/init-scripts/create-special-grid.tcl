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
          [expr $loop_counter_y + $width] \
      ]
  set loop_counter_y [expr $loop_counter_y + $step]
}

# carve out the special layer over macros
# get the list of macros in the design
set macro_list []
foreach macro $macro_list {
  # how it works?
  # "dbGet top.insts.name $macro": use $macro to filter out the instances that have the name "$macro"
  # "-p" option will take you back up one hierarchy (such that you can access other properties)
  # thus, "dbGet -p top.insts.name $macro" will give you the instance object that has a name $macro
  # Finally, .box can be used to access its bounding box property
  set macro_box_llx [dbGet [dbGet -p top.insts.name $macro].box_llx]
  set macro_box_lly [dbGet [dbGet -p top.insts.name $macro].box_lly]
  set macro_box_urx [dbGet [dbGet -p top.insts.name $macro].box_urx]
  set macro_box_ury [dbGet [dbGet -p top.insts.name $macro].box_ury]

  set macro_box [list \
    $macro_box_llx \
    $macro_box_lly \
    $macro_box_urx \
    $macro_box_ury \
  ]

  set macro_box_extended [list \
    [expr $macro_box_llx - $width] \
    [expr $macro_box_lly - $width] \
    [expr $macro_box_urx + $width] \
    [expr $macro_box_ury + $width] \
  ]

  # --- select the shapes
  editSelect -layer $ADK_SPCL_LAYER -net _NULL

  # --- cut the shapes, such that they can be deleted without affecting others
  editCutWire -selected -box $macro_box
  
  # --- delete the shapes inside the macro area
  editDelete -layer $ADK_SPCL_LAYER -net _NULL -area $macro_box_extended
}
