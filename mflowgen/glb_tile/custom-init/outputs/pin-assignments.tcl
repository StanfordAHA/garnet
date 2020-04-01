#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

proc port_compare {a b} {
    set a_sliced [split $a "\["]
    set a0 [lindex $a_sliced 0]
    set a_sliced [split [lindex $a_sliced 1] "\]"]
    set a1 [lindex $a_sliced 0]

    set b_sliced [split $b "\["]
    set b0 [lindex $b_sliced 0]
    set b_sliced [split [lindex $b_sliced 1] "\]"]
    set b1 [lindex $b_sliced 0]

    if {$a0 < $b0} {
        return -1
    } elseif {$a0 > $b0} {
        return 1
    } else {
        if {$a1 < $b1} {
            return -1
        } elseif {$a1 > $b1} {
            return 1
        } else {
            return 0
        }
    }
}

# Spread the ports for abutment.

set left [lsort -command port_compare [get_property [get_ports *_wst*] hierarchical_name]]
set right [lsort -command port_compare [get_property [get_ports *_est*] hierarchical_name]]
set bottom [lsort -command port_compare [get_property [get_ports -filter {hierarchical_name !~ *_wst* && hierarchical_name !~ *_est*}] hierarchial_name]]

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

editPin -pin $left -start { 0 5 } -end [list 0 [expr {$height - 5}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6
editPin -pin $right -start [list $width  5] -end [list $width [expr {$height - 5}]] -side RIGHT -spreadType RANGE -spreadDirection counterclockwise -layer M6
editPin -pin $bottom -start [list 5 0] -end [list [expr {$width - 5}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5

