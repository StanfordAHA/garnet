#include "parser.h"
#include "map.h"
#include "regmap.h"
#include <stdio.h>
#include <assert.h>

#define MAX_NUM_COLS 32
#define MAX_NUM_GLB_TILES 16
#define GROUP_SIZE 4
#define MAX_NUM_GROUPS MAX_NUM_COLS / GROUP_SIZE

#ifndef GLB_TILE_MEM_SIZE
#define GLB_TILE_MEM_SIZE 256
#endif

#define BANK_SIZE GLB_TILE_MEM_SIZE / 2 * 1024

// Hacky way to cache tile control configuration
int tile_config_table[MAX_NUM_GLB_TILES];

struct Monitor {
    int num_groups;
    int num_glb_tiles;
    int groups[MAX_NUM_GROUPS];
};

static struct Monitor monitor;

int initialize_monitor(int num_cols) {
    assert(num_cols % GROUP_SIZE == 0);
    if (num_cols > MAX_NUM_COLS) return 0;

    monitor.num_groups = num_cols / GROUP_SIZE;
    // currently, glb_tiles:group = 2:1
    monitor.num_glb_tiles = monitor.num_groups * 2;

    return 1;
}

int glb_map(void *kernel_) {
    struct KernelInfo *kernel = kernel_;
    int num_groups = kernel->place_info->num_groups;

    int group_start = -1;
    for (int i=0; i < monitor.num_groups; i++) {
        int success = 0;
        for (int j=0; j < num_groups; j++) {
            if ((i+j) >= monitor.num_groups) {
                success = -1;
                break;
            }
            if (monitor.groups[i+j] != 0) {
                break;
            }
            if (j == (num_groups-1)) {
                group_start = i;
                success = 1;
            }
        }
        if (success != 0) break;
    }
    // no available group
    if (group_start == -1) return 0;

    for(int i=group_start; i < group_start+num_groups; i++) {
        monitor.groups[i] = 1;
    }
    kernel->place_info->group_start = group_start;

    // bitstream map
    // always put bitstream first
    int tile;
    tile = group_start*2;
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
        tile = (group_start*GROUP_SIZE + io_info->pos.x) / 2;
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
        tile = (group_start*GROUP_SIZE + io_info->pos.x) / 2;
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
    // convert 8bit size to 16bit size
    int size = ((io_info->size) >> 1);
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
    int start = place_info->group_start*2;
    int end = start + place_info->num_groups*2;
    for(int i=start; i<end; i++) {
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
