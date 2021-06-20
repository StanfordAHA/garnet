#include "parser.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main() {
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

    assert(info->output_info[0]->io == Output);
    assert(strcmp(info->output_info[0]->filename, "bin/gold.pgm") == 0);
    assert(info->output_info[0]->num_io_tiles == 1);
}
