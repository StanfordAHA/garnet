This script is moved to power-strategy to avoid power grid creation problems.

# set design_llx [dbGet top.fPlan.box_llx]
# set design_lly [dbGet top.fPlan.box_lly]
# set design_urx [dbGet top.fPlan.box_urx]
# set design_ury [dbGet top.fPlan.box_ury]

# set pe_lower_left  [get_cells -hierarchical -filter {is_macro_cell==true} *pe_2016]
# set pe_upper_right [get_cells -hierarchical -filter {is_macro_cell==true} *pe_31]

# set pb_llx [get_property $pe_lower_left  x_coordinate_min]
# set pb_lly [get_property $pe_lower_left  y_coordinate_min]
# set pb_urx [get_property $pe_upper_right x_coordinate_max]
# set pb_ury [get_property $pe_upper_right y_coordinate_max]

# createPlaceBlockage \
#     -box [list $pb_llx $pb_lly $design_urx $pb_ury] \
#     -type hard \
#     -name pe_array_placement_blockage
