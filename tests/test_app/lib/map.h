#ifndef GLB_MAP_LIBRARY_H
#define GLB_MAP_LIBRARY_H

int glb_map(void *kernel);
int initialize_monitor(int num_cols);
int update_io_tile_configuration(struct IOTileInfo *io_tile_info, struct ConfigInfo *config_info);
void update_bs_configuration(struct BitstreamInfo *bs_info);
void add_config(struct ConfigInfo *config_info, int addr, int data);

#endif
