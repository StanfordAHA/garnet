// check_io_tile_glb_ranges() (tests/test_app/lib/map.c) against the GLB headers garnet
// generated: an IO tile whose data runs out of its GLB bank must stop the testbench.
//
// usage: glb_ranges_test fit|overlap|past_end|bank_toggle
// Prints GLB_RANGES_OK and exits 0 when the check lets the kernel through; the check
// itself prints "ERROR: GLB: ..." and exits 1.
#include "../test_app/lib/map.c"

static struct KernelInfo kernel;
static struct IOInfo in0, out0;

static void plain_tile(struct IOTileInfo *t, long start, long words) {
    memset(t, 0, sizeof(*t));
    t->start_addr = (int)start;
    t->loop_dim = 1;
    t->data_stride[0] = 1;
    t->extent[0] = (int)words;
}

int main(int argc, char **argv) {
    const long bank = 1L << BANK_ADDR_WIDTH;           // bytes per GLB bank
    const long words = bank >> CGRA_BYTE_OFFSET;       // CGRA words per bank
    const long glb = (long)NUM_GLB_TILES * BANKS_PER_TILE * bank;
    const char *mode = argc > 1 ? argv[1] : "fit";

    kernel.num_glb_tiling = 1;
    kernel.num_inputs = 1;
    kernel.num_outputs = 1;
    kernel.input_info[0] = &in0;
    kernel.output_info[0] = &out0;
    in0.num_io_tiles = out0.num_io_tiles = 1;
    // map.c's layout: input of IO tile 0 in bank 0, its output in bank 1
    plain_tile(&in0.io_tiles[0], 0, words);
    plain_tile(&out0.io_tiles[0], bank, words);

    if (!strcmp(mode, "overlap")) {
        in0.io_tiles[0].extent[0] = (int)(words + 1);      // one word into the output's bank
    } else if (!strcmp(mode, "past_end")) {
        kernel.num_inputs = 0;
        out0.io_tiles[0].start_addr = (int)(glb - bank);   // the last bank
        out0.io_tiles[0].extent[0] = (int)(words + 1);
    } else if (!strcmp(mode, "bank_toggle")) {
        in0.io_tiles[0].extent[0] = (int)(words + 1);      // overlaps, but bank toggle mode
        in0.io_tiles[0].bank_toggle_mode = 1;              // has its own layout: not checked
    } else if (strcmp(mode, "fit")) {
        fprintf(stderr, "unknown mode %s\n", mode);
        return 2;
    }
    check_io_tile_glb_ranges(&kernel);
    printf("GLB_RANGES_OK words_per_bank=%ld byte_offset=%d\n", words, CGRA_BYTE_OFFSET);
    return 0;
}
