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

set tile_separation_x 0
set tile_separation_y 0
set grid_margin_t 50
set grid_margin_b 50
set grid_margin_l 200
set grid_margin_r 200

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

set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set horiz_pitch [dbGet top.fPlan.coreSite.size_x]
set savedvars(vert_pitch) $vert_pitch
set savedvars(horiz_pitch) $horiz_pitch

set min_col 99999
set min_row 99999
set max_row -99999
set max_col -99999
foreach_in_collection tile [get_cells -hier -filter "ref_name=~Tile_PE* || ref_name=~Tile_MemCore*"] {
  set tile_name [get_property $tile full_name]
  regexp {X(\S*)_} $tile_name -> col
  regexp {Y(\S*)} $tile_name -> row

  # Convert hex IDs to decimal
  set row [expr 0x$row + 0]
  set col [expr 0x$col + 0]

  set tiles($row,$col,name) $tile_name
  set tiles($row,$col,width) [dbGet [dbGet -p top.insts.name $tile_name -i 0].cell.size_x]
  set tiles($row,$col,height) [dbGet [dbGet -p top.insts.name $tile_name -i 0].cell.size_y]

  # grid height = max row value
  if {$row > $max_row} {
    set max_row $row
  }
  if {$row < $min_row} {
    set min_row $row
  }
  if {$col > $max_col} {
    set max_col $col
  }
  if {$col < $min_col} {
    set min_col $col
  }
}

# Get grid height/width from max_row/col
set grid_num_rows [expr $max_row - $min_row + 1]
set grid_num_cols [expr $max_col - $min_col + 1]
# Multiply separation params by respective pitches to calculate actual separation numbers
set tile_separation_x [expr $tile_separation_x * $horiz_pitch]
set tile_separation_y [expr $tile_separation_y * $vert_pitch]
# Calculate the height and width of the full array of tiles including any inter-tile spacing
set grid_height 0
for {set i $min_row} {$i <= $max_row} {incr i} {
  set grid_height [expr $grid_height + $tiles($i,$min_col,height) + $tile_separation_y]
}
# Subtract the spacing for the last tile for correct size
set grid_height [expr $grid_height - $tile_separation_y]

set grid_width 0
for {set i $min_col} {$i <= $max_col} {incr i} {
  set grid_width [expr $grid_width + $tiles($min_row,$i,width) + $tile_separation_x]
}
# Subtract the spacing for the last tile for correct size
set grid_width [expr $grid_width - $tile_separation_x]

# Now use the width of the grid and the specified margins to calculate floorplan size
set grid_margin_t [expr $grid_margin_t * $vert_pitch]
set grid_margin_b [expr $grid_margin_b * $vert_pitch]
set grid_margin_l [expr $grid_margin_l * $horiz_pitch]
set grid_margin_r [expr $grid_margin_r * $horiz_pitch]

floorPlan -s [expr $grid_width + $grid_margin_l + $grid_margin_r] \
             [expr $grid_height + $grid_margin_t + $grid_margin_b] \
             $core_margin_l $core_margin_b $core_margin_r $core_margin_t

setFlipping s

# Now, actually place the CGRA tiles
set start_x [expr $core_margin_l + $grid_margin_l]
set start_y [expr $core_margin_b + $grid_margin_b]
set y_loc $start_y
for {set row $max_row} {$row >= $min_row} {incr row -1} {
  set x_loc $start_x
  for {set col $min_col} {$col <= $max_col} {incr col} {
    set tiles($row,$col,x_loc) $x_loc
    set tiles($row,$col,y_loc) $y_loc
    placeInstance $tiles($row,$col,name) $x_loc $y_loc -fixed
    set x_loc [expr $x_loc + $tiles($row,$col,width) + $tile_separation_x]
  }
  set y_loc [expr $y_loc + $tiles($row,$min_col,height) + $tile_separation_y]
}

addHaloToBlock -allMacro [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch

# Manually connect all of the tile_id pins
selectPin *tile_id*
set tile_id_pin [dbGet selected -i 0]
set pin_depth [dbGet $tile_id_pin.cellTerm.pins.allShapes.shapes.rect_sizex -i 0]
set connection_layer [dbGet $tile_id_pin.layer.name]
set connection_width [expr 2 * [dbGet $tile_id_pin.layer.minWidth]]
for {set row $min_row} {$row <= $max_row} {incr row} {
  for {set col $min_col} {$col <= $max_col} {incr col} {
    set tile_id_pins [get_pins $tiles($row,$col,name)/tile_id*]
    set num_id_pins [sizeof_collection $tile_id_pins]
    # The ID pins are on the left side of the tile,
    # all have same x coordinate as the tile itself
    set id_pin_x [dbGet [dbGet top.insts.name -p $tiles($row,$col,name)].box_llx]
    for {set index 0} {$index < $num_id_pins} {incr index} {
      set id_pin [index_collection $tile_id_pins [expr $num_id_pins - $index - 1]]
      set id_pin_y [get_property $id_pin y_coordinate]
      set id_net [get_net -of_objects $id_pin]
      set id_net_name [get_property $id_net hierarchical_name]
      set tie_pin [get_pins -of_objects $id_net -filter "hierarchical_name!~*id*"] 
      set tie_pin_y [get_property $tie_pin y_coordinate]
      set llx [expr $id_pin_x]
      set urx [expr $llx + $connection_width]
      set lly [expr min($tie_pin_y, $id_pin_y)]
      set ury [expr max($tie_pin_y, $id_pin_y)]
      add_shape -net $id_net_name -layer $connection_layer -rect $llx $lly $urx $ury
    }
  }
}
deselectAll

