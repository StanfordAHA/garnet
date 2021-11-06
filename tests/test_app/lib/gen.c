#include "glc_addrmap.h"
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
    return GLC_PC_START_PULSE;
}

int get_pcfg_pulse_data(void *info)
{
    GET_BS_INFO(info);
    return 1 << bs_info->tile;
}

int get_strm_pulse_addr()
{
    return GLC_STREAM_START_PULSE;
}

int get_strm_pulse_data(void *info)
{
    GET_KERNEL_INFO(info);
    int num_inputs = kernel_info->num_inputs;
    int num_io_tiles;
    struct IOInfo *io_info;
    int result = 0;

    // Iterate through all input_io_tiles and store it to result
    for (int i = 0; i < num_inputs; i++)
    {
        io_info = kernel_info->input_info[i];
        num_io_tiles = io_info->num_io_tiles;
        for (int j = 0; j < num_io_tiles; j++)
        {
            result |= (1 << io_info->io_tiles[j].tile);
        }
    }

    return result;
}
