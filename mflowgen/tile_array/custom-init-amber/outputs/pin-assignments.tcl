#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

set num_cgra_tiles $savedvars(grid_num_cols)

set all [get_ports]
set all_tile_ports ""
# per cgra tile ports
for {set col 0} {$col < $num_cgra_tiles} {incr col} {
    # Covert col to hex
    set col_hex [format "%02X" $col]
    # Data stream signals
    set data_ports [get_ports [list \
        glb2io_*_X${col_hex}_Y00* \
        io2glb_*_X${col_hex}_Y00* \
        ]]
    set data_ports [sort_collection $data_ports hierarchical_name]
    # Config and stall signals
    set port_names [list \
        stall\[${col}\] \
        config_${col}_*]
    # Insert a flush for every PR region (every 4 cols)
    if {[expr (($col + 3) % 4)] == 0} {
        set pr_region [expr (($col+3)/4) - 1]
        lappend port_names flush\[${pr_region}\]
    }
    set config_ports [get_ports $port_names]
    set config_ports [sort_collection $config_ports hierarchical_name]
    set ports [concat $data_ports $config_ports]
    set tile_ports($col) [get_object_name $ports]
    set all_tile_ports [concat $all_tile_ports $tile_ports($col)] 
}

# Now put clk and reset in the center
set center_ports [get_object_name [get_ports {clk reset}]]
set all_tile_ports [concat $all_tile_ports $center_ports]
set center_col   [expr $num_cgra_tiles / 2]
if { $center_ports != 0 } {
    set tile_ports($center_col) [concat $tile_ports($center_col) $center_ports]
}

# Collect any ports we missed
foreach a [get_object_name $all] {
    if {$a ni $all_tile_ports} {
        echo "INFO: Assigning port $a to top left corner"
        lappend topleft $a
    }
}

set width [dbGet top.fPlan.box_urx]
set height [dbGet top.fPlan.box_ury]

set topleft_length [expr [llength $topleft] + 5]
set edge_offset 10

editPin \
    -pin $topleft \
    -start [list 0. [expr $height - $edge_offset - $topleft_length]] \
    -end [list 0. [expr $height - $edge_offset]] \
    -side LEFT \
    -spreadType RANGE \
    -spreadDirection clockwise \
    -layer 6

# This speeds up pin assignment
setPinAssignMode -pinEditInBatch true
for {set col 0} {$col < $num_cgra_tiles} {incr col} {
    set start_x [expr $tiles(1,$col,x_loc) + 1] 
    set end_x [expr $start_x + $tiles(1,$col,width) - 2] 
    editPin \
        -pin $tile_ports($col) \
        -start [list $start_x $height ] \
        -end [list $end_x $height ] \
        -side TOP \
        -spreadType RANGE \
        -spreadDirection clockwise \
        -layer 5
}
setPinAssignMode -pinEditInBatch false

