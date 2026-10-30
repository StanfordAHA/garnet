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
set core_margin_r [expr 10 * $horiz_pitch]
set core_margin_l [expr 10 * $horiz_pitch]

#-------------------------------------------------------------------------
# Grow the die to fit the edge pins (only if they don't fit)
#-------------------------------------------------------------------------
# pin-assignments.tcl spreads the switch-box pins one per routing track:
# left/right on M6 over the two halves of [5, die_h - 15] (SB_IN / SB_OUT),
# top/bottom on M5 over [5, die_w - 5] (SB and config pins together). An RV
# dw64 tile has 345 pins per left/right half (5 x (64 + valid + ready) + 5 x 3
# one-bit) but 341 M6 tracks at the fixed core_height (the Tile_MemCore
# thesis_dse dw64 fit tile failed there, IMPPTN-970). Grow height (even rows)
# or width just enough, with 2 tracks of slack. Keep these ranges and pin
# lists in step with pin-assignments.tcl. A tile whose pins fit is
# byte-identical. editPin's M5/M6 are the 5th/6th routing layers (gf12: C5,
# 0.080 vertical; K1, 0.128 horizontal).
proc _fp_layer_pitch {n dir} {
  foreach l [dbGet -p head.layers.type routing] {
    if { [dbGet $l.num] == $n } { return [dbGet $l.pitch$dir] }
  }
  return 0
}
set _fp_pitch_lr [_fp_layer_pitch 6 Y]
set _fp_pitch_tb [_fp_layer_pitch 5 X]
if { $_fp_pitch_lr > 0 && $_fp_pitch_tb > 0 } {
  set _fp_n_lr 0
  foreach _fp_pat {SB_*_WEST_SB_IN* SB_*_WEST_SB_OUT* SB_*_EAST_SB_IN* SB_*_EAST_SB_OUT*} {
    set _fp_n [sizeof_collection [get_ports -quiet $_fp_pat]]
    if { $_fp_n > $_fp_n_lr } { set _fp_n_lr $_fp_n }
  }
  # each left/right half is die_h / 2 - 11 long
  set _fp_need_h [expr 2 * (($_fp_n_lr + 2) * $_fp_pitch_lr + 11) - $core_margin_t - $core_margin_b]
  if { $_fp_n_lr > 0 && $_fp_need_h > $height } {
    set _fp_old $height
    set height [expr ceil($_fp_need_h / (2 * $vert_pitch)) * 2 * $vert_pitch]
    puts "INFO: floorplan: grew die height for $_fp_n_lr pins per left/right half (M6 pitch $_fp_pitch_lr): core height $_fp_old -> $height"
  }
  set _fp_n_tb [expr max( \
    [sizeof_collection [get_ports -quiet {SB_*_NORTH_SB_IN* SB_*_NORTH_SB_OUT* clk clk_pass_through reset stall flush config_config_* config_read config_write read_config_data_in}]], \
    [sizeof_collection [get_ports -quiet {SB_*_SOUTH_SB_OUT* SB_*_SOUTH_SB_IN* clk_out clk_pass_through_out_bot reset_out stall_out flush_out config_out_config_* config_out_read config_out_write read_config_data}]])]
  set _fp_need_w [expr 10 + ($_fp_n_tb + 2) * $_fp_pitch_tb - $core_margin_l - $core_margin_r]
  if { $_fp_need_w > $width } {
    set _fp_old $width
    set width [expr ceil($_fp_need_w / $horiz_pitch) * $horiz_pitch]
    puts "INFO: floorplan: grew die width for $_fp_n_tb pins per top/bottom side (M5 pitch $_fp_pitch_tb): core width $_fp_old -> $width"
  }
} else {
  puts "WARNING: floorplan: no 5th/6th routing layer pitch from the tech LEF; edge-pin fit not checked"
}

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

floorPlan -s $width $height \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

