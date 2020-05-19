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

set num_glb_tiles 16
set num_cgra_tiles 32
set cgra_data_width 16
set cgra_cfg_addr_width 32
set cgra_cfg_data_width 32

set all [sort_collection [get_ports] hierarchical_name]

# per cgra tile ports
for {set j 0} {$j < $num_cgra_tiles} {incr j} {
    for {set k 0} {$k < $cgra_data_width} {incr k} {
        lappend tile_ports($j) [get_object_name [get_ports "stream_data_f2g[[expr {$j*$cgra_data_width+$k}]]"]]
        lappend tile_ports($j) [get_object_name [get_ports "stream_data_g2f[[expr {$j*$cgra_data_width+$k}]]"]]
    }
    lappend tile_ports($j) [get_object_name [get_ports "stream_data_valid_f2g[$j]"]]
    lappend tile_ports($j) [get_object_name [get_ports "stream_data_valid_g2f[$j]"]]
    for {set k 0} {$k < $cgra_cfg_addr_width} {incr k} {
        lappend tile_ports($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_addr[[expr {$j*$cgra_cfg_addr_width+$k}]]"]]
    }
    for {set k 0} {$k < $cgra_cfg_data_width} {incr k} {
        lappend tile_ports($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_data[[expr {$j*$cgra_cfg_data_width+$k}]]"]]
    }
    lappend tile_ports($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_wr_en[$j]"]]
    lappend tile_ports($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_rd_en[$j]"]]
}

for {set j 0} {$j < $num_cgra_tiles} {incr j} {
    foreach port $tile_ports($j) {
        lappend cache $port
    }
}

# per glb tile ports
for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set k 0} {$k < 3} {incr k} {
        lappend glb_tile_ports($i) [get_object_name [get_ports "interrupt_pulse[[expr {$i*3+$k}]]"]]
    }
    lappend glb_tile_ports($i) [get_object_name [get_ports "strm_start_pulse[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "pc_start_pulse[$i]"]]
}

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    foreach port $glb_tile_ports($i) {
        lappend cache $port
    }
}

# left is a list that holds object name that is not in tile_ports
foreach a [get_object_name $all] {
    if {($a ni $cache) && ($a ne "clk")} {
        lappend left $a
    }
}

# sorting
for {set j 0} {$j < $num_cgra_tiles} {incr j} {
    set tile_ports($j) [lsort -command port_compare $tile_ports($j)]
}

set left [lsort -command port_compare $left]

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]
set tile_width [dbGet [dbGet -p top.insts.name *glb_tile* -i 0].cell.size_x]

editPin -pin $left -start { 0 10 } -end [list 0 [expr {$height - 5}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6
editPin -pin "clk" -assign {0 5} -layer M6

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    editPin -pin $glb_tile_ports($i) -start [list [expr {$tile_width*$i+5}] 0] -end [list [expr {$tile_width*$i+8}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5
}

for {set j 0} {$j < $num_cgra_tiles} {incr j} {
    editPin -pin $tile_ports($j) -start [list [expr {($tile_width/2)*$j+10}] 0] -end [list [expr {($tile_width/2)*($j+1)-10}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5
}

