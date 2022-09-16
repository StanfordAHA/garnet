# Put all GLB tiles in a single skew group
#create_ccopt_skew_group -name glb_tiles -exclusive_sinks [get_object_name [get_pins -hier glb_tile_gen*/clk]]


#set_ccopt_property auto_limit_insertion_delay_factor 1.2
