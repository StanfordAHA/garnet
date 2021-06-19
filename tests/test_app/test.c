#include "parser.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main() {
    struct KernelInfo *info = parse_metadata("bin/design_meta.json");
 //    // struct KernelInfo *p = parse_placement("vectors/design.place");
    // assert(p->outputs[2] == 1);
    // assert(p->outputs[3] == 0);
    // assert(p->num_groups == 1);
    // assert(p->num_outputs == 3);

    // struct MetaInfo *info = parse_metadata("vectors/design.meta");
    // assert(strncmp(info->placement_filename, "vectors/design.place", 21) == 0);
    // assert(strncmp(info->bitstream_filename, "vectors/design.bs", 6) == 0);
    // assert(strncmp(info->input_filenames[0], "vectors/a", 10) == 0);
    // assert(strncmp(info->output_filenames[2], "vectors/e", 14) == 0);
    // assert(info->input_size == 8);
    // assert(info->output_size == 4);
}
