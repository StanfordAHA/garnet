#==============================================================================
# Tile Array dont_touch constraints file
# Author : Alex Carsello
#==============================================================================

# This constraints file ensures that no buffers get inserted on connections
# between abutted CGRA tiles.

# First get all nets connected to CGRA tiles
set tile_nets [get_nets -of_objects [get_cells -filter {ref_lib_cell_name =~ *Tile*}]]
# Now iterate over collection and check if net connects > 1
# CGRA tile and no other cells. If this is true, don't try to route it.
foreach_in_collection net $tile_nets {
  set connected_cells [get_cells -of_object $net]
  set connected_tiles [filter_collection $connected_cells {ref_lib_cell_name =~ *Tile*}]
  set num_connected_tiles [sizeof_collection $connected_tiles]
  if {($num_connected_tiles > 1) && ([compare_collections $connected_cells $connected_tiles] == 0)} {
    set_dont_touch $net true
  }
}

# This can catch nets connected to external ports of tile_array.
# We must ensure that these nets can be touched
set ext_port_nets [get_nets -of_objects [get_ports]]
set_dont_touch $ext_port_nets false

