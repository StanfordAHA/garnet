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

set array_width $env(array_width)
set num_glb_tiles $env(num_glb_tiles)
set prr_size 4
set cgra_data_width 16
set cgra_cfg_addr_width 32
set cgra_cfg_data_width 32

set all []
set cache []
set all [sort_collection [get_ports] hierarchical_name]

# per cgra tile ports
for {set j 0} {$j < $array_width} {incr j} {
    for {set k 0} {$k < $cgra_data_width} {incr k} {
        lappend tile_ports($j) [get_object_name [get_ports "strm_data_f2g[[expr {$j*$cgra_data_width+$k}]]"]]
        lappend tile_ports($j) [get_object_name [get_ports "strm_data_g2f[[expr {$j*$cgra_data_width+$k}]]"]]
    }
    lappend tile_ports($j) [get_object_name [get_ports "strm_data_valid_f2g[$j]"]]
    lappend tile_ports($j) [get_object_name [get_ports "strm_data_valid_g2f[$j]"]]
    for {set k 0} {$k < $cgra_cfg_addr_width} {incr k} {
        lappend tile_ports($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_addr[[expr {$j*$cgra_cfg_addr_width+$k}]]"]]
    }
    for {set k 0} {$k < $cgra_cfg_data_width} {incr k} {
        lappend tile_ports($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_data[[expr {$j*$cgra_cfg_data_width+$k}]]"]]
    }
    lappend tile_ports($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_wr_en[$j]"]]
    lappend tile_ports($j) [get_object_name [get_ports "cgra_cfg_g2f_cfg_rd_en[$j]"]]
    if {[expr {($j % $prr_size) == 0}]} {
        lappend tile_ports($j) [get_object_name [get_ports "strm_data_flush_g2f[[expr {$j / $prr_size}]]"]]
    }
}

for {set j 0} {$j < $array_width} {incr j} {
    foreach port $tile_ports($j) {
        lappend cache $port
    }
}

# per glb tile ports
for {set i 0} {$i < $num_glb_tiles} {incr i} {
    lappend glb_tile_ports($i) [get_object_name [get_ports "glb_clk_en_master[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "glb_clk_en_bank_master[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "pcfg_broadcast_stall[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "strm_g2f_interrupt_pulse[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "strm_f2g_interrupt_pulse[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "pcfg_g2f_interrupt_pulse[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "strm_g2f_start_pulse[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "strm_f2g_start_pulse[$i]"]]
    lappend glb_tile_ports($i) [get_object_name [get_ports "pcfg_start_pulse[$i]"]]
}

# first_tile is a list that holds object name that is not in tile_ports
set first_tile []
for {set i 0} {$i < $num_glb_tiles} {incr i} {
    foreach port $glb_tile_ports($i) {
        lappend cache $port
    }
}

foreach a [get_object_name $all] {
    if {($a ni $cache) && ($a ne "clk") && ($a ne "reset")} {
        lappend first_tile $a
    }
}

# sorting
for {set j 0} {$j < $array_width} {incr j} {
    set tile_ports($j) [lsort -command port_compare $tile_ports($j)]
}

set first_tile [lsort -command port_compare $first_tile]
set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]
set first_tile_pin_range [expr {[llength $first_tile] * 0.5 + 5}]
set center [expr {($width - $first_tile_pin_range) / 2 + $first_tile_pin_range}]
set tile_width [dbGet [dbGet -p top.insts.name *glb_tile* -i 0].cell.size_x]
set left_offset 20

set glb_tile_port_offset [expr {($width - $first_tile_pin_range) / $num_glb_tiles }]
 
# pins for glb <-> soc
editPin -pin $first_tile -start 5 $height -end $first_tile_pin_range $height -side TOP -spreadType RANGE -spreadDirection clockwise -layer M5

# clk pin
editPin -pin "clk" -side TOP -assign [expr $center-10]  $height -layer M5
editPin -pin "reset" -side TOP -assign [expr $center+10] $height -layer M5

# for glb <-> glc
for {set i 0} {$i < $num_glb_tiles} {incr i} {
    editPin -pin $glb_tile_ports($i) -start [list [expr {$first_tile_pin_range + $glb_tile_port_offset * $i + 20}] $height] -end [list [expr {$first_tile_pin_range + $glb_tile_port_offset * ($i + 1) - 20}] $height] -side TOP -spreadType RANGE -spreadDirection clockwise -layer M5
}
  
# bottom pins
for {set j 0} {$j < $array_width} {incr j} {
    editPin -pin $tile_ports($j) -start [list [expr {($tile_width/2)*$j+5+$left_offset}] 0] -end [list [expr {($tile_width/2)*($j+1)-5+$left_offset}] 0] -side BOTTOM -spreadType RANGE -spreadDirection counterclockwise -layer M5
}

