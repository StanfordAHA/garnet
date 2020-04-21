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

set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set horiz_pitch [dbGet top.fPlan.coreSite.size_x]

set core_margin_t $vert_pitch
set core_margin_b $vert_pitch 
set core_margin_r [expr 5 * $horiz_pitch]
set core_margin_l [expr 5 * $horiz_pitch]

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
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set srams [get_cells -hierarchical *sram_array*]
set sram_width [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_y]
set sram_spacing_y 0
set sram_spacing_x_even 0
# Magic number
set sram_spacing_x_odd 15
set bank_height 4

# Center the SRAMs within the core area of the tile
set num_banks [expr [sizeof_collection $srams] / $bank_height]
set num_spacings [expr $num_banks - 1]
set num_even_spacings [expr int(ceil($num_spacings/2.0))]
set num_odd_spacings [expr $num_spacings/2]
set total_spacing_width [expr ($num_odd_spacings * $sram_spacing_x_odd) + ($num_even_spacings * $sram_spacing_x_even)]
set block_width [expr ($num_banks * $sram_width) + $total_spacing_width]
set block_height [expr ($sram_height * $bank_height) + ($sram_spacing_y * ($bank_height - 1))]

# Put SRAMs more towards top of tile
set sram_start_y [snap_to_grid [expr 7 * ([dbGet top.fPlan.box_sizey] - $block_height)/8.] $vert_pitch]
#Center SRAMs horizontally
set sram_start_x [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $block_width)/2.] $horiz_pitch]

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

  # Create M3 pg net blockage to prevent DRC from interaction
  # with M5 stripes
  set llx [dbGet [dbGet -p top.insts.name $sram_name].box_llx]
  set lly [dbGet [dbGet -p top.insts.name $sram_name].box_lly]
  set urx [dbGet [dbGet -p top.insts.name $sram_name].box_urx]
  set ury [dbGet [dbGet -p top.insts.name $sram_name].box_ury]
  set tb_margin $vert_pitch
  set lr_margin [expr $horiz_pitch * 3]
  createRouteBlk \
    -inst $sram_name \
    -box [expr $llx - $lr_margin] [expr $lly - $tb_margin] [expr $urx + $lr_margin] [expr $ury + $tb_margin] \
    -layer 3 \
    -pgnetonly

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

addHaloToBlock -allMacro [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch

