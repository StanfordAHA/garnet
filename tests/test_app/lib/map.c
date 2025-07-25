#include "map.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "glb.h"
#include "glc.h"
#include "global_buffer_param.h"
#include "matrix_unit_param.h"

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

int get_exchange_64_config() {
    int exchange_64_mode = 0;
    const char *exchange_64_env_var = "E64_MODE_ON";
    char *exchange_64_value = getenv(exchange_64_env_var);
    if (exchange_64_value != NULL && strcmp(exchange_64_value, "1") == 0) {
        exchange_64_mode = 1;
    }
    return exchange_64_mode;
}

int HW_supports_E64() {
    int hw_suports_E64 = 0;
    const char *HW_supports_E64_env_var = "INCLUDE_E64_HW";
    char *hw_support_E64_value = getenv(HW_supports_E64_env_var);
    if (hw_support_E64_value != NULL && strcmp(hw_support_E64_value, "1") == 0) {
        hw_suports_E64 = 1;
    }
    return hw_suports_E64;
}

int get_E64_multi_bank_mode_config() {
    int E64_multi_bank_mode = 0;
    const char *E64_multi_bank_mode_env_var = "E64_MULTI_BANK_MODE_ON";
    char *E64_multi_bank_mode_value = getenv(E64_multi_bank_mode_env_var);
    if (E64_multi_bank_mode_value != NULL && strcmp(E64_multi_bank_mode_value, "1") == 0) {
        E64_multi_bank_mode = 1;
    }
    return E64_multi_bank_mode;
}

int HW_supports_multi_bank() {
    int hw_suports_multi_bank = 0;
    const char *HW_supports_multi_bank_env_var = "INCLUDE_MULTI_BANK_HW";
    char *hw_support_multi_bank_value = getenv(HW_supports_multi_bank_env_var);
    if (hw_support_multi_bank_value != NULL && strcmp(hw_support_multi_bank_value, "1") == 0) {
        hw_suports_multi_bank = 1;
    }
    return hw_suports_multi_bank;
}

