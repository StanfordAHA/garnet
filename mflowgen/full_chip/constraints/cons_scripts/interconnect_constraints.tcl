#=========================================================================
# Design Constraints File
#=========================================================================

# Relax constraints on reset and stall signals, since these aren't pipelined and can run slower
set_multicycle_path -setup 6 -through [get_pins -hierarchical *Interconnect_inst0/reset]
set_multicycle_path -hold  5 -through [get_pins -hierarchical *Interconnect_inst0/reset]
set_multicycle_path -setup 6 -through [get_pins -hierarchical *Interconnect_inst0/stall]
set_multicycle_path -hold  5 -through [get_pins -hierarchical *Interconnect_inst0/stall]

# Ensure that no buffers get inserted on abutted nets
# First get all nets connected to CGRA tiles
set cgra_tiles [get_cells -hier -filter {ref_name =~ Tile_PE || ref_name =~ Tile_MemCore}]
set tile_nets [get_nets -of_objects $cgra_tiles]
# Now iterate over collection and check if net connects > 1
# CGRA tile and no other cells. If this is true, don't try to route it.
foreach_in_collection net $tile_nets {
  set connected_cells [get_cells -of_object $net]
  set connected_tiles [filter_collection $connected_cells {ref_name =~ *Tile*}]
  set num_connected_tiles [sizeof_collection $connected_tiles]
  if {($num_connected_tiles > 1) && ([compare_collections $connected_cells $connected_tiles] == 0)} {
    set_dont_touch $net true
  }
  # Don't touch the tile ID nets
  set net_name [get_property $net name]
  foreach tile_id_net_name {_tile_id _hi _lo} {
    if {[string first $tile_id_net_name $net_name] != -1} {
      set_dont_touch $net true
    }
  }
}
# This can catch nets connected to external ports of tile_array.
# We must ensure that these nets can be touched
set ext_port_nets [get_nets -of_objects [get_pins -hierarchical *Interconnect_inst0/*]]
set_dont_touch $ext_port_nets false

# This can catch nets connected to IO tiles, which should be touched
set io_tile_nets [get_nets -of_objects [get_cells -hier -filter {ref_name =~ Tile_IO*}]]
set_dont_touch $io_tile_nets false

set mu_io_tile_nets [get_nets -of_objects [get_cells -hier -filter {ref_name =~ Tile_MU2F*}]]
set_dont_touch $mu_io_tile_nets false

# Ensure that no buffers get inserted on abutted nets
# First get all nets connected to IO tiles
set io_tiles [get_cells -hier -filter {ref_name =~ Tile_IOCoreReadyValid}]
set tile_nets [get_nets -of_objects $io_tiles]
foreach_in_collection net $tile_nets {
  set connected_cells [get_cells -of_object $net]
  set connected_tiles [filter_collection $connected_cells {ref_name =~ *Tile_IOCoreReadyValid*}]
  set num_connected_tiles [sizeof_collection $connected_tiles]
  if {($num_connected_tiles > 1) && ([compare_collections $connected_cells $connected_tiles] == 0)} {
    set_dont_touch $net true
  }
  # Don't touch the tile ID nets
  set net_name [get_property $net name]
  foreach tile_id_net_name {_tile_id _hi _lo} {
    if {[string first $tile_id_net_name $net_name] != -1} {
      set_dont_touch $net true
    }
  }
}

# Relax read_config_data timing path
set_multicycle_path 16 -to [get_pins -hierarchical *Interconnect_inst0/read_config_data] -setup
set_multicycle_path 15 -to [get_pins -hierarchical *Interconnect_inst0/read_config_data] -hold
