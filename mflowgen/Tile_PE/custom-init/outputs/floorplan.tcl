#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.

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

set core_width  [expr 196 * $tech_pitch_x - $core_margin_left - $core_margin_right]
set core_height [expr 300 * $tech_pitch_y - $core_margin_top - $core_margin_bottom]
#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

floorPlan -s $core_width $core_height \
             $core_margin_left $core_margin_bottom $core_margin_right $core_margin_top

setFlipping s
