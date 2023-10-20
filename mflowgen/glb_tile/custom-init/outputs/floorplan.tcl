#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.
#
# Author : James Thomas, Alex Carsello
# Date   : November 2019

#-------------------------------------------------------------------------
# Floorplan variables
#-------------------------------------------------------------------------
 
set hori_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set tech_pitch_x [expr 5 * $hori_pitch]
set tech_pitch_y [expr 1 * $vert_pitch]

set core_margin_left   $tech_pitch_x
set core_margin_bottom $tech_pitch_y
set core_margin_right  $tech_pitch_x
set core_margin_top    $tech_pitch_y

set core_width  [expr 490 * $tech_pitch_x - $core_margin_left - $core_margin_right]
set core_height [expr 900 * $tech_pitch_y - $core_margin_top - $core_margin_bottom]

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

floorPlan -s $core_width $core_height \
             $core_margin_left $core_margin_bottom $core_margin_right $core_margin_top

setFlipping s

#-------------------------------------------------------------------------
# SRAM Placement
#-------------------------------------------------------------------------
proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}
set floorplan_width [dbGet top.fPlan.box_urx]
set floorplan_height [dbGet top.fPlan.box_ury]
set sram_width [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_y]

# compute the gap between each SRAM
set gap_x [expr ($floorplan_width - $sram_width * 1) / 2.0]
set gap_y [expr ($floorplan_height - $sram_height * 4) / 5.0]

# loop through each SRAM and place it
set x_loc $gap_x
set y_loc $gap_y
# DRC Fix: Looks like the power stripes happens to connect to the "tip"
#          of the SRAM power pin (vddp). This causes several DRC on v4/m5
#          because the overlap region is too small.
#          To fix this, we move the SRAM x-location a little bit to the left
#          such that the power stripe and power pin can have a nice cross
#          overlap.
set x_loc [expr $x_loc - 5 * $hori_pitch]
foreach_in_collection sram [get_cells -hierarchical *sram_array*] {
  set sram_name [get_property $sram full_name]
  set x_loc_snap [snap_to_grid $x_loc [expr 2*$hori_pitch]]
  set y_loc_snap [snap_to_grid $y_loc [expr 2*$vert_pitch]]
  placeInstance $sram_name $x_loc_snap $y_loc_snap -fixed
  set y_loc [expr $y_loc + $sram_height + $gap_y]
}

# Add placement blockages around the SRAMs
addHaloToBlock \
    -allMacro \
    [expr $hori_pitch * 4] \
    $vert_pitch \
    [expr $hori_pitch * 4] \
    1.53
