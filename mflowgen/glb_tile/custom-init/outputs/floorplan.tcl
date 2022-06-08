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

set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set horiz_pitch [dbGet top.fPlan.coreSite.size_x]

# Core bounding box margins

set core_margin_t $vert_pitch
set core_margin_b $vert_pitch 
set core_margin_r [expr 5 * $horiz_pitch]
set core_margin_l [expr 5 * $horiz_pitch]

# Amount of space between SRAM banks and core area
# boundary on each side
set sram_margin_t [expr 4 * $vert_pitch]
set sram_margin_b [expr 150 * $vert_pitch]
set sram_margin_r [expr 175 * $horiz_pitch] 
set sram_margin_l [expr 175 * $horiz_pitch]

# Get the SRAMs and use both them and floorplan vars to determine 
# necessary tile size
set srams [get_cells -hierarchical *sram_array*]
set sram_width [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_y]
set sram_spacing_y 0
# Magic numbers, see https://github.com/StanfordAHA/garnet/issues/804
set sram_spacing_x_odd  15
set sram_spacing_x_even 15
# Bank height from env var; currently 8 (see glb_tile/construct.py)
set bank_height $::env(bank_height)

# Center the SRAMs within the core area of the tile
# Number of banks here = number of columns of SRAMs. If the bank height isn't
# a factor of the number of SRAMs, one columb will be incomplete, but it's
# still a column we must account for in placeing SRAMs and
# determining floorplan size
set num_banks [expr int(ceil([sizeof_collection $srams] / double($bank_height)))]
set num_spacings [expr $num_banks - 1]
set num_even_spacings [expr int(ceil($num_spacings/2.0))]
set num_odd_spacings [expr $num_spacings/2]
set total_spacing_width [expr ($num_odd_spacings * $sram_spacing_x_odd) + ($num_even_spacings * $sram_spacing_x_even)]
set block_width [expr ($num_banks * $sram_width) + $total_spacing_width]
set block_height [expr ($sram_height * $bank_height) + ($sram_spacing_y * ($bank_height - 1))]

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

set core_width [expr $block_width + $sram_margin_l + $sram_margin_r]
set core_height [expr $block_height + $sram_margin_t + $sram_margin_b]
puts "@file_info glb_tile core_width= $core_width, core_height=$core_height"

floorPlan -s $core_width $core_height \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

# Use automatic floorplan synthesis to pack macros (e.g., SRAMs) together

planDesign

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

# Use margin variables to determine sram start location
set sram_start_y [snap_to_grid [expr $core_margin_b + $sram_margin_b] $vert_pitch]
set sram_start_x [snap_to_grid [expr $core_margin_l + $sram_margin_l] $horiz_pitch]

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

