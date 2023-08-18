#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.
#
# Author : Christopher Torng
# Date   : March 26, 2018

if { [info exists ::env(WHICH_SOC)] } {
    set WHICH_SOC $::env(WHICH_SOC)
} else {
    set WHICH_SOC "onyx"
}

#-------------------------------------------------------------------------
# Floorplan variables
#-------------------------------------------------------------------------

# Density target: width will be adjusted to meet this cell density
set core_density_target $::env(core_density_target); # Placement density of 65% is reasonable
# Core height : number of vertical pitches in height of core area
# We fix this value because the height of the memory and PE tiles
# must be the same to allow for abutment at the top level

# Maintain even row height for power domains
set core_height 226; # For gf12, specifically
if { $WHICH_SOC == "amber" } { set core_height 150 }

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

if { $WHICH_SOC == "amber" } {
# 10/2022 steveri
# Latest RTL gives width 124, builds array bigger than the chip :(
# PE width 124 routes in 20 min, but then array is too big.
# PE width 105 takes over 5 hours to route. So that's too small.
# PE width 110 routes in 40 min, Let's use that as a max width, see what happens.
# (Even though I set it to 110, it comes out 112 in the report, not sure why?)
set max_width 110
if { $width > $max_width } {
    set new_density [expr $total_cell_area / $width / $height]
    echo "+++ PE too wide"
    echo "Wanted width $width for density target $core_density_target"
    echo "But width > 110 disallowed (Tile_PE/custom-init/outputs/floorplan.tcl)"
    echo "So now using width $width for new density $new_density"
    set width $max_width
}
}

# Core bounding box margins
set core_margin_t $vert_pitch
set core_margin_b $vert_pitch 
set core_margin_r [expr 4 * $horiz_pitch]
set core_margin_l [expr 4 * $horiz_pitch]

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

floorPlan -s $width $height \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

