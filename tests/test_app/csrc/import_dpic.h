
 extern void* parse_metadata(/* INPUT */const char* filename);

 extern void* get_place_info(/* INPUT */void* info);

 extern void* get_bs_info(/* INPUT */void* info);

 extern void* get_input_info(/* INPUT */void* info, /* INPUT */int index);

 extern void* get_output_info(/* INPUT */void* info, /* INPUT */int index);

 extern int glb_map(/* INPUT */void* kernel);

 extern int get_num_groups(/* INPUT */void* info);

 extern int get_group_start(/* INPUT */void* info);

 extern int get_num_inputs(/* INPUT */void* info);

 extern int get_num_io_tiles(/* INPUT */void* info, /* INPUT */int index);

 extern int get_num_outputs(/* INPUT */void* info);

 extern SV_STRING get_placement_filename(/* INPUT */void* info);

 extern SV_STRING get_bitstream_filename(/* INPUT */void* info);

 extern SV_STRING get_input_filename(/* INPUT */void* info, /* INPUT */int index);

 extern SV_STRING get_output_filename(/* INPUT */void* info, /* INPUT */int index);

 extern int get_input_size(/* INPUT */void* info, /* INPUT */int index);

 extern int get_output_size(/* INPUT */void* info, /* INPUT */int index);

 extern int get_bs_size(/* INPUT */void* info);

 extern int get_bs_tile(/* INPUT */void* info);

 extern int get_bs_start_addr(/* INPUT */void* info);

 extern int get_io_tile_start_addr(/* INPUT */void* info, /* INPUT */int index);

 extern int get_io_tile_map_tile(/* INPUT */void* info, /* INPUT */int index);

 extern int get_io_tile_loop_dim(/* INPUT */void* info, /* INPUT */int index);

 extern int get_io_tile_extent(/* INPUT */void* info, /* INPUT */int index, /* INPUT */int extent_idx);

 extern int get_io_tile_data_stride(/* INPUT */void* info, /* INPUT */int index, /* INPUT */int stride_idx);

 extern int get_io_tile_cycle_stride(/* INPUT */void* info, /* INPUT */int index, /* INPUT */int stride_idx);

 extern void* get_kernel_configuration(/* INPUT */void* info);

 extern void* get_pcfg_configuration(/* INPUT */void* info);

 extern int get_configuration_size(/* INPUT */void* info);

 extern int get_configuration_addr(/* INPUT */void* info, /* INPUT */int index);

 extern int get_configuration_data(/* INPUT */void* info, /* INPUT */int index);

 extern int get_pcfg_pulse_addr();

 extern int get_pcfg_pulse_data(/* INPUT */void* info);

 extern int get_strm_pulse_addr();

 extern int get_strm_pulse_data(/* INPUT */void* info);

 extern int initialize_monitor(/* INPUT */int num_cols);
