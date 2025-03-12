#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : Po-Han Chen
# Date   : 

#-------------------------------------------------------------------------
# Batch Mode Start
#-------------------------------------------------------------------------
setPinAssignMode -pinEditInBatch true

#-------------------------------------------------------------------------
# Parameters
#-------------------------------------------------------------------------
# PE block dimensions
set block_width  [dbGet top.fPlan.box_urx]
set block_height [dbGet top.fPlan.box_ury]
# ports objects
set weight_in    [get_ports {weightIn*}]
set weight_out   [get_ports {weightOut*}]
set input_in     [get_ports {inputIn*}]
set input_out    [get_ports {inputOut*}]
set psum_in      [get_ports {psumIn*}]
set psum_out     [get_ports {psumOut*}]

#-------------------------------------------------------------------------
# Pins
#-------------------------------------------------------------------------
# top/bottom pins
set pins_top    [lsort -dictionary [get_property [concat $weight_in $psum_in] hierarchical_name]]
set pins_bottom [lsort -dictionary [get_property [concat $weight_out $psum_out] hierarchical_name]]
# add clk/rstn to the middle of the pin list
set pins_top    [linsert $pins_top [expr [llength $pins_top] / 2] clk]
set pins_bottom [linsert $pins_bottom [expr [llength $pins_bottom] / 2] rstn]
# left/right pins
set pins_left   [lsort -dictionary -decreasing [get_property [concat $input_in] hierarchical_name]]
set pins_right  [lsort -dictionary -decreasing [get_property [concat $input_out] hierarchical_name]]

#-------------------------------------------------------------------------
# Top/Bottom Pin Placement
#-------------------------------------------------------------------------
set gap_to_corner 1
set horiz_min $gap_to_corner
set horiz_max [expr $block_width - $gap_to_corner]

editPin \
    -layer           M3 \
    -side            TOP \
    -spreadType      RANGE \
    -start           [list $horiz_min $block_height] \
    -end             [list $horiz_max $block_height] \
    -snap            TRACK \
    -pin             $pins_top

editPin \
    -layer           M3 \
    -side            BOTTOM \
    -spreadType      RANGE \
    -start           [list $horiz_min 0] \
    -end             [list $horiz_max 0] \
    -spreadDirection counterclockwise \
    -snap            TRACK \
    -pin             $pins_bottom

#-------------------------------------------------------------------------
# Left/Right Pin Placement
#-------------------------------------------------------------------------
set gap_to_corner 2
set vert_min $gap_to_corner
set vert_max [expr $block_height - $gap_to_corner]

editPin \
    -layer           M4 \
    -side            LEFT \
    -spreadType      RANGE \
    -start           [list 0 $vert_min] \
    -end             [list 0 $vert_max] \
    -snap            TRACK \
    -pin             $pins_left

editPin \
    -layer           M4 \
    -side            RIGHT \
    -spreadType      RANGE \
    -start           [list $block_width $vert_min] \
    -end             [list $block_width $vert_max] \
    -spreadDirection counterclockwise \
    -snap            TRACK \
    -pin             $pins_right

#-------------------------------------------------------------------------
# Batch Mode End
#-------------------------------------------------------------------------
setPinAssignMode -pinEditInBatch false
