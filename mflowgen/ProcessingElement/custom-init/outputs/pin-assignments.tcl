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
set weight_in    [get_ports {weight_in*}]
set weight_out   [get_ports {weight_out*}]
set input_in     [get_ports {input_in*}]
set input_out    [get_ports {input_out*}]
set psum_in      [get_ports {psum_in*}]
set psum_out     [get_ports {psum_out*}]

#-------------------------------------------------------------------------
# Pins
#-------------------------------------------------------------------------
# top/bottom pins
set pins_top    [lsort -dictionary [get_property [concat $weight_in $psum_in] hierarchical_name]]
set pins_bottom [lsort -dictionary [get_property [concat $weight_out $psum_out] hierarchical_name]]
# left/right pins
set pins_left   [lsort -dictionary -decreasing [get_property [concat $input_in] hierarchical_name]]
set pins_right  [lsort -dictionary -decreasing [get_property [concat $input_out] hierarchical_name]]

#-------------------------------------------------------------------------
# Top/Bottom Pin Placement
#-------------------------------------------------------------------------
set track_pitch 0.09
set start_pos [expr $track_pitch * 39]

editPin \
    -layer           M3 \
    -side            TOP \
    -spreadType      START \
    -start           [list $start_pos $block_height] \
    -unit            TRACK \
    -snap            TRACK \
    -spacing         6 \
    -pin             $pins_top

editPin \
    -layer           M3 \
    -side            BOTTOM \
    -spreadType      START \
    -start           [list $start_pos 0] \
    -unit            TRACK \
    -snap            TRACK \
    -spacing         6 \
    -spreadDirection counterclockwise \
    -pin             $pins_bottom

#-------------------------------------------------------------------------
# Left/Right Pin Placement
#-------------------------------------------------------------------------
set track_pitch 0.09
set start_pos [expr $track_pitch * 30]

editPin \
    -layer           M4 \
    -side            LEFT \
    -spreadType      START \
    -start           [list 0 $start_pos] \
    -unit            TRACK \
    -snap            TRACK \
    -spacing         21 \
    -pin             $pins_left

editPin \
    -layer           M4 \
    -side            RIGHT \
    -spreadType      START \
    -start           [list $block_width $start_pos] \
    -unit            TRACK \
    -snap            TRACK \
    -spacing         21 \
    -spreadDirection counterclockwise \
    -pin             $pins_right

#-------------------------------------------------------------------------
# Clock / Reset Pin Placement
#-------------------------------------------------------------------------
editPin \
    -layer           M6 \
    -side            LEFT \
    -spreadType      START \
    -start           [list 0 12.5] \
    -snap            TRACK \
    -pin             rstn

editPin \
    -layer           M6 \
    -side            RIGHT \
    -spreadType      START \
    -start           [list $block_width 12.5] \
    -snap            TRACK \
    -spreadDirection counterclockwise \
    -pin             clk


#-------------------------------------------------------------------------
# Batch Mode End
#-------------------------------------------------------------------------
setPinAssignMode -pinEditInBatch false
