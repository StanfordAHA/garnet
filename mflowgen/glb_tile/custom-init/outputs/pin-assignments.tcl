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
set all [sort_collection [get_ports] hierarchical_name]

# Moving if_cfg*rd_data ports to top of left side so they're close to GLC at top level
set all_left_port_objs [get_ports *_wst*]
set left_top_port_objs [get_ports if_cfg*_wst*rd_data*]
set left_bot_port_objs [remove_from_collection $all_left_port_objs $left_top_port_objs]

set left_top [lsort -command port_compare [get_property $left_top_port_objs hierarchical_name]]
set left_bot [lsort -command port_compare [get_property $left_bot_port_objs hierarchical_name]]
set left [concat $left_bot $left_top]


# Now do the same on the right to satisfy abutment requirements
set all_right_port_objs [get_ports *_est*]
set right_top_port_objs [get_ports if_cfg*_est*rd_data*]
set right_bot_port_objs [remove_from_collection $all_right_port_objs $right_top_port_objs]

set right_top [lsort -command port_compare [get_property $right_top_port_objs hierarchical_name]]
set right_bot [lsort -command port_compare [get_property $right_bot_port_objs hierarchical_name]]
set right [concat $right_bot $right_top]

set cols_per_tile 2
set cgra_data_width 16
set cgra_cfg_addr_width 32
set cgra_cfg_data_width 32

for {set j 0} {$j < $cols_per_tile} {incr j} {
    for {set k 0} {$k < $cgra_data_width} {incr k} {
        lappend bottom_col($j) [get_object_name [get_ports "strm_data_f2g[[expr {$j*$cgra_data_width+$k}]]"]]
        lappend bottom_col($j) [get_object_name [get_ports "strm_data_g2f[[expr {$j*$cgra_data_width+$k}]]"]]
    }
    lappend bottom_col($j) [get_object_name [get_ports "strm_data_f2g_vld[$j]"]]
    lappend bottom_col($j) [get_object_name [get_ports "strm_data_f2g_rdy[$j]"]]

    lappend bottom_col($j) [get_object_name [get_ports "strm_data_g2f_vld[$j]"]]
    lappend bottom_col($j) [get_object_name [get_ports "strm_data_g2f_rdy[$j]"]]

    lappend bottom_col($j) [get_object_name [get_ports "strm_ctrl_f2g[$j]"]]
    lappend bottom_col($j) [get_object_name [get_ports "strm_ctrl_g2f[$j]"]]
    for {set k 0} {$k < $cgra_cfg_addr_width} {incr k} {
        lappend bottom_col($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_addr[[expr {$j*$cgra_cfg_addr_width+$k}]]"]]
    }
    for {set k 0} {$k < $cgra_cfg_data_width} {incr k} {
        lappend bottom_col($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_data[[expr {$j*$cgra_cfg_data_width+$k}]]"]]
    }
    lappend bottom_col($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_wr_en[$j]"]]
    lappend bottom_col($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_rd_en[$j]"]]
    if {$j == 0} {
        lappend bottom_col($j) [get_object_name [get_ports "data_flush"]]
    }
}

foreach port $left {
    lappend cache $port
}

foreach port $right {
    lappend cache $port
}

for {set i 0} {$i < $cols_per_tile} {incr i} {
    foreach port $bottom_col($i) {
        lappend cache $port
    }
}

# top is a list that holds object name that is not in bottom_cols, left, or right
foreach a [get_object_name $all] {
    if {($a ni $cache) && ($a ne "clk")} {
        lappend top $a
    }
}

# Sorting
for {set j 0} {$j < $cols_per_tile} {incr j} {
    set bottom_col($j) [lsort -command port_compare $bottom_col($j)]
}
set top [lsort -command port_compare $top]

# assignment
set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

# clk pin in middle of top side on higher layer than other pins
editPin -pin "clk" -side TOP -spreadType CENTER -layer 9

# control pins assignment 
editPin -pin $top -side TOP -spreadType RANGE -start [list 10 $height] -end [list [expr {$width - 10}] $height] -layer M5

editPin -pin $left -start { 0 5 } -end [list 0 [expr {$height - 5}]] -side LEFT -spreadType RANGE -spreadDirection clockwise -layer M6
editPin -pin $right -start [list $width  5] -end [list $width [expr {$height - 5}]] -side RIGHT -spreadType RANGE -spreadDirection counterclockwise -layer M6

for {set j 0} {$j < $cols_per_tile} {incr j} {
    editPin -pin $bottom_col($j) -start [list [expr {($width/2)*$j+10}] 0] -end [list [expr {($width/2)*($j+1)-10}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5
}

