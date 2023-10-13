# Put all GLB tiles in a single skew group
#create_ccopt_skew_group \
#    -name glb_tiles \
#    -exclusive_sinks [get_object_name [get_pins -hier glb_tile_gen*/clk]] \
#    -target_skew 0.1ns \
#    -target_insertion_delay 0.4ns
#
#set_ccopt_property -skew_group glb_tiles constrains ccopt

foreach_in_collection clk_pin [get_pins -hier glb_tile_gen*/clk] {
    set_ccopt_property -pin [get_object_name $clk_pin] insertion_delay 400ps
}
