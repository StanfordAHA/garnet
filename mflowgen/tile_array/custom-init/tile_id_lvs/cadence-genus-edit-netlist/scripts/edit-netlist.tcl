#=========================================================================
# edit_netlist.tcl
#=========================================================================
# Author : Alex Carsello
# Date   : April 11, 2024


set_db /modules/Tile_PE .boundary_opto false
set_db /modules/Tile_MemCore .boundary_opto false

# Get min max col
set min_col 99999
set min_row 99999
set max_row -99999
set max_col -99999
foreach_in_collection tile [get_cells -hier -filter "ref_name=~Tile_PE* || ref_name=~Tile_MemCore*"] {
  set tile_name [get_property $tile full_name]
  regexp {X(\S*)_} $tile_name -> col
  regexp {Y(\S*)} $tile_name -> row

  # Convert hex IDs to decimal
  set row [expr 0x$row + 0]
  set col [expr 0x$col + 0]

  # grid height = max row value
  if {$row > $max_row} {
    set max_row $row
  }
  if {$row < $min_row} {
    set min_row $row
  }
  if {$col > $max_col} {
    set max_col $col
  }
  if {$col < $min_col} {
    set min_col $col
  }
}

set min_row_hex [format %02X $min_row]
set max_row_hex [format %02X $max_row]
set min_col_hex [format %02X $min_col]
set max_col_hex [format %02X $max_col]

set second_half_start_row_hex [format %02X [expr $min_row + 8]]

set non_tile_insts [get_cells * -filter {(ref_lib_cell_name!=Tile_MemCore) && (ref_lib_cell_name!=Tile_PE)}]

# Disconnect everything going into top of array
# Get all the top row tiles
set top_tiles [get_cells Tile_*_Y${min_row_hex}]
set second_half_top_tiles [get_cells Tile_*_Y${second_half_start_row_hex}]

append_to_collection top_tiles $second_half_top_tiles

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

# Disconnect west pins
foreach_in_collection pin [get_pins Tile_X${min_col_hex}_Y*/*WEST*] {
  edit_netlist disconnect $pin
}

# Disconnect east pins
foreach_in_collection pin [get_pins Tile_X${max_col_hex}_Y*/*EAST*] {
  edit_netlist disconnect $pin
}

# Disconnect south pins
foreach_in_collection pin [get_pins Tile_X*_Y${max_row_hex}/*SOUTH*] {
  edit_netlist disconnect $pin
}

