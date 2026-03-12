
# set x_start 08
set x_start 0C
set x_end   1B
set y_start 01
set y_end   10

set all_tiles [get_cells -hier -filter {ref_name =~ Tile_PE || ref_name =~ Tile_MemCore}]

set tile_corner_north_west [get_cells -hier Tile_X${x_start}_Y${y_start}]
set tile_corner_north_east [get_cells -hier Tile_X${x_end}_Y${y_start}]
set tile_corner_south_west [get_cells -hier Tile_X${x_start}_Y${y_end}]
set tile_corner_south_east [get_cells -hier Tile_X${x_end}_Y${y_end}]

set tiles_row_first [get_cells -hier Tile_X*_Y${y_start} -filter {ref_name =~ Tile_PE || ref_name =~ Tile_MemCore}]
set tiles_row_first [remove_from_collection $tiles_row_first $tile_corner_north_west]
set tiles_row_first [remove_from_collection $tiles_row_first $tile_corner_north_east]

set tiles_row_last  [get_cells -hier Tile_X*_Y${y_end}   -filter {ref_name =~ Tile_PE || ref_name =~ Tile_MemCore}]
set tiles_row_last  [remove_from_collection $tiles_row_last  $tile_corner_south_west]
set tiles_row_last  [remove_from_collection $tiles_row_last  $tile_corner_south_east]

set tiles_col_first [get_cells -hier Tile_X${x_start}_Y* -filter {ref_name =~ Tile_PE || ref_name =~ Tile_MemCore}]
set tiles_col_first [remove_from_collection $tiles_col_first $tile_corner_north_west]
set tiles_col_first [remove_from_collection $tiles_col_first $tile_corner_south_west]

set tiles_col_last  [get_cells -hier Tile_X${x_end}_Y*   -filter {ref_name =~ Tile_PE || ref_name =~ Tile_MemCore}]
set tiles_col_last  [remove_from_collection $tiles_col_last  $tile_corner_north_east]
set tiles_col_last  [remove_from_collection $tiles_col_last  $tile_corner_south_east]

set inner_tiles [remove_from_collection $all_tiles   $tiles_row_first]
set inner_tiles [remove_from_collection $inner_tiles $tiles_row_last]
set inner_tiles [remove_from_collection $inner_tiles $tiles_col_first]
set inner_tiles [remove_from_collection $inner_tiles $tiles_col_last]
set inner_tiles [remove_from_collection $inner_tiles $tile_corner_north_west]
set inner_tiles [remove_from_collection $inner_tiles $tile_corner_north_east]
set inner_tiles [remove_from_collection $inner_tiles $tile_corner_south_west]
set inner_tiles [remove_from_collection $inner_tiles $tile_corner_south_east]

set total_tile_disable_timing 0

# disable timing for all SB ports
foreach_in_collection tile $inner_tiles {
    puts [get_property $tile full_name]
    set tile_pins [get_pins -of_object $tile]
    set tile_sb_pins [filter_collection $tile_pins {name =~ SB*}]
    set_disable_timing $tile_sb_pins
    incr total_tile_disable_timing
}

# Top
foreach_in_collection tile $tiles_row_first {
    puts [get_property $tile full_name]
    set tile_pins [get_pins -of_object $tile]
    set tile_sb_pins [filter_collection $tile_pins {name =~ SB*WEST* || name =~ SB*SOUTH* || name =~ SB*EAST*}]
    set_disable_timing $tile_sb_pins
    incr total_tile_disable_timing
}

# Bottom
foreach_in_collection tile $tiles_row_last {
    puts [get_property $tile full_name]
    set tile_pins [get_pins -of_object $tile]
    set tile_sb_pins [filter_collection $tile_pins {name =~ SB*WEST* || name =~ SB*NORTH* || name =~ SB*EAST*}]
    set_disable_timing $tile_sb_pins
    incr total_tile_disable_timing
}

# LEFT
foreach_in_collection tile $tiles_col_first {
    puts [get_property $tile full_name]
    set tile_pins [get_pins -of_object $tile]
    set tile_sb_pins [filter_collection $tile_pins {name =~ SB*NORTH* || name =~ SB*EAST* || name =~ SB*SOUTH*}]
    set_disable_timing $tile_sb_pins
    incr total_tile_disable_timing
}

# RIGHT
foreach_in_collection tile $tiles_col_last {
    puts [get_property $tile full_name]
    set tile_pins [get_pins -of_object $tile]
    set tile_sb_pins [filter_collection $tile_pins {name =~ SB*NORTH* || name =~ SB*WEST* || name =~ SB*SOUTH*}]
    set_disable_timing $tile_sb_pins
    incr total_tile_disable_timing
}

# Corners
puts [get_property $tile_corner_north_west full_name]
set tile_pins [get_pins -of_object $tile_corner_north_west]
set tile_sb_pins [filter_collection $tile_pins {name =~ SB*EAST* || name =~ SB*SOUTH*}]
set_disable_timing $tile_sb_pins
incr total_tile_disable_timing

puts [get_property $tile_corner_north_east full_name]
set tile_pins [get_pins -of_object $tile_corner_north_east]
set tile_sb_pins [filter_collection $tile_pins {name =~ SB*WEST* || name =~ SB*SOUTH*}]
set_disable_timing $tile_sb_pins
incr total_tile_disable_timing

puts [get_property $tile_corner_south_west full_name]
set tile_pins [get_pins -of_object $tile_corner_south_west]
set tile_sb_pins [filter_collection $tile_pins {name =~ SB*NORTH* || name =~ SB*EAST*}]
set_disable_timing $tile_sb_pins
incr total_tile_disable_timing

puts [get_property $tile_corner_south_east full_name]
set tile_pins [get_pins -of_object $tile_corner_south_east]
set tile_sb_pins [filter_collection $tile_pins {name =~ SB*NORTH* || name =~ SB*WEST*}]
set_disable_timing $tile_sb_pins
incr total_tile_disable_timing

# also disable timing on IO tiles
set io_tiles  [get_cells -hier -filter {ref_name =~ Tile_IOCoreReadyValid}]
foreach_in_collection tile $io_tiles {
    puts [get_property $tile full_name]
    set tile_pins [get_pins -of_object $tile]
    set tile_sb_pins [filter_collection $tile_pins {name =~ SB*EAST* || name =~ SB*WEST*}]
    set_disable_timing $tile_sb_pins
    incr total_tile_disable_timing
}


puts "Total tile disable timing: $total_tile_disable_timing"