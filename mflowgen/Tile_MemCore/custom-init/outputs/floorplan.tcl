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

set core_width  [expr 392 * $tech_pitch_x - $core_margin_left - $core_margin_right]
set core_height [expr 300 * $tech_pitch_y - $core_margin_top - $core_margin_bottom]

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
set sram_spacing_x_even [expr 200 * $hori_pitch]

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

# snap the 2x height
set sram_start_y [snap_to_grid [expr ([dbGet top.fPlan.box_sizey] - $block_height)/2.] [expr $vert_pitch*2]]
set sram_start_x [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $block_width)/2.] $hori_pitch]

set y_loc $sram_start_y
set x_loc $sram_start_x
set col 0
set row 0
foreach_in_collection sram $srams {
  set sram_name [get_property $sram full_name]
  if {[expr $col % 2] == 1} {
    placeInstance $sram_name [expr $x_loc + $hori_pitch] $y_loc -fixed
  } else {
    placeInstance $sram_name [expr $x_loc - $hori_pitch] $y_loc MY -fixed
  }
  # create Halo around the SRAM
  set halo_left   $tech_pitch_x
  set halo_bottom $tech_pitch_y 
  set halo_right  $tech_pitch_x 
  set halo_top    [expr $tech_pitch_y + $vert_pitch]
  addHaloToBlock \
      $halo_left \
      $halo_bottom \
      $halo_right \
      $halo_top \
      -snapToSite \
      $sram_name

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
