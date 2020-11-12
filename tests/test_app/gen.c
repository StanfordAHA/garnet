#include "gen.h"
#include "parser.h"
#include "regmap.h"

void *get_pcfg_configuration(void *info) {
    GET_BS_INFO(info);
    return &bs_info->config;
}

void *get_io_configuration(void *info) {
    GET_IO_INFO(info);
    return &io_info->config;
}

void *get_tile_configuration(void *info) {
    GET_PLACE_INFO(info);
    return &place_info->config;
}

int get_configuration_size(void *info) {
    GET_CONFIG_INFO(info);
    return config_info->num_config;
}

int get_configuration_addr(void *info, int index) {
    GET_CONFIG_INFO(info);
    return (config_info->config)[index].addr;
}

int get_configuration_data(void *info, int index) {
    GET_CONFIG_INFO(info);
    return (config_info->config)[index].data;
}

int get_pcfg_pulse_addr() {
    return GLC_PC_START_PULSE;
}

int get_pcfg_pulse_data(void *info) {
    GET_BS_INFO(info);
    return 1 << bs_info->tile;
}

int get_strm_pulse_addr() {
    return GLC_STREAM_START_PULSE;
}

int get_strm_pulse_data(void *info) {
    int num_inputs = get_num_inputs(info);
    GET_PLACE_INFO(info);
    int result = 0;
    for (int i=0; i<num_inputs; i++) {
        result |= (1 << place_info->inputs[i].tile);
    }
    return result;
}
