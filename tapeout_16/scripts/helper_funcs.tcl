# Common helper functions and variables to be used in multiple back-end scripts

##### HELPER FUNCTIONS #####
proc snap_to_grid {input granularity edge_offset} {
   set new_value [expr (ceil(($input - $edge_offset)/$granularity) * $granularity) + $edge_offset]
   return $new_value
}

proc gcd {a b} {
  ## Everything divides 0  
  if {$a < $b} {
      return [gcd $b $a]
  }
 
  ## Base case     
  if {$b < 0.001} {  
      return $a 
  } else {
      return [gcd $b [expr $a - floor($a/$b) * $b]]
  }
}

proc lcm {a b} {
  return [expr ($a * $b) / [gcd $a $b]]
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
    create_route_blockage -inst $sram_name -cover -pg_nets -layers M1 -spacing 2
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

proc get_cell_area_from_rpt {name} {
  # Parse post-synthesis area report to get cell area
  # Line starts with cell name
  set area_string [exec grep "^${name}" ../${name}/results_syn/final_area.rpt]
  # Split line on spaces
  set area_list [regexp -inline -all -- {\S+} $area_string]
  # Cell area is third word in string
  set cell_area [lindex $area_list 2]
}

proc calculate_tile_info {pe_util mem_util min_height min_width tile_x_grid tile_y_grid tile_stripes} { 
  set tile_info(Tile_PECore,area) [expr [get_cell_area_from_rpt Tile_PECore] / $pe_util]
  set tile_info(Tile_MemCore,area) [expr [get_cell_area_from_rpt Tile_MemCore] / $mem_util]
  # First make the smaller of the two tiles square
  if {$tile_info(Tile_PECore,area) < $tile_info(Tile_MemCore,area)} {
    set smaller Tile_PECore
    set larger Tile_MemCore
  } else {
    set smaller Tile_MemCore
    set larger Tile_PECore
  }
  set side_length [expr sqrt($tile_info($smaller,area))]
  set height $side_length
  set width $side_length
  # Make sure this conforms to min_height
  set height [expr max($height,$min_height)]
  set height [snap_to_grid $height $tile_y_grid 0]
  # Once we've set the height, recalculate width
  set width [expr $tile_info($smaller,area)/$height]
  # Make sure width conforms to min_width
  set width [expr max($width,$min_width)]
  set width [snap_to_grid $width $tile_x_grid 0]
  # Make the width an even number of grid units to make 
  # resizing easier
  set num_grid_units [expr round($width / $tile_x_grid)]
  if {[expr fmod($num_grid_units, 2) > 0.0]} {
    incr num_grid_units
    set width [expr $num_grid_units * $tile_x_grid]
  }
  # Now we've calculated dimensions of smaller tile
  set tile_info($smaller,height) $height
  set tile_info($smaller,width) $width
  # Larger tile has same height
  set tile_info($larger,height) $height
  # Now calculate width of larger tile
  set width [expr $tile_info($larger,area)/$height]
  set width [expr max($width,$min_width)]
  set tile_info($larger,width) [snap_to_grid $width $tile_x_grid 0]
  set tile_info_array [array get tile_info]
  set tile_stripes [calculate_stripe_info $tile_info_array $tile_stripes $tile_x_grid $tile_y_grid]
  #Finally, snap width of larger tile to M9 s2s so that all stripes fit evenly
  set larger_width [dict get $tile_info_array $larger,width]
  set max_s2s [dict get $tile_stripes M9,s2s]
  dict set tile_info_array $larger,width [snap_to_grid $larger_width $max_s2s 0]
  set merged_tile_info [dict merge $tile_info_array $tile_stripes]
  return $merged_tile_info
}

#Given the tile dimensions give a set of stripe intervals that will fit into the tile
proc gen_acceptable_stripe_intervals {length grid} {
  set max_div [expr floor($length)]
  set intervals ""
  set interval 99999
  set div 1
  while { $interval > 1 } {
    set interval [expr $length / $div]
    if {[expr $grid == 0]} {
      lappend intervals $interval 
    } else { 
        set remainder [expr fmod($interval, $grid)]
        if {[expr $remainder == 0.0] || [expr $remainder == $grid]} {
          lappend intervals $interval 
        }
    }
    incr div
  }
  return $intervals
}

proc find_closest_in_list {target values} {
  set min_diff 99999
  set closest ""
  foreach {val} $values {
    set diff [expr abs($val - $target)]
    if {$diff < $min_diff} {
      set min_diff $diff
      set closest $val
    }
  }
  return $closest
}

proc calculate_stripe_info {tile_info tile_stripes tile_x_grid tile_y_grid} {
  set pe_width [dict get $tile_info Tile_PECore,width]
  set mem_width [dict get $tile_info Tile_MemCore,width]
  set height [dict get $tile_info Tile_PECore,height]
  set min_width [expr min($pe_width, $mem_width)]
  # First do horizontal layer (M8)
  set intervals [gen_acceptable_stripe_intervals $height 0]
  dict set tile_stripes M8,s2s [find_closest_in_list [dict get $tile_stripes M8,s2s] $intervals]

  # Then do vertial layer(s) (M7, M9)
  set intervals [gen_acceptable_stripe_intervals $min_width $tile_x_grid]
  dict set tile_stripes M9,s2s [find_closest_in_list [dict get $tile_stripes M9,s2s] $intervals]
  set intervals [gen_acceptable_stripe_intervals [dict get $tile_stripes M9,s2s] 0]
  dict set tile_stripes M7,s2s [find_closest_in_list [dict get $tile_stripes M7,s2s] $intervals]

  return $tile_stripes
}

##### END HELPER FUNCTIONS #####
