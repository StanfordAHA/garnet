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

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

set horiz_pitch [dbGet top.fPlan.coreSite.size_x]
set srams [get_cells *sram_array*]
set sram_width [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name *sram_array* -i 0].cell.size_y]
set sram_start_y [expr [dbGet top.fPlan.box_lly] + 20]
set sram_start_x [expr [dbGet top.fPlan.box_llx] + 20]
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

# Spread the ports for abutment.

set left [sort_collection [get_ports *_dwst*] hierarchical_name]
set right [sort_collection [get_ports *_dest*] hierarchical_name]
set top [get_ports -filter {hierarchical_name !~ *_dwst* && hierarchical_name !~ *_dest*}]

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

editPin -pin [get_property $left hierarchical_name] -start { 0 5 } -end [list 0 [expr {$height - 5}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6
editPin -pin [get_property $right hierarchical_name] -start [list $width  5] -end [list $width [expr {$height - 5}]] -side RIGHT -spreadType RANGE -spreadDirection counterclockwise -layer M6
editPin -pin [get_property $top hierarchical_name] -start [list 5 $height] -end [list [expr {$width - 5}] $height] -side TOP -spreadType RANGE -spreadDirection clockwise -layer M5

#source $vars(plug_dir)/tile_io_place.tcl
#set ns_io_offset [expr ($core_width - $ns_io_width) / 2] 
#set ew_io_offset [expr ($core_height - $ew_io_width) / 2]
#place_ios $width $height $ns_io_offset $ew_io_offset