int get_MU_input_bubble_mode() {
    int add_mu_input_bubbles = 0;
    const char *add_mu_input_bubbles_env_var = "ADD_MU_INPUT_BUBBLES";
    char *add_mu_input_bubbles_value = getenv(add_mu_input_bubbles_env_var);
    if (add_mu_input_bubbles_value != NULL && strcmp(add_mu_input_bubbles_value, "1") == 0) {
        add_mu_input_bubbles = 1;
    }
    return add_mu_input_bubbles;
}

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

    int first_output_tile;
    int last_output_tile;

    struct IOInfo *io_info;
    struct IOTileInfo *io_tile_info;
    for (int i = 0; i < num_inputs; i++) {
        io_info = get_input_info(kernel, i);
        int num_io_tiles = io_info->num_io_tiles;
        for (int j = 0; j < num_io_tiles; j++) {
            io_tile_info = get_io_tile_info(io_info, j);
            const char *west_io_env_var = "WEST_IN_IO_SIDES";
            char *west_io_value = getenv(west_io_env_var);
            if (west_io_value != NULL && strcmp(west_io_value, "1") == 0) {
                printf("Input placement shifted right by one\n");
                tile = (group_start * GROUP_SIZE + (io_tile_info->pos.x - 1)) / 2;
            } else {
                tile = (group_start * GROUP_SIZE + io_tile_info->pos.x) / 2;
            }
            printf("Group start: %d, pos x: %d\n", group_start, io_tile_info->pos.x);
            io_tile_info->tile = tile;
            if (get_E64_multi_bank_mode_config() && io_tile_info->E64_packed) {
                io_tile_info->start_addr =
                (io_tile_info->start_addr << CGRA_BYTE_OFFSET) + ((tile * 2 + j%2) << BANK_ADDR_WIDTH);
            } else {
                io_tile_info->start_addr =
                (io_tile_info->start_addr << CGRA_BYTE_OFFSET) + ((tile * 2) << BANK_ADDR_WIDTH);
            }

            printf("Mapping input_%0d_block_%0d to global buffer\n", i, j);
            if (io_tile_info->is_fake_io == 0) {
                update_io_tile_configuration(io_tile_info, &kernel->config, kernel);
            }
            else {
                printf("Fake IO tile detected at pos x: %d, skipping configuration\n", io_tile_info->pos.x);
            }
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

            const char *west_io_env_var = "WEST_IN_IO_SIDES";
            char *west_io_value = getenv(west_io_env_var);
            if (west_io_value != NULL && strcmp(west_io_value, "1") == 0) {
                printf("Output placement shifted right by one\n");
                tile = (group_start * GROUP_SIZE + (io_tile_info->pos.x - 1)) / 2;
            } else {
                tile = (group_start * GROUP_SIZE + io_tile_info->pos.x) / 2;
            }

            io_tile_info->tile = tile;
            if (get_E64_multi_bank_mode_config() && io_tile_info->E64_packed) {
                io_tile_info->start_addr =
                (io_tile_info->start_addr << CGRA_BYTE_OFFSET) + ((tile * 2 + j%2) << BANK_ADDR_WIDTH);
                io_tile_info->gold_check_start_addr =
                (io_tile_info->gold_check_start_addr << CGRA_BYTE_OFFSET) + ((tile * 2 + j%2) << BANK_ADDR_WIDTH);
            } else {
                io_tile_info->start_addr =
                (io_tile_info->start_addr << CGRA_BYTE_OFFSET) + ((tile * 2 + 1) << BANK_ADDR_WIDTH);
                io_tile_info->gold_check_start_addr =
                (io_tile_info->gold_check_start_addr << CGRA_BYTE_OFFSET) + ((tile * 2 + 1) << BANK_ADDR_WIDTH);
            }

            printf("Mapping output_%0d_block_%0d to global buffer\n", i, j);
            if (io_tile_info->is_fake_io == 0) {
                update_io_tile_configuration(io_tile_info, &kernel->config, kernel);
            }
            else {
                printf("Fake IO tile detected at pos x: %d, skipping configuration\n", io_tile_info->pos.x);
            }
            if (i == 0 && j == 0) {
                first_output_tile = tile;
            }
        }
    }

    // book keeping last output tile
    last_output_tile = tile;

    // unset padding var after a kernel is mapped
    if(getenv("pad_o_left") != NULL) unsetenv("pad_o_left");
    if(getenv("pad_o_right") != NULL) unsetenv("pad_o_right");

    // configure flush crossbar
    int kernel_crossbar_config = 0;
    if (!kernel->opal_dense_scanner_workaround) {
        for (int i = group_start; i < group_start + num_groups; i++) {

            // MO: Hack to emit flush from output tiles for MU2CGRA app
            if (kernel->app_type == mu2cgra) {
                crossbar_config[i] = first_output_tile;
            } else {
                crossbar_config[i] = first_input_tile;
            }
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
        } else {
            fprintf(fptr, "glc_reg_write(0x%lx", (&kernel->config)->config[i].addr);
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

bool glb_tiling_config(struct KernelInfo *kernel_info, struct IOTileInfo *io_tile_info, int *start_addr, int *cycle_start_addr) {

    if (kernel_info->num_glb_tiling <= 0) return false;
    int n_ic = atoi(getenv("n_ic"));
    int unroll = atoi(getenv("unroll"));

    if (io_tile_info->io == Output) {
        if (io_tile_info->loop_dim == 2) {
            io_tile_info->data_stride[0] *= kernel_info->num_glb_tiling;
            io_tile_info->data_stride[1] *= kernel_info->num_glb_tiling;
        }
        // Adjust local cycle_start_addr for static mode
        // TODO: The magic number 10 needs a formal calculation method.
        *cycle_start_addr += 10;
        printf("Output GLB tiling cnt: %d\n", kernel_info->glb_tiling_cnt);
        *start_addr += (kernel_info->glb_tiling_cnt) * n_ic / unroll << CGRA_BYTE_OFFSET;
    }
    else {
        if (io_tile_info->loop_dim == 2) {
            io_tile_info->data_stride[0] *= kernel_info->num_glb_tiling;
            io_tile_info->data_stride[1] *= kernel_info->num_glb_tiling;
        }
        printf("Input GLB tiling cnt: %d\n", kernel_info->glb_tiling_cnt);
        *start_addr += (kernel_info->glb_tiling_cnt) * n_ic / unroll << CGRA_BYTE_OFFSET;
    }
    return true;
}

int update_io_tile_configuration(struct IOTileInfo *io_tile_info, struct ConfigInfo *config_info, struct KernelInfo *kernel_info) {
    int tile = io_tile_info->tile;
    int start_addr = io_tile_info->start_addr;
    int cycle_start_addr = io_tile_info->cycle_start_addr;
    int loop_dim = io_tile_info->loop_dim;
    int E64_packed = io_tile_info->E64_packed;
    int extent[LOOP_LEVEL];
    int dma_range[LOOP_LEVEL];
    int data_stride[LOOP_LEVEL];
    int cycle_stride[LOOP_LEVEL];
    int mux_sel;
    int mode;
    bool hacked_for_mu_tiling = io_tile_info->hacked_for_mu_tiling;
    int bank_toggle_mode = io_tile_info->bank_toggle_mode;

    // If pad_o in env var call hacky padding function
    bool use_padding = output_padding_config(io_tile_info, &start_addr, &cycle_start_addr);
    bool use_glb_tiling = glb_tiling_config(kernel_info, io_tile_info, &start_addr, &cycle_start_addr);

    // Check if we are in exchange_64 mode
    int exchange_64_mode = get_exchange_64_config();
    if (exchange_64_mode && E64_packed) {
        printf("INFO: Using exchange_64 mode\n");
    }

    int E64_multi_bank_mode = get_E64_multi_bank_mode_config();
    if (E64_multi_bank_mode && E64_packed) {
        printf("INFO: Using exchange_64 with multi-bank mode\n");
    }


    int bytes_written_per_cycle_non_E64_mode = 2;

    // Writing 4x as many bytes in EXCHANGE_64_MODE mode; do -1 b/c addr is 0 indexed
    int E64_start_addr_increment = (4 - 1) * bytes_written_per_cycle_non_E64_mode;


    // Convert extent/stride hardware-friendly
    for (int i = 0; i < loop_dim; i++) {
        extent[i] = io_tile_info->extent[i] - 2;
        dma_range[i] = extent[i];

        cycle_stride[i] = io_tile_info->cycle_stride[i];
        data_stride[i] = io_tile_info->data_stride[i];

        // Skip this adjustment if the addr gen config has already been modified to account for matrix unit's tiling
        // Also skip it if configured in bank toggle mode
        if (!(hacked_for_mu_tiling || bank_toggle_mode)){
            for (int j = 0; j < i; j++) {
                cycle_stride[i] -= io_tile_info->cycle_stride[j] * (io_tile_info->extent[j] - 1);
                data_stride[i] -= io_tile_info->data_stride[j] * (io_tile_info->extent[j] - 1);
            }
        } else {
            if (hacked_for_mu_tiling)
                printf("INFO: Addr gen config hacked for MU tiling for IO tile at (%d, %d), skipping stride adjustment\n", io_tile_info->pos.x, io_tile_info->pos.y);
            if (bank_toggle_mode)
                printf("INFO: Addr gen config hacked for bank toggle mode for IO tile at (%d, %d), skipping stride adjustment\n", io_tile_info->pos.x, io_tile_info->pos.y);
        }

        data_stride[i] = data_stride[i] << CGRA_BYTE_OFFSET;
    }

    int modulo_check;
    const char *west_io_env_var = "WEST_IN_IO_SIDES";
    char *west_io_value = getenv(west_io_env_var);
    if (west_io_value != NULL && strcmp(west_io_value, "1") == 0) {
        printf("I/O bank select shifted right by one\n");
        modulo_check = 1;
    } else {
        modulo_check = 0;
    }

    if (io_tile_info->pos.x % 2 == modulo_check)
        mux_sel = 0b01;
    else
        mux_sel = 0b10;



    if (io_tile_info->io == Input) {

        // Point to the other bank if the input is stored in GLB
        if (io_tile_info->is_glb_input == 1) start_addr = start_addr + (1 << BANK_ADDR_WIDTH);

        if (strcmp(io_tile_info->mode, "RV") == 0) {
            printf("\nIO tiles are in READY-VALID mode\n");
            mode = LD_DMA_VALID_MODE_READY_VALID;
        } else {
            printf("\nIO tiles are in STATIC mode\n");
            mode = LD_DMA_VALID_MODE_STATIC;
        }

        #ifndef GLB_DMA_EXCHANGE_64_MODE_R
        #define GLB_DMA_EXCHANGE_64_MODE_R 0
        #endif

        #ifndef GLB_DMA_EXCHANGE_64_MODE_VALUE_F_LSB
        #define GLB_DMA_EXCHANGE_64_MODE_VALUE_F_LSB 0
        #endif

        if (HW_supports_multi_bank() && HW_supports_E64() && E64_packed) {
            add_config(config_info,
                    (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_DMA_EXCHANGE_64_MODE_R,
                    (E64_multi_bank_mode << GLB_DMA_EXCHANGE_64_MODE_VALUE_F_LSB + 1) |
                    (exchange_64_mode << GLB_DMA_EXCHANGE_64_MODE_VALUE_F_LSB));
        } else if (HW_supports_E64() && E64_packed) {
            add_config(config_info,
                    (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_DMA_EXCHANGE_64_MODE_R,
                    (exchange_64_mode << GLB_DMA_EXCHANGE_64_MODE_VALUE_F_LSB));
        }

        add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_LD_DMA_CTRL_R,
                   ((0b001 << GLB_LD_DMA_CTRL_MODE_F_LSB) | (mode << GLB_LD_DMA_CTRL_VALID_MODE_F_LSB) |
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

            // Count addr 4x faster b/c reading 8 bytes at once instead of 2 bytes
            if (exchange_64_mode && E64_packed) {
                data_stride[i] = data_stride[i] * 4;
            }

            add_config(config_info,
                       (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                           (GLB_LD_DMA_HEADER_0_RANGE_0_R + 0x0c * i),
                       dma_range[i] << (GLB_LD_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
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
        if (strcmp(io_tile_info->mode, "RV") == 0) {
            printf("\nIO tiles are in READY-VALID mode\n");

            const char *dense_rv_env_var = "DENSE_READY_VALID";
            char *dense_rv_value = getenv(dense_rv_env_var);
            if (dense_rv_value != NULL && strcmp(dense_rv_value, "1") == 0) {
                mode = ST_DMA_VALID_MODE_DENSE_READY_VALID;
            } else {
                mode = ST_DMA_VALID_MODE_SPARSE_READY_VALID;
            }

        } else {
             printf("\nIO tiles are in STATIC mode\n");
            mode = ST_DMA_VALID_MODE_VALID;
        }

        // If use hacky padding then switch to valid mode
        if (use_padding || use_glb_tiling) mode = ST_DMA_VALID_MODE_STATIC;

        if (HW_supports_multi_bank() && HW_supports_E64() && E64_packed) {
            add_config(config_info,
                    (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_DMA_EXCHANGE_64_MODE_R,
                    (E64_multi_bank_mode << GLB_DMA_EXCHANGE_64_MODE_VALUE_F_LSB + 1) |
                    ((exchange_64_mode) << GLB_DMA_EXCHANGE_64_MODE_VALUE_F_LSB));
        } else if (HW_supports_E64() && E64_packed) {
            add_config(config_info,
                    (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_DMA_EXCHANGE_64_MODE_R,
                    (exchange_64_mode << GLB_DMA_EXCHANGE_64_MODE_VALUE_F_LSB));
        }

        // Bank toggle mode
        #if defined(GLB_DMA_BANK_TOGGLE_MODE_R) && defined(GLB_DMA_BANK_TOGGLE_MODE_VALUE_F_LSB)
        if (bank_toggle_mode) {
            add_config(config_info,
                    (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_DMA_BANK_TOGGLE_MODE_R,
                     bank_toggle_mode << GLB_DMA_BANK_TOGGLE_MODE_VALUE_F_LSB);
        }
        #endif


        // MO: Hack to emit flush from output tiles for MU2CGRA app
        if (kernel_info->app_type == mu2cgra) {
            printf("INFO: MU2CGRA app detected. Emitting flush from output tiles\n");
            add_config(config_info,
                   (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + GLB_LD_DMA_CTRL_R,
                   ((0b100 << GLB_LD_DMA_CTRL_MODE_F_LSB)));
        }

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

        if (exchange_64_mode && E64_packed) {
            start_addr += E64_start_addr_increment;
        }

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
            // Count 4x faster b/c writing 8 bytes at once instead of 2 bytes
            if (exchange_64_mode && E64_packed) {
                data_stride[i] = data_stride[i] * 4;
            }

            add_config(config_info,
                       (1 << AXI_ADDR_WIDTH) + (tile << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) +
                           (GLB_ST_DMA_HEADER_0_RANGE_0_R + 0x0c * i),
                       dma_range[i] << (GLB_ST_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
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
