#=========================================================================
# place-memory-buffers.tcl
#=========================================================================
# Author : Po-Han Chen
# Date   : 

#-------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------
proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

proc legalize_sram_x_location {x_loc} {
    global ADK_M3_TO_M8_STRIPE_OFSET_LIST
    set hori_pitch [dbGet top.fPlan.coreSite.size_x]
    set vert_pitch [dbGet top.fPlan.coreSite.size_y]
    set tech_pitch_x [expr 5 * $hori_pitch]
    set tech_pitch_y [expr 1 * $vert_pitch]
    set sram_x_granularity [lindex $ADK_M3_TO_M8_STRIPE_OFSET_LIST 2]
    set sram_x_granularity [snap_to_grid $sram_x_granularity $hori_pitch]
    set sram_x_granularity [expr 2 * $sram_x_granularity]
    return [snap_to_grid $x_loc $sram_x_granularity]
}

proc get_memory_cells_by_name {pattern} {
    set matched_macros [ \
        get_cells \
            -hierarchical \
            -filter {is_memory_cell==true} \
            $pattern \
    ]
    return [sort_collection $matched_macros hierarchical_name]
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
    set macro_place_lly   [snap_to_grid $lly $tech_pitch_y]
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
set macro_accumulation_buffers [get_memory_cells_by_name *accumulation_buffer*]
set macro_input_buffers        [get_memory_cells_by_name *inputBuffer*]
set macro_weight_buffers       [get_memory_cells_by_name *weightBuffer*]
set macro_input_scale_buffers  [get_memory_cells_by_name *inputScaleBuffer*]
set macro_weight_scale_buffers [get_memory_cells_by_name *weightScaleBuffer*]

# Debugging
# print_collection_hierarchical_names $macro_accumulation_buffers
# print_collection_hierarchical_names $macro_input_buffers
# print_collection_hierarchical_names $macro_weight_buffers
# print_collection_hierarchical_names $macro_input_scale_buffers
# print_collection_hierarchical_names $macro_weight_scale_buffers

#-------------------------------------------------------------------------
# Placing Memory Macros
#-------------------------------------------------------------------------
# ========================================================== Input Buffers
# set llx           25.0
# set lly         2630.0
# set gap_x          0.0
# set gap_y         50.0
# set max_per_row    8
set llx           25.0
set lly         2720.0
set gap_x          0.0
set gap_y          0.0
set max_per_row    8
place_macro_grid_row_major \
    $macro_input_buffers \
    $llx \
    $lly \
    $gap_x \
    $gap_y \
    $max_per_row

# ========================================================= Weight Buffers
# set llx          920.0
# set lly         2630.0
# set gap_x          0.0
# set gap_y         50.0
# set max_per_row    4
set llx          750.0
set lly         2720.0
set gap_x          0.0
set gap_y          0.0
set max_per_row    4
place_macro_grid_row_major \
    $macro_weight_buffers \
    $llx \
    $lly \
    $gap_x \
    $gap_y \
    $max_per_row

# =================================================== Weight Scale Buffers
# set llx          735.0
# set lly         2630.0
# set gap_x          0.0
# set gap_y         50.0
# set max_per_row    4
set llx         1116.72
set lly         2720.0
set gap_x          0.0
set gap_y          0.0
set max_per_row    4
place_macro_grid_row_major \
    $macro_weight_scale_buffers \
    $llx \
    $lly \
    $gap_x \
    $gap_y \
    $max_per_row

# ==================================================== Input Scale Buffers
# set llx          150.0
# set lly         2350.0
# set gap_x          0.0
# set gap_y          0.0
# set max_per_row    2
set llx           25.0
set lly         2475.0
set gap_x          0.0
set gap_y          0.0
set max_per_row    1
place_macro_grid_row_major \
    $macro_input_scale_buffers \
    $llx \
    $lly \
    $gap_x \
    $gap_y \
    $max_per_row

# =================================================== Accumulation Buffers
set llx         50.3
set lly         30.0
set gap_x        0.0
set gap_y        0.0
set max_per_row  8
place_macro_grid_row_major \
    $macro_accumulation_buffers \
    $llx \
    $lly \
    $gap_x \
    $gap_y \
    $max_per_row
