`ifndef GLOBAL_BUFFER_PKG
`define GLOBAL_BUFFER_PKG

package global_buffer_pkg;
    localparam int BANK_DATA_WIDTH = 64;
    localparam int CGRA_DATA_WIDTH = 16;
    localparam int CFG_ADDR_WIDTH = 32;
    localparam int CFG_DATA_WIDTH = 32;

    localparam int BANK_ADDR_BYTE_OFFSET = $clog2(BANK_DATA_WIDTH/8);

    localparam int NUM_TOTAL_BANKS = 32;
    localparam int BANK_ADDR_WIDTH = 17;

    localparam int NUM_TILES = 8;
    localparam int NUM_BANKS = NUM_TOTAL_BANKS / NUM_TILES;

    localparam int AXI_ADDR_WIDTH = 32;
    localparam int TILE_SEL_ADDR_WIDTH = $clog2(NUM_TILES);
    localparam int BANK_SEL_ADDR_WIDTH = $clog2(NUM_BANKS);

    localparam int GLB_ADDR_WIDTH = BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH + TILE_SEL_ADDR_WIDTH;

    localparam int CONFIG_DATA_WIDTH = 32;

    localparam int GLB_CFG_ADDR_WIDTH = 12;
    localparam int GLB_CFG_BYTE_OFFSET = $clog2(CFG_DATA_WIDTH/8);
    localparam int GLB_CFG_TILE_WIDTH = $clog2(NUM_TILES);
    localparam int GLB_CFG_FEATURE_WIDTH = 2;
    localparam int GLB_CFG_REG_WIDTH = GLB_CFG_ADDR_WIDTH - GLB_CFG_TILE_WIDTH - GLB_CFG_FEATURE_WIDTH - GLB_CFG_BYTE_OFFSET;

    localparam int MODE_BIT_WIDTH = 2;
    typedef logic [MODE_BIT_WIDTH-1:0] addr_gen_mode_t;
    localparam addr_gen_mode_t IDLE = 0;
    localparam addr_gen_mode_t INSTREAM = 1;
    localparam addr_gen_mode_t OUTSTREAM = 2;
    localparam addr_gen_mode_t SRAM = 3;

endpackage

`endif
