#ifndef GLB_MAP_LIBRARY_H
#define GLB_MAP_LIBRARY_H
#include "parser.h"

int glb_map(void *kernel, int is_first);
int initialize_monitor(int num_cols);
int update_io_tile_configuration(struct IOTileInfo *io_tile_info, struct ConfigInfo *config_info, int is_first);
void update_bs_configuration(struct BitstreamInfo *bs_info);
void add_config(struct ConfigInfo *config_info, int addr, int data);

#endif
