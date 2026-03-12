#=========================================================================
# pin-assignments.tcl
#=========================================================================
# Author : Po-Han Chen
# Date   : 

#-------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------
proc print_collection_hierarchical_names {collection} {
    foreach_in_collection c $collection {
        puts [get_property $c hierarchical_name]
    }
}

proc insert_into_middle_of_collection {base_collection new_collection} {
    set output_collection {}
    set middle_index [expr {[sizeof_collection $base_collection] / 2}]
    set index 0
    foreach_in_collection element_base $base_collection {
        if {$index == $middle_index} {
            foreach_in_collection element_new $new_collection {
                append_to_collection output_collection $element_new
            }
        }
        append_to_collection output_collection $element_base
        incr index
    }
    return $output_collection
}

#-------------------------------------------------------------------------
# Pin Collections
#-------------------------------------------------------------------------
# [Top Pins]
#             clock_in_clock ------------------ 1
#             clock_in_reset ------------------ 1
#             axi_in* ------------------------- 235
#             unified_out* -------------------- 352
# [Bottom Pins]
#             io_outputsFromSystolicArray* ---- 514

# Organize ports into collection objects
set ports_uni     [sort_collection [get_ports {*unified_out*}]                hierarchical_name]
set ports_axi     [sort_collection [get_ports {*axi_in*}]                     hierarchical_name]
set ports_clk_rst [sort_collection [get_ports {*in_clock* *in_reset*}]        hierarchical_name]
set ports_output  [sort_collection [get_ports {*outputsFromSystolicArray*}]   hierarchical_name]

# Distribute the ports to different sides
set ports_top    [concat $ports_uni $ports_axi]
set ports_bottom [concat $ports_output]
set ports_left   []
set ports_right  []

# Manipulate the orders -- make sure clk and reset are in the middle
set ports_top [insert_into_middle_of_collection $ports_top $ports_clk_rst]

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------
set pin_layer_top_bottom M3
set pin_layer_left_right M4
set block_width  [dbGet top.fPlan.box_urx]
set block_height [dbGet top.fPlan.box_ury]
set pin_margin_top    25.0
set pin_margin_bottom 25.0

setPinAssignMode -pinEditInBatch true

editPin \
    -layer           $pin_layer_top_bottom \
    -side            TOP \
    -spreadType      START \
    -unit            TRACK \
    -spacing         23 \
    -start           [list $pin_margin_top $block_height] \
    -pin             [get_property $ports_top hierarchical_name]

editPin \
    -layer           $pin_layer_top_bottom \
    -side            BOTTOM \
    -spreadType      START \
    -unit            TRACK \
    -spacing         26 \
    -start           [list $pin_margin_bottom 0.0] \
    -spreadDirection counterClockwise \
    -pin             [get_property $ports_bottom hierarchical_name]

setPinAssignMode -pinEditInBatch false
