#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

# Take all ports and split into halves

set all_ports       [dbGet top.terms.name -v *clk*]

set num_ports       [llength $all_ports]
set half_ports_idx  [expr $num_ports / 2]

set pins_left_half  [lrange $all_ports 0               [expr $half_ports_idx - 1]]
set pins_right_half [lrange $all_ports $half_ports_idx [expr $num_ports - 1]     ]

# Take all clock ports and place them center-left

set clock_ports     [dbGet top.terms.name *clk*]
set half_left_idx   [expr [llength $pins_left_half] / 2]

if { $clock_ports != 0 } {
  for {set i 0} {$i < [llength $clock_ports]} {incr i} {
    set pins_left_half \
      [linsert $pins_left_half $half_left_idx [lindex $clock_ports $i]]
  }
}

# Spread the ports for abutment.

# Buses with more than 10 bits will be out of order after the sort, but shouldn't be a big issue since
# the whole bus will still be together.
set north1 [sort_collection [get_ports SB_*_NORTH_SB_IN*] hierarchical_name]
set north2 [sort_collection [get_ports SB_*_NORTH_SB_OUT*] hierarchical_name]
set north_sb [concat $north1 $north2]
set north_config [sort_collection [get_ports {reset stall config_config_* config_read config_write read_config_data_in}] hierarchical_name]

set south1 [sort_collection [get_ports SB_*_SOUTH_SB_OUT*] hierarchical_name]
set south2 [sort_collection [get_ports SB_*_SOUTH_SB_IN*] hierarchical_name] 
set south_sb [concat $south1 $south2]
set south_config [sort_collection [get_ports {reset_out stall_out config_out_config_* config_out_read config_out_write read_config_data}] hierarchical_name]

set east1 [sort_collection [get_ports SB_*_EAST_SB_OUT*] hierarchical_name]
set east2 [sort_collection [get_ports SB_*_EAST_SB_IN*] hierarchical_name]

set west1 [sort_collection [get_ports SB_*_WEST_SB_IN*] hierarchical_name]
set west2 [sort_collection [get_ports SB_*_WEST_SB_OUT*] hierarchical_name]

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

# Assign top and bottom side pins
set tb_spread_min 5
set tb_spread_max [expr $width - 5]
set num_sb_pins [sizeof_collection $south_sb]
set num_config_pins [sizeof_collection $south_config]
set num_tb_pins [expr $num_sb_pins + $num_config_pins]
set split_point [expr double($num_sb_pins)/double($num_tb_pins)]
set tb_spread_mid [expr (($tb_spread_max - $tb_spread_min) * $split_point) + $tb_spread_min]

# Bottom pins
editPin -pin [get_property $south_sb hierarchical_name] -start [list $tb_spread_min 0] -end [list [expr {$tb_spread_mid - 1}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5

# clk_out in the middle of the bottom side
editPin -pin clk_out -assign [list $tb_spread_mid 0] -side BOTTOM -layer M5 -spreadDirection counterclockwise

editPin -pin [get_property $south_config hierarchical_name] -start [list [expr {$tb_spread_mid + 1}] 0] -end [list $tb_spread_max 0]  -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5

# Top pins
editPin -pin [get_property $north_sb hierarchical_name] -start [list $tb_spread_min $height] -end [list [expr {$tb_spread_mid - 1}] $height] -side TOP -spreadType RANGE -spreadDirection clockwise -layer M5
editPin -pin [get_property $north_config hierarchical_name] -start [list [expr {$tb_spread_mid + 1}] $height] -end [list $tb_spread_max $height]  -side TOP -spreadType RANGE -spreadDirection clockwise -layer M5

set lr_spread_min 5
set lr_spread_max [expr $height - 15]
set lr_spread_mid [expr ($lr_spread_min + $lr_spread_max) / 2]

# Assign left side pins
editPin -pin [get_property $west1 hierarchical_name] -start [list 0 $lr_spread_min ] -end [list 0 [expr {$lr_spread_mid - 1}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6

# Clk in the middle of the left side
editPin -pin clk -assign [list 0 $lr_spread_mid] -side LEFT -layer M6

editPin -pin [get_property $west2 hierarchical_name] -start [list 0 [expr $lr_spread_mid + 1] ] -end [list 0 $lr_spread_max] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6

# Assign right side pins
editPin -pin [get_property $east1 hierarchical_name] -start [list $width $lr_spread_min ] -end [list $width [expr {$lr_spread_mid - 1}]] -side RIGHT -spreadType RANGE -spreadDirection counterclockwise -layer M6
editPin -pin [get_property $east2 hierarchical_name] -start [list $width [expr $lr_spread_mid + 1] ] -end [list $width $lr_spread_max] -side RIGHT -spreadType RANGE -spreadDirection counterclockwise -layer M6

# These lists will be ordered from msb to lsb.
set tile_id [get_property [get_ports tile_id] hierarchical_name]
set hi [get_property [get_ports hi] hierarchical_name]
set lo [get_property [get_ports lo] hierarchical_name]
set tile_id_layer M6

set id_ports [lindex $hi 0]
for {set i 0} {$i < [llength $tile_id]} {incr i} {
  lappend id_ports [lindex $tile_id $i]
  if {$i % 2 == 0} {
    lappend id_ports [lindex $lo [expr {$i / 2}]]
  } else {
    lappend id_ports [lindex $hi [expr {$i / 2 + 1}]]
  }
}

editPin -pin $id_ports -start [list 0 [expr {$height - 14}]] -end [list 0 [expr {$height - 5}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer $tile_id_layer

# Add blockage in area near tile_id pins so we can route these at the top level
set tile_id_y_coords [get_property [get_ports {*tile_id* hi* lo*}] y_coordinate]
set tile_id_y_coords [lsort -real $tile_id_y_coords]
set tile_id_min_y [lindex $tile_id_y_coords 0]
set tile_id_max_y [lindex $tile_id_y_coords end]
selectIOPin *tile_id*
set tile_id_max_x [dbGet [dbGet selected -i 0].pins.allShapes.shapes.rect_urx]
deselectAll

createRouteBlk -name tile_id_rb -layer $tile_id_layer -box [list 0 $tile_id_min_y $tile_id_max_x $tile_id_max_y]
#create route blockage on other side of tile aligned with tile id pins
set horiz_pitch [dbGet top.fPlan.coreSite.size_x]
createRouteBlk -name tile_id_oppo -layer $tile_id_layer -box [list [expr $width - (5 * $horiz_pitch)] $tile_id_min_y $width $tile_id_max_y]
