#ifndef VIRTUALIZE_META_LIBRARY_H
#define VIRTUALIZE_META_LIBRARY_H

#include "common/tiny-json.h"

#define MAX_NUM_IO 4
#define MAX_NUM_IO_TILES 8
#define BUFFER_SIZE 1024
#define MAX_NUM_KERNEL 16
#define MAX_JSON_FIELDS 512
#define MAX_CONFIG 20
#define MAX_ADDR_GEN_LOOP 5

#define GET_KERNEL_INFO(info) struct KernelInfo *kernel_info = \
                                    (struct KernelInfo *) info

#define GET_PLACE_INFO(info) struct ScheduleInfo *place_info = \
                                    (struct ScheduleInfo *) info

#define GET_CONFIG_INFO(info) struct ConfigInfo *config_info = \
                                    (struct ConfigInfo *) info

#define GET_BS_INFO(info) struct BitstreamInfo *bs_info = \
                                    (struct BitstreamInfo *) info

#define GET_IO_TILE_INFO(info) struct IOTileInfo *io_info = \
                                    (struct IOTileInfo *) info

   
struct Configuration {
    int addr;
    int data;
};

struct ConfigInfo {
    int num_config;
    struct Configuration config[MAX_CONFIG];
};
struct BitstreamInfo {
    int tile;
    int size;
    int start_addr;

    // TODO: Store glb control information separately
    struct ConfigInfo config;
};
 
struct Position {
    int x;
    int y;
};

enum IO {Input = 0, Output = 1}; 

struct IOTileInfo {

    int tile;
    // TODO: we do not need size anymore as we have extent
    int size; 
    int start_addr;

    struct Position pos; 
    int loop_dim;
    int stride[MAX_ADDR_GEN_LOOP];
    int extent[MAX_ADDR_GEN_LOOP];

    struct ConfigInfo config;
};

struct IOInfo {
    enum IO io;
    int num_io_tiles;
    char filename[BUFFER_SIZE];

    struct IOTileInfo io_tiles[MAX_NUM_IO_TILES];
    struct ConfigInfo config;
};

struct KernelInfo {
    int num_inputs;
    int num_outputs;

    int group_start;
    int num_groups;
    // index to the inputs, need to multiply by 2
    int reset_port;

    char coreir_filename[BUFFER_SIZE];
    char bitstream_filename[BUFFER_SIZE];
    char placement_filename[BUFFER_SIZE];

    // TODO: input_info + output_info should be less than MAX_NUM_IO
    // TODO: Is static global variable better or local variable better?
    struct IOInfo *input_info[MAX_NUM_IO];
    struct IOInfo *output_info[MAX_NUM_IO];
    struct BitstreamInfo *bitstream_info;
};
 

void *parse_metadata(char *filename);
void *parse_schedule(json_t const* IOs_json);
int parse_num_group(struct KernelInfo *info);
// void *get_place_info(void *info);
// void *get_bs_info(void *info);
// void *get_input_info(void *info, int index);
// void *get_output_info(void *info, int index);
// 
// // helper functions to access data from SV
// int get_num_groups(void *info);
// int get_group_start(void *info);
// int get_num_inputs(void *info);
// int get_num_outputs(void *info);
// int get_input_x(void *info, int index);
// int get_input_y(void *info, int index);
// int get_output_x(void *info, int index);
// int get_output_y(void *info, int index);
// int get_reset_index(void *info);
// 
// char *get_placement_filename(void *info);
// char *get_bitstream_filename(void *info);
// char *get_input_filename(void *info, int index);
// char *get_output_filename(void *info, int index);
// int get_input_size(void *info, int index);
// int get_output_size(void *info, int index);
// 
// int get_input_start_addr(void *info, int index);
// int get_input_size(void *info, int index);
// int get_input_tile(void *info, int index);
// int get_output_start_addr(void *info, int index);
// int get_output_size(void *info, int index);
// int get_output_tile(void *info, int index);
// 
// int get_bs_start_addr(void *info);
// int get_bs_size(void *info);
// int get_bs_tile(void *info);
static char *get_prefix(const char *s, char t);

#endif//VIRTUALIZE_META_LIBRARY_H
