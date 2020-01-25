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



