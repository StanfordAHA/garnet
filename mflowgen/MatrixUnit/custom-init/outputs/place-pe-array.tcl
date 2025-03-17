#=========================================================================
# place-pe-array.tcl
#=========================================================================
# Author : Po-Han Chen
# Date   : 

#-------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------
proc sort_collection_by_postfix {collection} {
    # Get the hierarchical names of the collection elements
    set collection_names [get_property $collection hierarchical_name]

    # Define a custom comparison function to extract and compare the numerical postfix
    proc compare_postfix {a b} {
        # Extract the numerical postfix from the hierarchical names
        if {[regexp {(\d+)$} $a -> a_postfix] && [regexp {(\d+)$} $b -> b_postfix]} {
            # Compare the numerical postfixes
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

proc get_pe_cells_by_name {pattern} {
    set matched_macros [ \
        get_cells \
            -hierarchical \
            -filter {is_black_box==true} \
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
    set macro_place_llx   $llx
    set macro_place_lly   $lly
    set macro_orientation R0
    set halo_left         $tech_pitch_x
    set halo_bottom       $tech_pitch_y
    set halo_right        $tech_pitch_x
    set halo_top          $tech_pitch_y
    # ----- Place Macros
    set row 0
    set col 0
    foreach_in_collection macro $macros {
        set macro_name [get_property $macro hierarchical_name]
        # place the instance
        placeInstance \
            $macro_name \
            $macro_place_llx \
            $macro_place_lly \
            $macro_orientation \
            -fixed
        # put halo
        addHaloToBlock \
            $halo_left \
            $halo_bottom \
            $halo_right \
            $halo_top \
            -snapToSite \
            $macro_name
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
# Memory Macro Information
#-------------------------------------------------------------------------
# Organize memory macros into collection objects
set macro_pes [get_pe_cells_by_name *systolicArray_pe*]

# Debugging
# print_collection_hierarchical_names $macro_pes

#-------------------------------------------------------------------------
# Placing PE Array
#-------------------------------------------------------------------------
set llx 80.0
set lly 2600.0
set gap_x 3.0
set gap_y 4.5
set max_per_row 32
place_macro_grid_row_major \
    $macro_pes \
    $llx \
    $lly \
    $gap_x \
    $gap_y \
    $max_per_row
