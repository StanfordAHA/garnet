# Common helper functions and variables to be used in multiple back-end scripts

proc snap_to_grid {input granularity edge_offset} {
   set new_value [expr (ceil(($input - $edge_offset)/$granularity) * $granularity) + $edge_offset]
   return $new_value
}

proc glbuf_sram_place {srams sram_start_x sram_start_y sram_spacing_x_even sram_spacing_x_odd sram_spacing_y bank_height sram_height sram_width} {
  set y_loc $sram_start_y
  set x_loc $sram_start_x
  set col 0
  set row 0
  foreach_in_collection sram $srams {
    set sram_name [get_property $sram full_name]
    set y_loc [snap_to_grid $y_loc 0.09 0]
    if {[expr $col % 2] == 0} {
      place_inst $sram_name $x_loc $y_loc -fixed MY
    } else {
      place_inst $sram_name $x_loc $y_loc -fixed
    }
    set row [expr $row + 1]
    set y_loc [expr $y_loc + $sram_height + $sram_spacing_y]
    # Next column over
    if {$row >= $bank_height} {
      set row 0
      set sram_spacing_x 0
      if {[expr $col % 2] == 0} {
        set sram_spacing_x $sram_spacing_x_even
      } else {
        set sram_spacing_x $sram_spacing_x_odd
      }
      set x_loc [expr $x_loc + $sram_width + $sram_spacing_x]
      set y_loc $sram_start_y
      set col [expr $col + 1]
    }
  }
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
