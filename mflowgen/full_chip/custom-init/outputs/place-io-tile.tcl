#=========================================================================
# place-tile-array.tcl
#=========================================================================
#
# Author : Po-Han Chen
# Date   : 

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

proc sort_collection_by_postfix {collection} {
    # Get the hierarchical names of the collection elements
    set collection_names [get_property $collection hierarchical_name]

    # Define a custom comparison function to extract and compare the numerical postfix
    proc compare_postfix {a b} {
        # Extract the numerical postfix from the hierarchical names
        if {[regexp {X(\S*)_} $a -> a_postfix] && [regexp {X(\S*)_} $b -> b_postfix]} {
            # Compare the numerical postfixes
            set a_postfix [expr 0x$a_postfix + 0]
            set b_postfix [expr 0x$b_postfix + 0]
            return [expr {$a_postfix < $b_postfix ? -1 : ($a_postfix > $b_postfix ? 1 : 0)}]
        }
        return [string compare $a $b]
    }

    # Sort the collection names using the custom comparison function
    set sorted_names [lsort -command compare_postfix $collection_names]

    # Convert the sorted list of names back to a collection
    set sorted_collection {}
    foreach name $sorted_names {
        append_to_collection sorted_collection [get_cells $name]
    }

    return $sorted_collection
}

proc get_cells_by_name {pattern} {
    set matched_macros [ \
        get_cells \
            -hierarchical \
            -filter {is_macro_cell==true} \
            $pattern \
    ]
    return [sort_collection_by_postfix $matched_macros]
}

proc print_collection_hierarchical_names {collection} {
    foreach_in_collection c $collection {
        puts [get_property $c hierarchical_name]
    }
}

proc sanity_check_all_macro_dimension_is_equal {macros} {
    # All macros should have the same width and height
    set macro_width -1
    set macro_height -1
    foreach_in_collection macro $macros {
        set macro_name        [get_property $macro hierarchical_name]
        set temp_macro_width  [dbGet [dbGet top.insts.name $macro_name -p].cell.size_x]
        set temp_macro_height [dbGet [dbGet top.insts.name $macro_name -p].cell.size_y]
        if {$macro_width == -1} {
            set macro_width $temp_macro_width
            set macro_height $temp_macro_height
        } else {
            if {$macro_width != $temp_macro_width || $macro_height != $temp_macro_height} {
                # puts "\[Error\] *** All macros should have the same width and height"
                # puts "\[Error\] ***     First macro width: $macro_width"
                # puts "\[Error\] ***     First macro height: $macro_height"
                # puts "\[Error\] ***     Current Macro width: $temp_macro_width"
                # puts "\[Error\] ***     Current Macro height: $temp_macro_height"
                return 0
            }
        }
    }
    return 1
}

