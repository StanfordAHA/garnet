#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

set left [sort_collection [get_ports {clk* reset* glb_cfg_* sram_cfg_* cgra_cfg_gc2glb *pulse*}] hierarchical_name]
set bottom [get_ports -filter {hierarchical_name !~ clk* && hierarchical_name !~ reset && hierarchical_name !~ glb_cfg_* && hierarchical_name !~ sram_cfg_* && hierarchical_name !~ cgra_cfg_gc2glb* && hierarchical_name !~ *pulse*}]

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

editPin -pin [get_property $left hierarchical_name] -start { 0 5 } -end [list 0 [expr {$height - 5}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6
editPin -pin [get_property $bottom hierarchical_name] -start [list 5 0] -end [list [expr {$width - 5}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5

