# VERSION CHECK
# SR: I put it here b/c multiple other scripts source this
# FIXME this probably is not the best place for it
set version [string range [get_db / .program_version] 0 1]
puts "Found version ${version}"
if ($version!=19) { 
  puts stderr "**ERROR: (SR-420): Wanted version 19, found $version"
  exit 1
}


# Common helper functions and variables to be used in multiple back-end scripts

##### HELPER FUNCTIONS #####
proc snap_to_grid {input granularity {edge_offset 0}} {
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

proc glbuf_sram_place {srams sram_start_x sram_start_y sram_spacing_x_even sram_spacing_x_odd sram_spacing_y bank_height sram_height sram_width x_block_left x_block_right flip_odd stylus {margin 3} } {
  set y_loc $sram_start_y
  set x_loc $sram_start_x
  set col 0
  set row 0
  foreach_in_collection sram $srams {
    set sram_name [get_property $sram full_name]
    set y_loc [snap_to_grid $y_loc 0.09]
    #set x_loc [snap_to_grid $x_loc 0.09 $core_to_edge]
    if {$stylus} {
      if {[expr $col % 2] == $flip_odd} {
        place_inst $sram_name $x_loc $y_loc -fixed MY
      } else {
        place_inst $sram_name $x_loc $y_loc -fixed
      }
      # Don't block the pins with power vias
      create_route_blockage -inst $sram_name -cover -pg_nets -layers {VIA1 VIA2 VIA3} -spacing $margin
      create_route_blockage -inst $sram_name -cover -pg_nets -layers {M1} -spacing $margin
    } else {
      if {[expr $col % 2] == $flip_odd} {
        placeInstance $sram_name $x_loc $y_loc MY -fixed
      } else {
        placeInstance $sram_name $x_loc $y_loc -fixed
      }
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
      if {($x_loc > $x_block_left) && ($x_loc < $x_block_right)} {
        set x_loc $x_block_right
      }
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
  set tile_info(Tile_PE,area) [expr [get_cell_area_from_rpt Tile_PE] / $pe_util]
  set tile_info(Tile_MemCore,area) [expr [get_cell_area_from_rpt Tile_MemCore] / $mem_util]
  # First make the smaller of the two tiles square
  if {$tile_info(Tile_PE,area) < $tile_info(Tile_MemCore,area)} {
    set smaller Tile_PE
    set larger Tile_MemCore
  } else {
    set smaller Tile_MemCore
    set larger Tile_PE
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
  # Make the width  number of grid units divisible by 4 to make 
  # resizing easier
  set num_grid_units [expr round($width / $tile_x_grid)]
  set remainder [expr fmod($num_grid_units, 4)]
  if {[expr $remainder <= 1.0]} {
    incr num_grid_units [expr int(-$remainder)]
  } else {
    incr num_grid_units [expr 4 - int($remainder)]
  }
  set width [expr $num_grid_units * $tile_x_grid]
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
  
  # Tests!
  set pe_height [dict get $merged_tile_info Tile_PE,height]
  set mem_height [dict get $merged_tile_info Tile_MemCore,height]
  set pe_width [dict get $merged_tile_info Tile_PE,width]
  set mem_width [dict get $merged_tile_info Tile_MemCore,width]
  set m7_s2s [dict get $merged_tile_info M7,s2s]
  set m8_s2s [dict get $merged_tile_info M8,s2s]
  set m9_s2s [dict get $merged_tile_info M9,s2s]
  # Check that heights are equal
  if {$pe_height != $mem_height} {
    puts "ERROR: Tile heights not equal"
  }
  # HARD CODE SO NUMBERS STOP #!@?ing changing
  dict set merged_tile_info Tile_PE,height 86.4
  dict set merged_tile_info Tile_PE,width 60.48
  dict set merged_tile_info Tile_MemCore,height 86.4
  dict set merged_tile_info Tile_MemCore,width 161.28 
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
        set num_grids [expr $interval / $grid] 
        # Check if the interval is an integer number of grid units
        set remainder [expr fmod($num_grids, 1)]
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
  set pe_width [dict get $tile_info Tile_PE,width]
  set mem_width [dict get $tile_info Tile_MemCore,width]
  set height [dict get $tile_info Tile_PE,height]
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