proc place_macro_grid_row_major {macros llx lly gap_x gap_y max_per_row} {
    # ----- First check if all macros have the same width and height
    set sanity_check_pass [sanity_check_all_macro_dimension_is_equal $macros]
    if {$sanity_check_pass == 0} {
        puts "\[Error\] *** All macros should have the same width and height"
        return
    }
    # ----- Tech Parameters
    set hori_pitch [dbGet top.fPlan.coreSite.size_x]
    set vert_pitch [dbGet top.fPlan.coreSite.size_y]
    set tech_pitch_x [expr 5 * $hori_pitch]
    set tech_pitch_y [expr 1 * $vert_pitch]
    # ----- Macro Parameters
    set first_macro       [index_collection $macros 0]
    set first_macro_name  [get_property $first_macro hierarchical_name]
    set macro_width       [dbGet [dbGet -p top.insts.name $first_macro_name].cell.size_x]
    set macro_height      [dbGet [dbGet -p top.insts.name $first_macro_name].cell.size_y]
    set macro_place_llx   [snap_to_grid $llx $tech_pitch_x]
    set macro_place_lly   [snap_to_grid $lly $tech_pitch_y]
    set macro_orientation R0
    set halo_left         $tech_pitch_x
    set halo_bottom       $tech_pitch_y
    set halo_right        $tech_pitch_x
    set halo_top          $tech_pitch_y
    # ----- Place Macros
    set row 0
    set col 0
    set margin 0.32
    foreach_in_collection macro $macros {
        set macro_name [get_property $macro hierarchical_name]
        # place the instance
        placeInstance \
            $macro_name \
            $macro_place_llx \
            $macro_place_lly \
            $macro_orientation \
            -fixed
        
        set tile_llx [dbGet [dbGet -p top.insts.name $macro_name].box_llx]
        set tile_lly [dbGet [dbGet -p top.insts.name $macro_name].box_lly]
        set tile_urx [dbGet [dbGet -p top.insts.name $macro_name].box_urx]
        set tile_ury [dbGet [dbGet -p top.insts.name $macro_name].box_ury]
        # put halo
        addHaloToBlock \
            $halo_left \
            $halo_bottom \
            $halo_right \
            $halo_top \
            -snapToSite \
            $macro_name
        # put route blockage
        createRouteBlk \
            -name r${row}c${col}_rblk_sig_non_pin_layers \
            -layer { m1 m2       m5 m6 m7 m8 } \
            -inst $macro_name \
            -spacing $margin \
            -exceptpgnet \
            -cover
        createRouteBlk \
            -name r${row}c${col}_rblk_sig_pin_layers \
            -layer {       m3 m4             } \
            -inst $macro_name \
            -exceptpgnet \
            -cover
        
        createRouteBlk \
            -name r${row}c${col}_rblk_bot_m4 \
            -layer {          m4             } \
            -box $tile_llx [expr $tile_lly - $margin] $tile_urx $tile_lly \
            -exceptpgnet
        createRouteBlk \
            -name r${row}c${col}_rblk_top_m4 \
            -layer {          m4             } \
            -box $tile_llx $tile_ury $tile_urx [expr $tile_ury + $margin] \
            -exceptpgnet
        createRouteBlk \
            -name r${row}c${col}_rblk_left_m3 \
            -layer {       m3                } \
            -box [expr $tile_llx - $margin] $tile_lly $tile_llx $tile_ury \
            -exceptpgnet
        createRouteBlk \
            -name r${row}c${col}_rblk_right_m3 \
            -layer {       m3                } \
            -box $tile_urx $tile_lly [expr $tile_urx + $margin] $tile_ury \
            -exceptpgnet

        createRouteBlk \
            -name r${row}c${col}_rblk_pwr \
            -layer { m1 m2 m3 m4 m5 m6 m7 m8 } \
            -inst $macro_name \
            -pgnetonly \
            -spacing [expr 2*$margin] \
            -cover
        # update index and location
        incr col
        if {$col >= $max_per_row} {
            incr row
            set col 0
            set macro_place_llx $llx
            # stacking from top to down (-)
            set macro_place_lly [expr $macro_place_lly - $macro_height - $gap_y]
        } else {
            # stacking from left to right (+)
            set macro_place_llx [expr $macro_place_llx + $macro_width + $gap_x]
        }
    }
}

#-------------------------------------------------------------------------
# IO Macro Information
#-------------------------------------------------------------------------
# Organize io macros into collection objects
set macro_ios [get_cells_by_name *Tile_X*_Y00]

# Debugging
print_collection_hierarchical_names $macro_ios

#-------------------------------------------------------------------------
# Placing IO Tile Row
#-------------------------------------------------------------------------
# set llx             105.0
set llx             211.0
set lly            3032.5
set gap_x             0.0
set gap_y             0.0
set max_per_row        28
place_macro_grid_row_major \
    $macro_ios \
    $llx \
    $lly \
    $gap_x \
    $gap_y \
    $max_per_row

#-------------------------------------------------------------------------
# Tile ID Connections
#-------------------------------------------------------------------------
set connection_layer [dbGet -p head.layers.name M4]
set connection_width [dbGet $connection_layer.wrongwayWidth]
# Iterate over all tiles
foreach_in_collection tile $macro_ios {
      set tile_name [get_property $tile hierarchical_name]
      # For this tile, get all of the tile id pins
      set tile_id_pins [get_pins $tile_name/tile_id*]
      set num_id_pins [sizeof_collection $tile_id_pins]
      # The ID pins are on the left side of the tile,
      # all have same x coordinate as the tile itself
      set id_pin_x [dbGet [dbGet top.insts.name -p $tile_name].box_llx]
      # Iterate over tile id pins for this tile and connect each
      # to the corresponding hi/lo pin
      for {set index 0} {$index < $num_id_pins} {incr index} {
        set id_pin [index_collection $tile_id_pins [expr $num_id_pins - $index - 1]]
        set id_pin_y [get_property $id_pin y_coordinate]
        set id_net [get_net -of_objects $id_pin]
        set id_net_name [get_property $id_net hierarchical_name]
        # Here, we find whcih hi/lo pin is supposed to drive this tile_id input pin
        # We're going to draw a shape to connect these two pins

        # Find the nearest hi/lo pin to which we can connect the id pin
        set tie_pin [get_pins -of_objects $id_net -filter "hierarchical_name!~*id*"] 

        # Build the shape that connects id pin to hi/lo pin
        set tie_pin_y [get_property $tie_pin y_coordinate]
        # For X, start our shape at the lefmost edge of the tile
        set llx [expr $id_pin_x]
        # Come into the tile by connection_width
        set urx [expr $llx + $connection_width]
        # For y, start at whichever of the two pins is lower 
        set lly [expr min($tie_pin_y, $id_pin_y)]
        # End at the higher of the two pins
        set ury [expr max($tie_pin_y, $id_pin_y)]
        add_shape -net $id_net_name -layer $connection_layer -rect $llx $lly $urx $ury
    }
}
