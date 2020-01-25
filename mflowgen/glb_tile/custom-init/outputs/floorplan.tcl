#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.
#
# Author : Christopher Torng
# Date   : March 26, 2018

#-------------------------------------------------------------------------
# Floorplan variables
#-------------------------------------------------------------------------

# Set the floorplan to target a reasonable placement density with a good
# aspect ratio (height:width). An aspect ratio of 2.0 here will make a
# rectangular chip with a height that is twice the width.

set core_aspect_ratio   1.00; # Aspect ratio 1.0 for a square chip
set core_density_target 0.70; # Placement density of 70% is reasonable

# Make room in the floorplan for the core power ring

set pwr_net_list {VDD VSS}; # List of power nets in the core power ring

set M1_min_width   [dbGet [dbGetLayerByZ 1].minWidth]
set M1_min_spacing [dbGet [dbGetLayerByZ 1].minSpacing]

set savedvars(p_ring_width)   [expr 48 * $M1_min_width];   # Arbitrary!
set savedvars(p_ring_spacing) [expr 24 * $M1_min_spacing]; # Arbitrary!

# Core bounding box margins

set core_margin_t [expr ([llength $pwr_net_list] * ($savedvars(p_ring_width) + $savedvars(p_ring_spacing))) + $savedvars(p_ring_spacing)]
set core_margin_b [expr ([llength $pwr_net_list] * ($savedvars(p_ring_width) + $savedvars(p_ring_spacing))) + $savedvars(p_ring_spacing)]
set core_margin_r [expr ([llength $pwr_net_list] * ($savedvars(p_ring_width) + $savedvars(p_ring_spacing))) + $savedvars(p_ring_spacing)]
set core_margin_l [expr ([llength $pwr_net_list] * ($savedvars(p_ring_width) + $savedvars(p_ring_spacing))) + $savedvars(p_ring_spacing)]

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

set core_width $::env(core_width)
set core_height $::env(core_height)

floorPlan -s $core_width $core_height \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t
#floorPlan -r $core_aspect_ratio $core_density_target \
#             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

# Use automatic floorplan synthesis to pack macros (e.g., SRAMs) together

planDesign

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

set horiz_pitch [dbGet top.fPlan.coreSite.size_x]
set srams [get_cells *sram_array*]
set sram_width [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_y]
set sram_start_y [expr [dbGet top.fPlan.box_lly] + 50]
set sram_start_x [expr [dbGet top.fPlan.box_llx] + 50]
set sram_spacing_y 0
set sram_spacing_x_even 0
# Magic number
set sram_spacing_x_odd 5
set bank_height 8

set y_loc $sram_start_y
set x_loc $sram_start_x
set col 0
set row 0
foreach_in_collection sram $srams {
  set sram_name [get_property $sram full_name]
  # Does this line make sense?
  set y_loc [snap_to_grid $y_loc $horiz_pitch]
  if {[expr $col % 2] == 0} {
    placeInstance $sram_name $x_loc $y_loc MY -fixed
  } else {
    placeInstance $sram_name $x_loc $y_loc -fixed
  }
  set row [expr $row + 1]
  set y_loc [expr $y_loc + $sram_height + $sram_spacing_y]
  # Next column over
  if {$row >= $bank_height} {
    set row 0
    if {[expr $col % 2] == 0} {
      set sram_spacing_x $sram_spacing_x_even
    } else {
      set sram_spacing_x $sram_spacing_x_odd
    }
    set x_loc [expr $x_loc + $sram_width + $sram_spacing_x]
    set y_loc $sram_start_y
    set col [expr $col + 1]
  }
}

set horiz_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
addHaloToBlock -allMacro [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch

