#include "parser.h"
#include "map.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main() {
    // parse.c test
    struct KernelInfo *info = parse_metadata("bin/design_meta.json");
    assert(info->num_inputs == 1);
    assert(info->num_outputs == 1);
    assert(info->num_groups == 1);

    assert(strcmp(info->bitstream_filename, "bin/design.bs") == 0);
    assert(strcmp(info->placement_filename, "/aha/garnet/temp/design.place") == 0);
    assert(info->bitstream_info->size == 32);

    assert(info->input_info[0]->io == Input);
    assert(strcmp(info->input_info[0]->filename, "bin/input.pgm") == 0);
    assert(info->input_info[0]->num_io_tiles == 1);
    assert(info->input_info[0]->io_tiles[0].pos.x == 0);
    assert(info->input_info[0]->io_tiles[0].pos.y == 0);
    assert(info->input_info[0]->io_tiles[0].loop_dim == 1);
    assert(info->input_info[0]->io_tiles[0].stride[0] == 1);
    assert(info->input_info[0]->io_tiles[0].extent[0] == 4096);

    assert(info->output_info[0]->io == Output);
    assert(strcmp(info->output_info[0]->filename, "bin/gold.pgm") == 0);
    assert(info->output_info[0]->num_io_tiles == 1);
    assert(info->output_info[0]->io_tiles[0].pos.x == 1);
    assert(info->output_info[0]->io_tiles[0].pos.y == 0);
    assert(info->output_info[0]->io_tiles[0].loop_dim == 2);
    assert(info->output_info[0]->io_tiles[0].stride[0] == 1);
    assert(info->output_info[0]->io_tiles[0].stride[1] == 64);
    assert(info->output_info[0]->io_tiles[0].extent[0] == 63);
    assert(info->output_info[0]->io_tiles[0].extent[1] == 64);

    // map.c test
    assert(initialize_monitor(32) == 1);
    assert(glb_map(info) == 1);
    assert(info->config.num_config == 7);
    // for (int i=0; i<7; i++) {
    //     printf("addr: %x, data: %x\n", info->config.config[i].addr, info->config.config[i].data);
    // }
    assert(info->config.config[0].addr == 0x103c);
    assert(info->config.config[0].data == 0x100);
    assert(info->config.config[1].addr == 0x1044);
    assert(info->config.config[1].data == 0x400001);
    assert(info->config.config[2].addr == 0x1038);
    assert(info->config.config[2].data == 0x1);
    assert(info->config.config[3].addr == 0x100c);
    assert(info->config.config[3].data == 0x20000);
    assert(info->config.config[4].addr == 0x1010);
    assert(info->config.config[4].data == 0xfc0);
    assert(info->config.config[5].addr == 0x1008);
    assert(info->config.config[5].data == 0x1);
    assert(info->config.config[6].addr == 0x1000);
    assert(info->config.config[6].data == 0x564);
}
