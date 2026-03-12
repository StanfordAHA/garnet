deletePlaceBlockage pe_array_placement_blockage

#------------------- After the power mesh, add the placement blockage
# I don't know why the placement blockage will block the power mesh
# so I have to add it after the power mesh...
# This blockage should be removed at the end of placement
set design_llx [dbGet top.fPlan.box_llx]
set design_lly [dbGet top.fPlan.box_lly]
set design_urx [dbGet top.fPlan.box_urx]
set design_ury [dbGet top.fPlan.box_ury]

# set pe_lower_left  [get_cells -hierarchical -filter {is_macro_cell==true} *pe_2016]
# set pe_upper_right [get_cells -hierarchical -filter {is_macro_cell==true} *pe_31]
# set pb_llx [get_property $pe_lower_left  x_coordinate_min]
# set pb_lly [get_property $pe_lower_left  y_coordinate_min]
# set pb_urx [get_property $pe_upper_right x_coordinate_max]
# set pb_ury [get_property $pe_upper_right y_coordinate_max]
set pe_lower_left  [get_property [get_cells -hierarchical -filter {is_macro_cell==true} *pe_2016] full_name]
set pe_upper_right [get_property [get_cells -hierarchical -filter {is_macro_cell==true} *pe_31] full_name]
set pb_llx  [dbGet [dbGet -p top.insts.name $pe_lower_left].box_llx]
set pb_lly  [dbGet [dbGet -p top.insts.name $pe_lower_left].box_lly]
set pb_urx  [dbGet [dbGet -p top.insts.name $pe_upper_right].box_urx]
set pb_ury  [dbGet [dbGet -p top.insts.name $pe_upper_right].box_ury]

set pb_llx [expr $pb_llx - 2.16]
set pb_lly [expr $pb_lly - 2.16]
set pb_urx [expr $pb_urx + 2.16]
set pb_ury [expr $pb_ury + 2.16]

createPlaceBlockage \
    -box [list $pb_llx $pb_lly $design_urx $pb_ury] \
    -type soft \
    -name pe_array_placement_blockage