#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.
#
# Author : Christopher Torng
# Date   : March 26, 2018

#-------------------------------------------------------------------------
# Parameters
#-------------------------------------------------------------------------

set adk $::env(adk)

#-------------------------------------------------------------------------
# Floorplan variables
#-------------------------------------------------------------------------

# Density target: width will be adjusted to meet this cell density
set core_density_target $::env(core_density_target); # Placement density of 70% is reasonable
# Core height : number of vertical pitches in height of core area
# We fix this value because the height of the memory and PE tiles
# must be the same to allow for abutment at the top level

# Maintain even row height
# gf12 wants core_height 180, tsmc16 wants 150.
# Eventually this will be programmatical based on row_height or maybe a parameter
set core_height 180; # For gf12, specifically
if { $adk == "tsmc16" } { set core_height 150 }

set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set horiz_pitch [dbGet top.fPlan.coreSite.size_x]

# Calculate actual core height from height param
set height [expr $core_height * $vert_pitch]

# Now begin width calculation
# Get the combined area of all cells in the design
set cell_areas [get_property [get_cells *] area]
set total_cell_area 0
foreach area $cell_areas {
  set total_cell_area [expr $total_cell_area + $area]
}

# Calculate FP width that will meet density target given fixed height 
set width [expr $total_cell_area / $core_density_target / $height]

# Core bounding box margins

set core_margin_t $vert_pitch
set core_margin_b $vert_pitch 
set core_margin_r [expr 10 * $horiz_pitch]
set core_margin_l [expr 10 * $horiz_pitch]

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

floorPlan -s $width $height \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

# Place SRAMS
set srams [get_cells -quiet -hier -filter {is_memory_cell==true}]
set sram_name [lindex [get_property $srams name] 0]
set sram_width [dbGet [dbGet -p top.insts.name *$sram_name].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name *$sram_name].cell.size_y]

# SRAM Placement params
# SRAMs are abutted vertically
set sram_spacing_y 0
# We can abut sides of SRAMS with no pins
set sram_spacing_x_odd 0
# Set spacing between pinned sides of SRAMs to some 
# reasonable number of pitches
# Spread out further for power domains
if $::env(PWR_AWARE) {
  set sram_spacing_x_even [expr 300 * $horiz_pitch]
} else {
  set sram_spacing_x_even [expr 200 * $horiz_pitch]
}

# Parameter for how many SRAMs to stack vertically
set bank_height 1

# Center the SRAMs within the core area of the tile
set num_banks [expr [sizeof_collection $srams] / $bank_height]
set num_spacings [expr $num_banks - 1]
set num_even_spacings [expr int(ceil($num_spacings/2.0))]
set num_odd_spacings [expr $num_spacings/2]
set total_spacing_width [expr ($num_odd_spacings * $sram_spacing_x_odd) + ($num_even_spacings * $sram_spacing_x_even)]
set block_width [expr ($num_banks * $sram_width) + $total_spacing_width]
set block_height [expr ($sram_height * $bank_height) + ($sram_spacing_y * ($bank_height - 1))]

set sram_start_y [snap_to_grid [expr ([dbGet top.fPlan.box_sizey] - $block_height)/2.] $vert_pitch]
set sram_start_x [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $block_width)/2.] $horiz_pitch]

set y_loc $sram_start_y
set x_loc $sram_start_x
set col 0
set row 0
foreach_in_collection sram $srams {
  set sram_name [get_property $sram full_name]
  if {[expr $col % 2] == 1} {
    placeInstance $sram_name $x_loc $y_loc -fixed
  } else {
    placeInstance $sram_name $x_loc $y_loc MY -fixed
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

# Make total height of the SRAMs including the boundary cells even
# so it doesn't block placement of a power switch that is inserted
# on the even row, else a power switch won't be inserted on that
# column for that row that can cause LUP DRCs

if $::env(PWR_AWARE) {
  addHaloToBlock -allMacro [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] [expr $vert_pitch * 2]
} else {
  addHaloToBlock -allMacro [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch
}

