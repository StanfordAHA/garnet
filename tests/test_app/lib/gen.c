#include "glc.h"
#include "gen.h"
#include "parser.h"

void *get_pcfg_configuration(void *info)
{
    GET_BS_INFO(info);
    return &bs_info->config;
}

// TODO: All io configuration are stored in KernelInfo
void *get_kernel_configuration(void *info)
{
    GET_KERNEL_INFO(info);
    return &kernel_info->config;
}

int get_configuration_size(void *info)
{
    GET_CONFIG_INFO(info);
    return config_info->num_config;
}

int get_configuration_addr(void *info, int index)
{
    GET_CONFIG_INFO(info);
    return (config_info->config)[index].addr;
}

int get_configuration_data(void *info, int index)
{
    GET_CONFIG_INFO(info);
    return (config_info->config)[index].data;
}

int get_pcfg_pulse_addr()
{
    return GLC_PC_START_PULSE_R;
}

int get_pcfg_pulse_data(void *info)
{
    GET_BS_INFO(info);
    return 1 << bs_info->tile;
}

int get_strm_pulse_addr()
{
    return GLC_STREAM_START_PULSE_R;
}

int get_strm_pulse_data(void *info)
{
    GET_KERNEL_INFO(info);
    int num_inputs = kernel_info->num_inputs;
    int num_outputs = kernel_info->num_outputs;
    int num_io_tiles;
    struct IOInfo *io_info;
    int g2f_mask = 0;
    int f2g_mask = 0;
    int mask;

    // Iterate through all io_tiles and store it to result
    for (int i = 0; i < num_inputs; i++)
    {
        io_info = kernel_info->input_info[i];
        num_io_tiles = io_info->num_io_tiles;
        for (int j = 0; j < num_io_tiles; j++)
        {
            g2f_mask |= (1 << io_info->io_tiles[j].tile);
        }
    }

    for (int i = 0; i < num_outputs; i++)
    {
        io_info = kernel_info->output_info[i];
        num_io_tiles = io_info->num_io_tiles;
        for (int j = 0; j < num_io_tiles; j++)
        {
            f2g_mask |= (1 << io_info->io_tiles[j].tile);
        }
    }
    mask = (f2g_mask << GLC_STREAM_START_PULSE_F2G_GLB_TILE_0_F_LSB) | (g2f_mask << GLC_STREAM_START_PULSE_G2F_GLB_TILE_0_F_LSB);

    return mask;
}
