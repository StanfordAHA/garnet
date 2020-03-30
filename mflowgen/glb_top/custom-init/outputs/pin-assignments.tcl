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
set cgra_data_width 16
set cgra_cfg_addr_width 32
set cgra_cfg_data_width 32


set all [sort_collection [get_ports] hierarchical_name]

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        for {set k 0} {$k < $cgra_data_width} {incr k} {
            lappend tile_ports($i,$j) [get_object_name [get_ports "stream_data_f2g[[expr {$i*$num_cgra_tiles*$cgra_data_width+$j*$cgra_data_width+$k}]]"]]
            lappend tile_ports($i,$j) [get_object_name [get_ports "stream_data_g2f[[expr {$i*$num_cgra_tiles*$cgra_data_width+$j*$cgra_data_width+$k}]]"]]
        }
    }
}

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        lappend tile_ports($i,$j) [get_object_name [get_ports "stream_data_valid_f2g[[expr {$i*$num_cgra_tiles+$j}]]"]]
        lappend tile_ports($i,$j) [get_object_name [get_ports "stream_data_valid_g2f[[expr {$i*$num_cgra_tiles+$j}]]"]]
    }
}

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        for {set k 0} {$k < $cgra_cfg_addr_width} {incr k} {
            lappend tile_ports($i,$j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_addr[[expr {$i*$num_cgra_tiles*$cgra_cfg_addr_width+$j*$cgra_cfg_addr_width+$k}]]"]]
        }
    }
}

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        for {set k 0} {$k < $cgra_cfg_data_width} {incr k} {
            lappend tile_ports($i,$j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_data[[expr {$i*$num_cgra_tiles*$cgra_cfg_data_width+$j*$cgra_cfg_data_width+$k}]]"]]
        }
    }
}

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        lappend tile_ports($i,$j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_wr_en[[expr {$i*$num_cgra_tiles+$j}]]"]]
        lappend tile_ports($i,$j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_rd_en[[expr {$i*$num_cgra_tiles+$j}]]"]]
    }
}

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set k 0} {$k < 3} {incr k} {
        lappend tile_ports($i,$j) [get_object_name [get_ports "interrupt_pulse[[expr {$i*3+$k}]]"]]
    }
}

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    lappend tile_ports($i,$j) [get_object_name [get_ports "strm_start_pulse[$i]"]]
    lappend tile_ports($i,$j) [get_object_name [get_ports "pc_start_pulse[$i]"]]
}

# sorting
for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        set tile_ports($i,$j) [lsort $tile_ports($i,$j)]
    }
}

for {set i 0} {$i < $num_glb_tiles} {incr i} {
    for {set j 0} {$j < $num_cgra_tiles} {incr j} {
        foreach port $tile_ports($i,$j) {
            lappend cache $port
        }
    }
}

# left is a list that holds object name that is not in tile_ports
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
        editPin -pin $tile_ports($i,$j) -start [list [expr {($tile_width/2)*(2*$i+$j)+3}] 0] -end [list [expr {($tile_width/2)*(2*$i+$j+1)-3}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5
    }
}
