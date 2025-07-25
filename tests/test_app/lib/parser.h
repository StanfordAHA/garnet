#ifndef VIRTUALIZE_META_LIBRARY_H
#define VIRTUALIZE_META_LIBRARY_H

#include "global_buffer_param.h"
#include "tiny-json.h"

#define MAX_NUM_IO 16
#define MAX_NUM_IO_TILES 16
#define BUFFER_SIZE 1024
#define MAX_NUM_KERNEL 128
#define MAX_JSON_FIELDS 2048
#define MAX_CONFIG 8192

#define GET_BS_INFO(info) struct BitstreamInfo *bs_info = (struct BitstreamInfo *)info
#define GET_KERNEL_INFO(info) struct KernelInfo *kernel_info = (struct KernelInfo *)info
#define GET_CONFIG_INFO(info) struct ConfigInfo *config_info = (struct ConfigInfo *)info

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

    struct ConfigInfo config;
};

struct Position {
    int x;
    int y;
};

enum IO { Input = 0, Output = 1, MU_Input = 2 };
enum APP_TYPE {glb2cgra = 0, mu2cgra = 1, mu2cgra_glb2cgra = 2};

struct IOTileInfo {
    enum IO io;
    int tile;
    int start_addr;
    int gold_check_start_addr; // for gold check, may be different from start_addr
    int cycle_start_addr;

    struct Position pos;
    int num_blocks;
    char mode[BUFFER_SIZE];
    int loop_dim;
    int seg_mode;
    int cycle_stride[LOOP_LEVEL];
    int data_stride[LOOP_LEVEL];
    int extent[LOOP_LEVEL];
    int E64_packed;
    int extent_multiplier;

    // For back-to-back kernels
    int is_glb_input;

    // Indicates if the addr gen config has been modified to account for matrix unit's tiling
    bool hacked_for_mu_tiling;

    // For bank toggle mode
    int bank_toggle_mode;
    // We need fake IOs to read from toggled bank for gold check
    int is_fake_io;

};

struct IOInfo {
    enum IO io;
    int num_io_tiles;
    char filename[BUFFER_SIZE];
    int filesize;
    struct IOTileInfo io_tiles[MAX_NUM_IO_TILES];
};

struct KernelInfo {
    int num_inputs;
    int num_outputs;
    int num_mu_inputs;

    enum APP_TYPE app_type;

    int group_start;
    int num_groups;
    // index to the inputs, need to multiply by 2
    int reset_port;
    int opal_dense_scanner_workaround;

    // control glb tiling
    int num_glb_tiling;
    int glb_tiling_cnt;

    char bin_dir[BUFFER_SIZE];
    char coreir_filename[BUFFER_SIZE];
    char bitstream_filename[BUFFER_SIZE];
    char placement_filename[BUFFER_SIZE];

    struct IOInfo *input_info[MAX_NUM_IO];
    struct IOInfo *mu_input_info[MAX_NUM_IO];
    struct IOInfo *output_info[MAX_NUM_IO];
    struct BitstreamInfo *bitstream_info;

    // NOTE: What is the best place to store config information?
    // Most config should go into each IOInfo by having separate
    // configuration info for each DMA?
    struct ConfigInfo config;
};

void *parse_metadata(char *filename);
void *parse_schedule(json_t const *IOs_json);
int parse_num_group(struct KernelInfo *info);
void *get_bs_info(void *info);
void *get_input_info(void *info, int index);
void *get_mu_input_info(void *info, int index);
void *get_output_info(void *info, int index);
void *get_io_tile_info(void *info, int index);
int get_io_tile_loop_dim(void *info, int index);
int get_io_tile_extent(void *info, int index, int extent_idx);
int get_io_tile_cycle_stride(void *info, int index, int stride_idx);
int get_io_tile_data_stride(void *info, int index, int stride_idx);
int get_io_tile_is_glb_input(void *info, int index); // for back-to-back kernels judge if the input is already in global buffer
int get_io_tile_E64_packed(void *info, int index);
int get_io_tile_bank_toggle_mode(void *info, int index);

// helper functions to access data from SV testbench
int get_num_groups(void *info);
int get_group_start(void *info);
int get_app_type(void *info);
int get_num_inputs(void *info);
int get_num_mu_inputs(void *info);
int get_num_outputs(void *info);
int get_num_io_tiles(void *info, int index);
int get_io_tile_x(void *info, int index);
int get_io_tile_y(void *info, int index);
int get_reset_index(void *info);
int get_num_glb_tiling(void *info); // for GLB tiling
int get_glb_tiling_cnt(void *info); // for GLB tiling
void update_glb_tiling_cnt(void *info, int cnt); // for GLB tiling

char *get_placement_filename(void *info);
char *get_bitstream_filename(void *info);
char *get_input_filename(void *info, int index);
char *get_mu_input_filename(void *info, int index);
char *get_output_filename(void *info, int index);
int get_input_size(void *info, int index);
int get_mu_input_size(void *info, int index);
int get_output_size(void *info, int index);

int get_io_tile_start_addr(void *info, int index);
int get_io_tile_map_tile(void *info, int index);
int get_bs_start_addr(void *info);
int get_bs_size(void *info);
int get_bs_tile(void *info);
char *get_prefix(const char *s, char t);

#endif  // VIRTUALIZE_META_LIBRARY_H
