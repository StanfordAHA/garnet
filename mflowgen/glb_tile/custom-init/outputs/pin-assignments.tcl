#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

# Spread the ports for abutment.

set left [sort_collection [get_ports *_dwst*] hierarchical_name]
set right [sort_collection [get_ports *_dest*] hierarchical_name]
set top [get_ports -filter {hierarchical_name !~ *_dwst* && hierarchical_name !~ *_dest*}]

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

editPin -pin [get_property $left hierarchical_name] -start { 0 5 } -end [list 0 [expr {$height - 5}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6
editPin -pin [get_property $right hierarchical_name] -start [list $width  5] -end [list $width [expr {$height - 5}]] -side RIGHT -spreadType RANGE -spreadDirection counterclockwise -layer M6
editPin -pin [get_property $top hierarchical_name] -start [list 5 $height] -end [list [expr {$width - 5}] $height] -side TOP -spreadType RANGE -spreadDirection clockwise -layer M5

