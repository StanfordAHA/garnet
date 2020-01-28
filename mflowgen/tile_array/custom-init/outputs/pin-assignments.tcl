#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

set all_ports       [lsort [dbGet top.terms.name -v *clk*]]

set num_ports       [llength $all_ports]
set half_ports_idx  [expr $num_ports / 2]

# Take all clock ports and place them center-top

set clock_ports     [dbGet top.terms.name *clk*]

if { $clock_ports != 0 } {
  for {set i 0} {$i < [llength $clock_ports]} {incr i} {
    set all_ports \
      [linsert $all_ports $half_ports_idx [lindex $clock_ports $i]]
  }
}

set ports_layer M5
set offset_pitches 100
set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

set offset [expr $offset_pitches * $savedvars(horiz_pitch)]
set start $offset
set end [expr $width - $offset]
editPin -layer $ports_layer \
        -pin $all_ports \
        -side TOP \
        -start [list $start $height] \
        -end [list [expr $width - $offset] $height] \
        -spreadType RANGE \
        -spreadDirection clockwise
