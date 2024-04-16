#=========================================================================
# edit_netlist.tcl
#=========================================================================
# Author : Alex Carsello
# Date   : April 11, 2024

set non_tile_insts [get_cells * -filter {(ref_lib_cell_name!=Tile_MemCore) && (ref_lib_cell_name!=Tile_PE)}]

# Disconnect everything going into top of array
# Get all the top row tiles
set top_tiles [get_cells Tile_*_Y01]
foreach_in_collection tile $top_tiles {
  set tile_name [get_property $tile hierarchical_name]
  foreach pin_query {*NORTH* *config_config* config_read config_write flush clk clk_pass_through reset read_config_data_in stall} {
    set pins [get_pins ${tile_name}/${pin_query}]
    foreach_in_collection pin $pins {
      edit_netlist disconnect $pin
    }
  }
}

# Delete everything that's not a PE or a memory tile
foreach_in_collection inst $non_tile_insts {
  set name [get_property $inst hierarchical_name]
  edit_netlist delete $name
}

