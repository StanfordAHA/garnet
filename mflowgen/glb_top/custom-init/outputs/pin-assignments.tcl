#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

editPin -pin [get_property [get_ports] hierarchical_name] -start [list 5 $height] -end [list [expr {$width - 5}] $height] -side TOP -spreadType RANGE -spreadDirection clockwise -layer M5

