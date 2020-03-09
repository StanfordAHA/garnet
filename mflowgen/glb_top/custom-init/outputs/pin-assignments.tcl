#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

set width [dbGet top.fPlan.box_urx]

editPin -pin [get_property [get_ports] hierarchical_name] -start [list 5 0] -end [list [expr {$width - 5}] 0] -side BOTTOM -spreadType RANGE -spreadDirection clockwise -layer M5

