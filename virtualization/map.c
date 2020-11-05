#include "parser.h"
#include "map.h"
#include "regmap.h"
#include <stdio.h>

#define BANK_SIZE 131072
#define NUM_COLS 32
#define NUM_GLB_TILES NUM_COLS/2
#define GROUP_SIZE 4

// Hacky way to cache tile control configuration
int tile_config_table[NUM_GLB_TILES];

struct GarnetMonitor {
    int cols[NUM_COLS];
};

static struct GarnetMonitor garnet;

int glb_map(void *kernel_) {
    struct KernelInfo *kernel = kernel_;
    int num_groups = kernel->place_info->num_groups;

    int col_start = -1;
    for (int i=0; i < NUM_COLS; i++) {
        if (garnet.cols[i] == 0) {
            col_start = i;
            break;
        }
    }
    // no available columns
    if (col_start == -1) return 0;
    if (col_start % GROUP_SIZE != 0) {
        col_start = (col_start + GROUP_SIZE - 1) / GROUP_SIZE * GROUP_SIZE;
    }
    // not enought columns
    if ((col_start + num_groups * GROUP_SIZE) > NUM_COLS) return 0;

    for(int i=col_start; i < col_start+num_groups*GROUP_SIZE; i++) {
        garnet.cols[i] = 1;
    }

    // bitstream map
    // always put bitstream first
    int tile;
    tile = col_start / 2;
    struct BitstreamInfo *bs_info = get_bs_info(kernel);

    bs_info->tile = tile;
    bs_info->start_addr = (tile * 2) * BANK_SIZE;

    update_bs_configuration(bs_info);

    int num_bs = bs_info->size;
    int num_inputs = kernel->place_info->num_inputs;
    int num_outputs = kernel->place_info->num_outputs;

    struct IOInfo *io_info;
    for(int i=0; i<num_inputs; i++) {
        io_info = get_input_info(kernel->place_info, i);
        io_info->size = kernel->place_info->input_size[i];
        tile = (col_start + io_info->pos.x) / 2;
        io_info->tile = tile;
        if (i == 0) {
            io_info->start_addr = (tile * 2) * BANK_SIZE + num_bs*8;
        } else {
            io_info->start_addr = (tile * 2) * BANK_SIZE;
        }
        update_io_configuration(io_info);
    }

    for(int i=0; i<num_outputs; i++) {
        io_info = get_output_info(kernel->place_info, i);
        io_info->size = kernel->place_info->output_size[i];
        tile = (col_start + io_info->pos.x) / 2;
        io_info->tile = tile;
        io_info->start_addr = (tile * 2 + 1) * BANK_SIZE;
        update_io_configuration(io_info);
    }

    // hacky way to update tile configuration for a kernel
    update_tile_configuration(kernel->place_info);

    return 1;
}

void update_bs_configuration(struct BitstreamInfo *bs_info) {
    struct ConfigInfo *config_info = &bs_info->config;
    int tile = bs_info->tile;
    int start_addr = bs_info->start_addr;
    int size = bs_info->size;
    // TODO: input/output/pcfg shares the same controller
    // Need to make it separate
    // For now, just update config and add at the very last step
    update_tile_config_table(tile, 1 << 10);
    add_config(config_info, (tile * 0x100) + GLB_TILE0_PC_DMA_HEADER_START_ADDR, start_addr); 
    add_config(config_info, (tile * 0x100) + GLB_TILE0_PC_DMA_HEADER_NUM_CFG, size); 
}

void update_io_configuration(struct IOInfo *io_info) {
    //struct ConfigInfo *config_info = &io_info->config;
    struct ConfigInfo *config_info = &io_info->config;
    int tile = io_info->tile;
    int start_addr = io_info->start_addr;
    int size = io_info->size;
    if (io_info->io == Input) {
        update_tile_config_table(tile, 1 << 6);
        update_tile_config_table(tile, 1 << 2);
        add_config(config_info, (tile * 0x100) + GLB_TILE0_LD_DMA_HEADER_0_START_ADDR, start_addr); 
        add_config(config_info, (tile * 0x100) + GLB_TILE0_LD_DMA_HEADER_0_ITER_CTRL_0, (size << 10) + 1); 
        add_config(config_info, (tile * 0x100) + GLB_TILE0_LD_DMA_HEADER_0_VALIDATE, 1); 
    } else {
        update_tile_config_table(tile, 1 << 8);
        update_tile_config_table(tile, 1 << 5);
        add_config(config_info, (tile * 0x100) + GLB_TILE0_ST_DMA_HEADER_0_START_ADDR, start_addr); 
        add_config(config_info, (tile * 0x100) + GLB_TILE0_ST_DMA_HEADER_0_NUM_WORDS, size); 
        add_config(config_info, (tile * 0x100) + GLB_TILE0_ST_DMA_HEADER_0_VALIDATE, 1); 
    }
}

void update_tile_config_table(int tile, int data) {
    tile_config_table[tile] |= data;
}

void update_tile_configuration(struct PlaceInfo *place_info) {
    for(int i=0; i<NUM_GLB_TILES; i++) {
        if (tile_config_table[i] != 0) {
            add_config(&place_info->config, (i * 0x100) + GLB_TILE0_TILE_CTRL, tile_config_table[i]);
        }
    }
}

void add_config(struct ConfigInfo *config_info, int addr, int data) {
    int idx = config_info->num_config;
    config_info->config[idx].addr = addr;
    config_info->config[idx].data = data;
    config_info->num_config++;
}
