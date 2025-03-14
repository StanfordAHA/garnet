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
#             clk
#             rstn
#             startSignal* (r/v)
#             doneSignal* (r/v)
#             serialMatrixParamsIn* (dat: 32b, with r/v)
#             # Temporal Top Pins
#             # New IWB pins will replace the following input/weight/bias pins
#             IWB_Address_Request* (dat: 22b, with r/v)
#             IWB_Data_Response* (dat: 256b, with r/v)
#                 inputAddressRequest* ------------ 96
#                 inputDataResponse* -------------- 512
#                 inputScaleAddressRequest* ------- 96
#                 inputScaleDataResponse* --------- 8
#                 weightAddressRequest* ----------- 96
#                 weightDataResponse* ------------- 256
#                 weightScaleAddressRequest* ------ 96
#                 weightScaleDataResponse* -------- 256
#                 biasAddressRequest* ------------- 96
#                 biasDataResponse* --------------- 256
# [Bottom Pins]
#             outputsFromSystolicArray* (dat: 512b, with r/v)

# Organize ports into collection objects
set ports_param   [sort_collection [get_ports {*Param*}]     hierarchical_name]
set ports_input   [sort_collection [get_ports {*input*}]     hierarchical_name]
set ports_weight  [sort_collection [get_ports {*weight*}]    hierarchical_name]
set ports_bias    [sort_collection [get_ports {*bias*}]      hierarchical_name]
set ports_clk_rst [sort_collection [get_ports {*clk* *rst*}] hierarchical_name]
set ports_control [sort_collection [get_ports {*Signal*}]    hierarchical_name]
set ports_output  [sort_collection [get_ports {*outputs*}]   hierarchical_name]

# Distribute the ports to different sides
set ports_top    [concat $ports_param $ports_input $ports_weight $ports_bias $ports_control]
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
    -spacing         7 \
    -start           [list $pin_margin_top $block_height] \
    -pin             [get_property $ports_top hierarchical_name]

editPin \
    -layer           $pin_layer_top_bottom \
    -side            BOTTOM \
    -spreadType      START \
    -unit            TRACK \
    -spacing         25 \
    -start           [list $pin_margin_bottom 0.0] \
    -spreadDirection counterClockwise \
    -pin             [get_property $ports_bottom hierarchical_name]

setPinAssignMode -pinEditInBatch false
