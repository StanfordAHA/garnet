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

    // group = GROUP_SIZE columns
    // num_groups = total number of groups in CGRA
    monitor.num_groups = num_cols / GROUP_SIZE;

    // currently, glb_tiles:group = 2:1
    monitor.num_glb_tiles = monitor.num_groups * 2;

    return 1;
}

int glb_map(void *kernel_) {
    struct KernelInfo *kernel = kernel_;
    int num_groups = kernel->num_groups;

    // This is just greedy algorithm to schedule applications
    // TODO: Need a better way to schedule kernels
    int group_start = -1;
    for (int i=0; i < monitor.num_groups; i++) {
        int success = 0;
        for (int j=0; j < num_groups; j++) {
            // if the number of groups required exceeds the hardware resources, then fail
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
    kernel->group_start = group_start;

    // bitstream map
    // always put bitstream first
    int tile;
    tile = group_start*2; // one group has two glb tiles
    struct BitstreamInfo *bs_info = get_bs_info(kernel);

    bs_info->tile = tile;
    bs_info->start_addr = (tile * 2) * BANK_SIZE;
    update_bs_configuration(bs_info);

    int num_bs = bs_info->size;
    int num_inputs = kernel->num_inputs;
    int num_outputs = kernel->num_outputs;

    struct IOInfo *io_info;
    struct IOTileInfo *io_tile_info;
    for(int i=0; i<num_inputs; i++) {
        io_info = get_input_info(kernel, i);
        int num_io_tiles = io_info->num_io_tiles;
        for(int j=0; j<num_io_tiles; j++) {
            io_tile_info = get_io_tile_info(io_info, j);
            tile = (group_start*GROUP_SIZE + io_tile_info->pos.x) / 2;
            io_tile_info->tile = tile;
            // if (i == 0 && j==0) {
            //     io_tile_info->start_addr = (tile * 2) * BANK_SIZE + num_bs*8;
            // } else {
            //     io_tile_info->start_addr = (tile * 2) * BANK_SIZE;
            // }
            io_tile_info->start_addr = (tile * 2) * BANK_SIZE;
            update_io_tile_configuration(io_tile_info, &kernel->config);
        }
    }

    for(int i=0; i<num_outputs; i++) {
        io_info = get_output_info(kernel, i);
        int num_io_tiles = io_info->num_io_tiles;
        for(int j=0; j<num_io_tiles; j++) {
            io_tile_info = get_io_tile_info(io_info, j);
            tile = (group_start*GROUP_SIZE + io_tile_info->pos.x) / 2;
            io_tile_info->tile = tile;
            io_tile_info->start_addr = (tile * 2 + 1) * BANK_SIZE;
            update_io_tile_configuration(io_tile_info, &kernel->config);
        }
    }

    // hacky way to update tile configuration for a kernel
    update_tile_ctrl_configuration(kernel);

    return 1;
}

void update_bs_configuration(struct BitstreamInfo *bs_info) {
    struct ConfigInfo *config_info = &bs_info->config;
    int tile = bs_info->tile;
    int start_addr = bs_info->start_addr;
    int size = bs_info->size;
    // TODO: input/output/pcfg share the same configuration address
    // Need to make it separate
    // For now, just update config and add at the last step
    update_tile_config_table(tile, 1 << 10);
    add_config(config_info, (tile * 0x100) + GLB_TILE0_PC_DMA_HEADER_START_ADDR, start_addr); 
    add_config(config_info, (tile * 0x100) + GLB_TILE0_PC_DMA_HEADER_NUM_CFG, size); 
}

void update_io_tile_configuration(struct IOTileInfo *io_tile_info, struct ConfigInfo *config_info) {
    int tile = io_tile_info->tile;
    int start_addr = io_tile_info->start_addr;

    int loop_dim = io_tile_info->loop_dim;
    int *extent = io_tile_info->extent;
    int *stride = io_tile_info->data_stride;
    int *cycle_stride = io_tile_info->cycle_stride;

    if (io_tile_info->io == Input) {
        update_tile_config_table(tile, 1 << 6);
        update_tile_config_table(tile, 1 << 2);
        add_config(config_info, (tile * 0x100) + GLB_TILE0_LD_DMA_HEADER_0_START_ADDR, start_addr); 
        // TODO: Some hacky way to support >2D cycle_stride
        if (cycle_stride[0] > 1 && loop_dim > 1) {
            add_config(config_info, (tile * 0x100) + (GLB_TILE0_LD_DMA_HEADER_0_ITER_CTRL_0), (cycle_stride[0] << 10) + 0); 
            for (int i = 0; i < loop_dim; i++) {
                add_config(config_info, (tile * 0x100) + (GLB_TILE0_LD_DMA_HEADER_0_ITER_CTRL_0 + 0x04 * (i + 1)), (extent[i] << 10) + stride[i]); 
            }
            add_config(config_info, (tile * 0x100) + GLB_TILE0_LD_DMA_HEADER_0_ACTIVE_CTRL, ((cycle_stride[1] - cycle_stride[0] * extent[0]) << 16) + cycle_stride[0] * extent[0]); 
        } else {
            for (int i = 0; i < loop_dim; i++) {
                // TODO: 0x16 should be variable
                add_config(config_info, (tile * 0x100) + (GLB_TILE0_LD_DMA_HEADER_0_ITER_CTRL_0 + 0x04 * i), (extent[i] << 10) + stride[i]); 
            }
            // TODO: only support when loop_dim is 2D
            if (loop_dim == 2) {
                add_config(config_info, (tile * 0x100) + GLB_TILE0_LD_DMA_HEADER_0_ACTIVE_CTRL, ((cycle_stride[1] - stride[1]) << 16) + stride[1]); 
            }
        }

        add_config(config_info, (tile * 0x100) + GLB_TILE0_LD_DMA_HEADER_0_VALIDATE, 1); 
    } else {
        int size = 1;
        for (int i=0; i < loop_dim; i++) {
            size = size * extent[i];
        }
        update_tile_config_table(tile, 1 << 8);
        update_tile_config_table(tile, 1 << 5);
        add_config(config_info, (tile * 0x100) + GLB_TILE0_ST_DMA_HEADER_0_START_ADDR, start_addr); 
        add_config(config_info, (tile * 0x100) + GLB_TILE0_ST_DMA_HEADER_0_NUM_WORDS, size); 
        add_config(config_info, (tile * 0x100) + GLB_TILE0_ST_DMA_HEADER_0_VALIDATE, 1); 
    }
}

// TODO: This is hacky way to update tile control configuration reigster
// Since all DMAs share the same tile configuration address, we cache the data to 
// tile_config_table and update at the last step
void update_tile_config_table(int tile, int data) {
    tile_config_table[tile] |= data;
}

void update_tile_ctrl_configuration(struct KernelInfo *kernel_info) {
    int start = kernel_info->group_start*2;
    int end = start + kernel_info->num_groups*2;
    for(int i=start; i<end; i++) {
        if (tile_config_table[i] != 0) {
            add_config(&kernel_info->config, (i * 0x100) + GLB_TILE0_TILE_CTRL, tile_config_table[i]);
        }
    }
}

void add_config(struct ConfigInfo *config_info, int addr, int data) {
    int idx = config_info->num_config;
    config_info->config[idx].addr = addr;
    config_info->config[idx].data = data;
    config_info->num_config++;
}
