#include "map.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "glb.h"
#include "glc.h"
#include "global_buffer_param.h"

#define MAX_NUM_COLS 32
#define MAX_NUM_GLB_TILES 16
#define GROUP_SIZE 4
#define MAX_NUM_GROUPS MAX_NUM_COLS / GROUP_SIZE

int crossbar_config[GROUP_SIZE];
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

void update_bs_configuration(struct BitstreamInfo *bs_info) {
    struct ConfigInfo *config_info = &bs_info->config;
    int tile = bs_info->tile;
    int start_addr = bs_info->start_addr;
    int size = bs_info->size;

    add_config(config_info,
               (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_PCFG_DMA_CTRL_R, 1);
    add_config(
        config_info,
        (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_PCFG_DMA_HEADER_START_ADDR_R,
        start_addr);
    add_config(config_info,
               (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_PCFG_DMA_HEADER_NUM_CFG_R,
               size);
}

int glb_map(void *kernel_, int dpr_enabled) {
    struct KernelInfo *kernel = kernel_;
    int num_groups = kernel->num_groups;
    printf("number of groups: %d\n",  kernel->num_groups);
    printf("number of inputs: %d\n",  kernel->num_inputs);
    printf("number of outputs: %d\n",  kernel->num_outputs);

    printf("monitor.num_groups: %d\n", monitor.num_groups);

    if (num_groups > monitor.num_groups) {
        printf("Application does not fit on array. Possible error CGRA too small, applications overlapping\n");
        return 0;
    }

    int group_start;
    // DPR needs to check if enough array space
    if (dpr_enabled == 1) {
        // This is just greedy algorithm to schedule applications
        // TODO: Need a better way to schedule kernels
        group_start = -1;
        for (int i = 0; i < monitor.num_groups; i++) {
            int success = 0;
            for (int j = 0; j < num_groups; j++) {
                // if the number of groups required exceeds the hardware resources, then
                // fail
                if ((i + j) >= monitor.num_groups) {
                    success = -1;
                    break;
                }
                if (monitor.groups[i + j] != 0) {
                    break;
                }
                if (j == (num_groups - 1)) {
                    group_start = i;
                    success = 1;
                }
            }
            if (success != 0) break;
        }
        // no available group
        if (group_start == -1) {
            printf("Combination of Applications does not fit on array. Possible error CGRA too small, applications overlapping\n");
            return 0;
        }

        for (int i = group_start; i < group_start + num_groups; i++) {
            monitor.groups[i] = 1;
        }
    // DPR is not enabled so just clear the group start
    } else {
        group_start = 0;
    }
    kernel->group_start = group_start;

    // bitstream map
    // always put bitstream first
    int tile;
    tile = group_start * 2;  // one group has two glb tiles
    struct BitstreamInfo *bs_info = get_bs_info(kernel);

    bs_info->tile = tile;
    bs_info->start_addr = ((tile * 2) << BANK_ADDR_WIDTH);
    update_bs_configuration(bs_info);

    // PCFG mux
    int start_tile = group_start * 2;
    for (int i = start_tile; i < (group_start + num_groups) * GROUP_SIZE / 2; i++) {
        if (i == start_tile) {
            add_config(&bs_info->config,
                       (1 << AXI_ADDR_WIDTH) + (i << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_PCFG_BROADCAST_MUX_R,
                       (1 << GLB_PCFG_BROADCAST_MUX_SOUTH_F_LSB) | (1 << GLB_PCFG_BROADCAST_MUX_EAST_F_LSB) |
                           (0 << GLB_PCFG_BROADCAST_MUX_WEST_F_LSB));
        } else {
            add_config(&bs_info->config,
                       (1 << AXI_ADDR_WIDTH) + (i << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_PCFG_BROADCAST_MUX_R,
                       (2 << GLB_PCFG_BROADCAST_MUX_SOUTH_F_LSB) | (2 << GLB_PCFG_BROADCAST_MUX_EAST_F_LSB) |
                           (0 << GLB_PCFG_BROADCAST_MUX_WEST_F_LSB));
        }
    }

    // int num_bs = bs_info->size;
    int num_inputs = kernel->num_inputs;
    int num_outputs = kernel->num_outputs;
    int first_input_tile;
    int last_input_tile;

    struct IOInfo *io_info;
    struct IOTileInfo *io_tile_info;
    for (int i = 0; i < num_inputs; i++) {
        io_info = get_input_info(kernel, i);
        int num_io_tiles = io_info->num_io_tiles;
        for (int j = 0; j < num_io_tiles; j++) {
            io_tile_info = get_io_tile_info(io_info, j);
            tile = (group_start * GROUP_SIZE + io_tile_info->pos.x) / 2;
            io_tile_info->tile = tile;
            io_tile_info->start_addr = (io_tile_info->start_addr << CGRA_BYTE_OFFSET) + ((tile * 2) << BANK_ADDR_WIDTH);
            printf("Mapping input_%0d_block_%0d to global buffer\n", i, j);
            update_io_tile_configuration(io_tile_info, &kernel->config);
            if (i == 0 && j == 0) {
                first_input_tile = tile;
            }
        }
    }
    // book keeping last input tile so we can tie the flush to a unused glb tile
    last_input_tile = tile;

    for (int i = 0; i < num_outputs; i++) {
        io_info = get_output_info(kernel, i);
        int num_io_tiles = io_info->num_io_tiles;
        for (int j = 0; j < num_io_tiles; j++) {
            io_tile_info = get_io_tile_info(io_info, j);
            tile = (group_start * GROUP_SIZE + io_tile_info->pos.x) / 2;
            io_tile_info->tile = tile;
            io_tile_info->start_addr =
                (io_tile_info->start_addr << CGRA_BYTE_OFFSET) + ((tile * 2 + 1) << BANK_ADDR_WIDTH);
            printf("Mapping output_%0d_block_%0d to global buffer\n", i, j);
            update_io_tile_configuration(io_tile_info, &kernel->config);
        }
    }

    // unset padding var after a kernel is mapped
    if(getenv("pad_o_left") != NULL) unsetenv("pad_o_left");
    if(getenv("pad_o_right") != NULL) unsetenv("pad_o_right");

    // configure flush crossbar
    int kernel_crossbar_config = 0;
    if (!kernel->opal_dense_scanner_workaround) {
        for (int i = group_start; i < group_start + num_groups; i++) {
            crossbar_config[i] = first_input_tile;
        }
    } else {
        for (int i = group_start; i < group_start + num_groups; i++) {
            crossbar_config[i] = last_input_tile + 1;
        }
    }

    for (int i = 0; i < MAX_NUM_GROUPS; i++) {
        kernel_crossbar_config += (crossbar_config[i] << (((int)ceil(log(NUM_GLB_TILES) / log(2))) * i));
    }
    add_config(&kernel->config, GLC_GLB_FLUSH_CROSSBAR_R, kernel_crossbar_config << GLC_GLB_FLUSH_CROSSBAR_SEL_F_LSB);
    printf("Configuration of flush signal crossbar is updated to 0x%0x\n", kernel_crossbar_config);

    char* reg_write = kernel->bin_dir;
    strncat(reg_write, "reg_write.h", BUFFER_SIZE);
    FILE *fptr;

    fptr = fopen(reg_write, "w");

    fprintf(fptr, "\n\nstatic void bitstream_glb_config()\n{\n");

    int bs_configs = (&bs_info->config)->num_config;
    for(int i = 0; i < bs_configs; i++){
        fprintf(fptr, "glb_reg_write(0x%lx", (&bs_info->config)->config[i].addr - 0x1000);
        fprintf(fptr, ", 0x%lx);\n", (&bs_info->config)->config[i].data);
    }

    fprintf(fptr, "}\n");
    fprintf(fptr, "\n\nstatic void app_glb_config()\n{\n");

    int configs = (&kernel->config)->num_config;
    for(int i = 0; i < configs; i++){
        if((&kernel->config)->config[i].addr >= 0x1000){
            fprintf(fptr, "glb_reg_write(0x%lx", (&kernel->config)->config[i].addr - 0x1000);
            fprintf(fptr, ", 0x%lx);\n", (&kernel->config)->config[i].data);
        }
    }
    fprintf(fptr, "}\n");

    fclose(fptr);

    return 1;
}

// Hacky functions to update IO tile configurations for output padding
bool output_padding_config(struct IOTileInfo *io_tile_info, int *start_addr, int *cycle_start_addr) {
    // get layer shape from env var parsed in design_meta.json; see parser.c
    // HALIDE_GEN_ARGS added to design_meta.json; see parse_design_meta.py in H2H
    if (getenv("pad_o_left") == NULL && getenv("pad_o_right") == NULL) {
        return false;
    }
    int in_img = atoi(getenv("in_img"));
    int pad_o_left = atoi(getenv("pad_o_left"));
    int pad_o_right = atoi(getenv("pad_o_right"));
    int ksize = atoi(getenv("ksize"));
    int stride = atoi(getenv("stride"));
    int n_oc = atoi(getenv("n_oc"));
    int glb_o = atoi(getenv("glb_o"));
    int out_img = floor((in_img - ksize) / stride) + 1;

    int padded_X_ext = out_img + (pad_o_left + pad_o_right);
    int match_cnt = 0;
    if (io_tile_info->io == Output) {
        // calculate extents and strides for X and Y dims
        for (int i = 0; i < io_tile_info->loop_dim; i++) {
            if (io_tile_info->extent[i] == padded_X_ext) {
                match_cnt++;
                if (match_cnt == 1) {
                    // outer column dim
                    io_tile_info->extent[i] -= (pad_o_left + pad_o_right);
                }
                else if (match_cnt == 2) {
                    // inner row dim
                    io_tile_info->data_stride[i] += (pad_o_left + pad_o_right) * n_oc / glb_o;
                    io_tile_info->extent[i] -= (pad_o_left + pad_o_right);
                    break;
                }
            }
        }

        // Adjust local start_addr for first row padding
        *start_addr += ((n_oc * pad_o_left / glb_o) * (out_img + (pad_o_left + pad_o_right) + 1)) << CGRA_BYTE_OFFSET;

        // Adjust local cycle_start_addr for static mode
        // TODO: The magic number 10 needs a formal calculation method.
        *cycle_start_addr += 10;
    }
    return true;
}

int update_io_tile_configuration(struct IOTileInfo *io_tile_info, struct ConfigInfo *config_info) {
    int tile = io_tile_info->tile;
    int start_addr = io_tile_info->start_addr;
    int cycle_start_addr = io_tile_info->cycle_start_addr;
    int loop_dim = io_tile_info->loop_dim;
    int extent[LOOP_LEVEL];
    int data_stride[LOOP_LEVEL];
    int cycle_stride[LOOP_LEVEL];
    int mux_sel;
    int mode;

    // If pad_o in env var call hacky padding function
    bool use_padding = output_padding_config(io_tile_info, &start_addr, &cycle_start_addr);

    // Convert extent/stride hardware-friendly
    for (int i = 0; i < loop_dim; i++) {
        extent[i] = io_tile_info->extent[i] - 2;
        cycle_stride[i] = io_tile_info->cycle_stride[i];
        data_stride[i] = io_tile_info->data_stride[i];
        for (int j = 0; j < i; j++) {
            cycle_stride[i] -= io_tile_info->cycle_stride[j] * (io_tile_info->extent[j] - 1);
            data_stride[i] -= io_tile_info->data_stride[j] * (io_tile_info->extent[j] - 1);
        }
        data_stride[i] = data_stride[i] << CGRA_BYTE_OFFSET;
    }

    if (io_tile_info->pos.x % 2 == 0)
        mux_sel = 0b01;
    else
        mux_sel = 0b10;

    if (io_tile_info->io == Input) {

        // Point to the other bank if the input is stored in GLB
        if (io_tile_info->is_glb_input == 1) start_addr = start_addr + (1 << BANK_ADDR_WIDTH);

        if (strcmp(io_tile_info->mode, "RV") == 0)
            mode = LD_DMA_VALID_MODE_READY_VALID;
        else
            mode = LD_DMA_VALID_MODE_STATIC;
        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_LD_DMA_CTRL_R,
                   ((0b01 << GLB_LD_DMA_CTRL_MODE_F_LSB) | (mode << GLB_LD_DMA_CTRL_VALID_MODE_F_LSB) |
                    (mux_sel << GLB_LD_DMA_CTRL_DATA_MUX_F_LSB)));
        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_LD_DMA_HEADER_0_DIM_R,
                   loop_dim);
        add_config(
            config_info,
            (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_LD_DMA_HEADER_0_START_ADDR_R,
            start_addr);
        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                       GLB_LD_DMA_HEADER_0_CYCLE_START_ADDR_R,
                   cycle_start_addr);
        printf("Input block mapped to tile: %0d\n", tile);
        printf("Input block start addr: 0x%0x\n", start_addr);
        printf("Input block cycle start addr: %0d\n", cycle_start_addr);
        printf("Input block dimensionality: %0d\n", loop_dim);
        for (int i = 0; i < loop_dim; i++) {
            add_config(config_info,
                       (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                           (GLB_LD_DMA_HEADER_0_RANGE_0_R + 0x0c * i),
                       extent[i] << (GLB_LD_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
            add_config(config_info,
                       (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                           (GLB_LD_DMA_HEADER_0_CYCLE_STRIDE_0_R + 0x0c * i),
                       cycle_stride[i] << (GLB_LD_DMA_HEADER_0_CYCLE_STRIDE_0_CYCLE_STRIDE_F_LSB));
            add_config(config_info,
                       (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                           (GLB_LD_DMA_HEADER_0_STRIDE_0_R + 0x0c * i),
                       data_stride[i] << (GLB_LD_DMA_HEADER_0_STRIDE_0_STRIDE_F_LSB));
        }
        printf("=====Before Optimization=====\n");
        for (int i = 0; i < loop_dim; i++) {
            printf("[ITER CTRL - loop %0d] extent: %0d, cycle stride: %0d, data stride: %0d\n", i,
                   io_tile_info->extent[i], io_tile_info->cycle_stride[i], io_tile_info->data_stride[i]);
        }

        printf("=====After Optimization=====\n");
        for (int i = 0; i < loop_dim; i++) {
            printf("[ITER CTRL - loop %0d] extent: %0d, cycle stride: %0d, data stride: %0d\n", i, extent[i],
                   cycle_stride[i], data_stride[i]);
        }
    } else {
        if (strcmp(io_tile_info->mode, "RV") == 0)
            mode = ST_DMA_VALID_MODE_READY_VALID;
        else
            mode = ST_DMA_VALID_MODE_VALID;

        // If use hacky padding then switch to valid mode
        if (use_padding) mode = ST_DMA_VALID_MODE_STATIC;

        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_ST_DMA_CTRL_R,
                   ((0b01 << GLB_ST_DMA_CTRL_MODE_F_LSB) | (mode << GLB_ST_DMA_CTRL_VALID_MODE_F_LSB) |
                    (mux_sel << GLB_ST_DMA_CTRL_DATA_MUX_F_LSB)));
        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_ST_DMA_NUM_BLOCKS_R,
                   (io_tile_info->num_blocks << GLB_ST_DMA_NUM_BLOCKS_VALUE_F_LSB));
        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_ST_DMA_RV_SEG_MODE_R,
                   (io_tile_info->seg_mode << GLB_ST_DMA_RV_SEG_MODE_VALUE_F_LSB));
        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_ST_DMA_HEADER_0_DIM_R,
                   loop_dim);
        add_config(
            config_info,
            (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_ST_DMA_HEADER_0_START_ADDR_R,
            start_addr);
        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                       GLB_ST_DMA_HEADER_0_CYCLE_START_ADDR_R,
                   cycle_start_addr);
        printf("Output block mapped to tile: %0d\n", tile);
        printf("Output block start addr: 0x%0x\n", start_addr);
        printf("Output block cycle start addr: %0d\n", cycle_start_addr);
        printf("Output block dimensionality: %0d\n", loop_dim);
        for (int i = 0; i < loop_dim; i++) {
            add_config(config_info,
                       (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                           (GLB_ST_DMA_HEADER_0_RANGE_0_R + 0x0c * i),
                       extent[i] << (GLB_ST_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
            add_config(config_info,
                       (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                           (GLB_ST_DMA_HEADER_0_CYCLE_STRIDE_0_R + 0x0c * i),
                       cycle_stride[i] << (GLB_ST_DMA_HEADER_0_CYCLE_STRIDE_0_CYCLE_STRIDE_F_LSB));
            add_config(config_info,
                       (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                           (GLB_ST_DMA_HEADER_0_STRIDE_0_R + 0x0c * i),
                       data_stride[i] << (GLB_ST_DMA_HEADER_0_STRIDE_0_STRIDE_F_LSB));
        }
        printf("=====Before Optimization=====\n");
        for (int i = 0; i < loop_dim; i++) {
            printf("[ITER CTRL - loop %0d] extent: %0d, cycle stride: %0d, data stride: %0d\n", i,
                   io_tile_info->extent[i], io_tile_info->cycle_stride[i], io_tile_info->data_stride[i]);
        }

        printf("=====After Optimization=====\n");
        for (int i = 0; i < loop_dim; i++) {
            printf("[ITER CTRL - loop %0d] extent: %0d, cycle stride: %0d, data stride: %0d\n", i, extent[i],
                   cycle_stride[i], data_stride[i]);
        }
    }
    return 1;
}

void add_config(struct ConfigInfo *config_info, int addr, int data) {
    int idx = config_info->num_config;
    config_info->config[idx].addr = addr;
    config_info->config[idx].data = data;
    config_info->num_config++;
}
