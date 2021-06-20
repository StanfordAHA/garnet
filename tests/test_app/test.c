#include "parser.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main() {
    struct KernelInfo *info = parse_metadata("bin/design_meta.json");

    assert(info->num_inputs == 1);
    assert(info->num_outputs == 1);

    assert(strcmp(info->bitstream_filename, "bin/design.bs") == 0);
    assert(strcmp(info->placement_filename, "/aha/garnet/temp/design.place") == 0);
    assert(strcmp(info->input_filenames[0], "bin/input.pgm") == 0);
    assert(strcmp(info->gold_filenames[0], "bin/gold.pgm") == 0);


    assert(info->bitstream_info->size == 32);
}
