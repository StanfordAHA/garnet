# Common helper functions and variables to be used in multiple back-end scripts

proc snap_to_grid {input granularity edge_offset} {
   set new_value [expr (ceil(($input - $edge_offset)/$granularity) * $granularity) + $edge_offset]
   return $new_value
}

set cell_row_height 0.576
set M3_pitch 0.07
set M4_pitch 0.08
set M5_pitch 0.08
set M6_pitch 0.08

# set x grid granularity to LCM of M3 and M5 pitches 
# (layers where we placed vertical pins)
set tile_x_grid 0.56 
# set y grid granularity to LCM of M4 and M6 pitches 
# (layers where we placed horizontal pins) and std_cell row height
set tile_y_grid 2.88
