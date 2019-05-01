# Common helper functions and variables to be used in multiple back-end scripts

proc snap_to_grid {input granularity edge_offset} {
   set new_value [expr (ceil(($input - $edge_offset)/$granularity) * $granularity) + $edge_offset]
   return $new_value
}

# set x grid granularity to LCM of M3 and M5 pitches 
# (layers where we placed vertical pins)
set tile_x_grid 0.56 
# set y grid granularity to LCM of M4 and M6 pitches 
# (layers where we placed horizontal pins) and std_cell row height
set tile_y_grid 2.88

#stripe width
set tile_stripes(M7,width) 1
set tile_stripes(M8,width) 3
set tile_stripes(M9,width) 4
#stripe spacing
set tile_stripes(M7,spacing) 0.5
set tile_stripes(M8,spacing) 2
set tile_stripes(M9,spacing) 2
#stripe set to set distance
if $::env(PWR_AWARE) {
  set tile_stripes(M7,s2s) 10
  set tile_stripes(M8,s2s) 15
  set tile_stripes(M9,s2s) 20
} else {
set tile_stripes(M7,s2s) 10
set tile_stripes(M8,s2s) 12
set tile_stripes(M9,s2s) 16
}
#stripe start
set tile_stripes(M7,start) 2
set tile_stripes(M8,start) 4
set tile_stripes(M9,start) 4
