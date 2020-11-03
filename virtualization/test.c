#include "parser.h"
#include "map.h"
#include "gen.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main() {
    int num_app = 1;
    void *kernels[num_app];

    kernels[0] = parse_metadata("app0/design.meta");
    //kernels[1] = parse_metadata("app1/design.meta");
    //kernels[0] = parse_metadata("/sim/kongty/aha/Halide-to-Hardware/apps/hardware_benchmarks/tests/conv_3_3/bin/design.meta");

    printf("%s\n", ((struct KernelInfo*)kernels[0])->placement_filename);

    for (int i=0; i < num_app; i++) {
        if (glb_map(kernels[i]) == 0) {
            printf("glb map failed\n");
            return 0;
        }
    }
    printf("glb map success\n");

    //assert(strncmp(kernels[0]->placement_filename, "app0/design.place", 21) == 0);
    //assert(strncmp(kernels[0]->bitstream_filename, "app0/design.bs", 6) == 0);
    //assert(strncmp(kernels[0]->input_filenames[0], "app0/a", 10) == 0);
    //assert(strncmp(kernels[0]->output_filenames[2], "app0/e", 14) == 0);
    //assert(kernels[0]->input_size[0] == 8);
    //assert(kernels[0]->output_size[0] == 4);

    struct PlaceInfo *p = ((struct KernelInfo*)kernels[0])->place_info;
    printf("get input size: %d\n", get_input_size(p, 0));
    printf("get input start_addr: %d\n", get_input_start_addr(p, 0));
    printf("num_groups: %d\n", p->num_groups);

    struct BitstreamInfo *b = get_bs_info(kernels[0]);
    printf("num_inputs: %d\n", get_num_inputs(p));
    printf("pcfg start addr: %x, data: %x\n", get_pcfg_pulse_addr(), get_pcfg_pulse_data(b));
    printf("strm start addr: %x, data: %x\n", get_strm_pulse_addr(), get_strm_pulse_data(p));

    struct IOInfo *i = get_output_info(p, 1);
    struct ConfigInfo *io_cfg = get_io_configuration(i);
    int io_cfg_size = get_configuration_size(io_cfg);
    printf("io_cfg_size: %d\n", io_cfg_size);
    for(int i=0; i<io_cfg_size; i++) {
        printf("addr: %x, data: %x\n", get_configuration_addr(io_cfg, i), get_configuration_data(io_cfg, i));
    }
    struct ConfigInfo *tile_cfg = get_tile_configuration(p);
    int tile_cfg_size = get_configuration_size(tile_cfg);
    printf("tile_cfg_size: %d\n", tile_cfg_size);

}
