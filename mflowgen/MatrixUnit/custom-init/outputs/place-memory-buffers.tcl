#=========================================================================
# place-memory-buffers.tcl
#=========================================================================
# Author : Po-Han Chen
# Date   : 

#-------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------
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
    # ----- Macro Parameters
    set first_macro [index_collection $macros 0]
    set first_macro_name [get_property $first_macro hierarchical_name]
    set macro_width  [dbGet [dbGet -p top.insts.name $first_macro_name].cell.size_x]
    set macro_height [dbGet [dbGet -p top.insts.name $first_macro_name].cell.size_y]
    set row 0
    set col 0
    set macro_place_llx $llx
    set macro_place_lly $lly
    set macro_orientation R0
    # ----- Place Macros
    foreach_in_collection macro $macros {
        set macro_name [get_property $macro hierarchical_name]
        placeInstance \
            $macro_name \
            $macro_place_llx \
            $macro_place_lly \
            $macro_orientation \
            -fixed
        # update index
        incr col
        if {$col >= $max_per_row} {
            incr row
            set col 0
            set macro_place_llx $llx
            set macro_place_lly [expr $macro_place_lly - $macro_height - $gap_y]
        } else {
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
set llx_accumulation_buffers 10.0
set lly_accumulation_buffers 1600.0
set gap_x_accumulation_buffers 0.0
set gap_y_accumulation_buffers 0.0
set max_per_row_accumulation_buffers 8

place_macro_grid_row_major \
    $macro_accumulation_buffers \
    $llx_accumulation_buffers \
    $lly_accumulation_buffers \
    $gap_x_accumulation_buffers \
    $gap_y_accumulation_buffers \
    $max_per_row_accumulation_buffers

# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[1].g_width[7].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[0].g_width[7].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[1].g_width[6].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[0].g_width[6].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[1].g_width[5].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[0].g_width[5].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[1].g_width[4].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[0].g_width[4].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[1].g_width[3].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[0].g_width[3].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[1].g_width[2].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[0].g_width[2].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[1].g_width[1].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[0].g_width[1].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[1].g_width[0].g_macro1024.mem
# matrixProcessor_MatrixProcessor_I8_I32_F16_E8M0_true_64_32_2048_process_accumulation_inst_constexpr_if_if_while_accumulation_buffer_value_float_val_d_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[7].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[7].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[6].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[6].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[5].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[5].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[4].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[4].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[3].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[3].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[2].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[2].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[1].g_macro1024.mem
# inputBuffer_DoubleBuffer_I8_64_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[1].g_macro1024.mem
# weightBuffer_DoubleBuffer_I8_32_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[3].g_macro1024.mem
# weightBuffer_DoubleBuffer_I8_32_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[3].g_macro1024.mem
# weightBuffer_DoubleBuffer_I8_32_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[2].g_macro1024.mem
# weightBuffer_DoubleBuffer_I8_32_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[2].g_macro1024.mem
# weightBuffer_DoubleBuffer_I8_32_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[1].g_macro1024.mem
# weightBuffer_DoubleBuffer_I8_32_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[1].g_macro1024.mem
# weightBuffer_DoubleBuffer_I8_32_1024_mem1Run_inst_mem1_value_int_val_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem
# weightBuffer_DoubleBuffer_I8_32_1024_mem0Run_inst_mem0_value_int_val_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem
# -----below are new-----
# inputScaleBuffer_DoubleBuffer_E8M0_1_1024_mem1Run_inst_mem1_value_d_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem
# inputScaleBuffer_DoubleBuffer_E8M0_1_1024_mem0Run_inst_mem0_value_d_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem
# weightScaleBuffer_DoubleBuffer_E8M0_32_1024_mem1Run_inst_mem1_value_d_rsc_comp_g_depth[0].g_width[3].g_macro1024.mem
# weightScaleBuffer_DoubleBuffer_E8M0_32_1024_mem1Run_inst_mem1_value_d_rsc_comp_g_depth[0].g_width[2].g_macro1024.mem
# weightScaleBuffer_DoubleBuffer_E8M0_32_1024_mem1Run_inst_mem1_value_d_rsc_comp_g_depth[0].g_width[1].g_macro1024.mem
# weightScaleBuffer_DoubleBuffer_E8M0_32_1024_mem1Run_inst_mem1_value_d_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem
# weightScaleBuffer_DoubleBuffer_E8M0_32_1024_mem0Run_inst_mem0_value_d_rsc_comp_g_depth[0].g_width[3].g_macro1024.mem
# weightScaleBuffer_DoubleBuffer_E8M0_32_1024_mem0Run_inst_mem0_value_d_rsc_comp_g_depth[0].g_width[2].g_macro1024.mem
# weightScaleBuffer_DoubleBuffer_E8M0_32_1024_mem0Run_inst_mem0_value_d_rsc_comp_g_depth[0].g_width[1].g_macro1024.mem
# weightScaleBuffer_DoubleBuffer_E8M0_32_1024_mem0Run_inst_mem0_value_d_rsc_comp_g_depth[0].g_width[0].g_macro1024.mem