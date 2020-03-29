#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

set num_glb_tiles 16
set num_cgra_tiles 2

set all [sort_collection [get_ports] hierarchical_name]

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        set tile_ports($i,$j) [sort_collection [get_ports -regexp "(stream_data_(|valid_)(f2g|g2f)(.)($i)(..)($j)(.)*)|(cgra_cfg_g2f(.)($i)(..)($j)(.)*)"] hierarchical_name]
    }
}

unset cache
for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        foreach port [get_object_name $tile_ports($i,$j)] {
            lappend cache $port
        }
    }
}

# left is a list that holds object name that is not in tile_ports
unset left
foreach a [get_object_name $all] {
    if {$a ni $cache} {
        lappend left $a
    }
}

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]
set tile_width [dbGet [dbGet -p top.insts.name *glb_tile* -i 0].cell.size_x]

editPin -pin $left -start { 0 5 } -end [list 0 [expr {$height - 5}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        editPin -pin [get_property $tile_ports($i,$j) hierarchical_name] -start [list [expr {($tile_width/2)*(2*$i+$j)+3}] 0] -end [list [expr {($tile_width/2)*(2*$i+$j+1)-3}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5
    }
}
