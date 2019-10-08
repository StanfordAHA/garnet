package global_buffer_pkg;
    localparam int BANK_DATA_WIDTH = 64;
    localparam int CGRA_DATA_WIDTH = 16;
    localparam int CFG_ADDR_WIDTH = 32;
    localparam int CFG_DATA_WIDTH = 32;

    localparam int GLB_CFG_ADDR_WIDTH = 12;
    localparam int GLB_CFG_TILE_WIDTH = 2;
    localparam int GLB_CFG_FEATURE_WIDTH = 4;
    localparam int GLB_CFG_REG_WIDTH = 4;

    localparam int NUM_TOTAL_BANKS = 32;
    localparam int BANK_ADDR_WIDTH = 17;

    localparam int NUM_TILES = 8;
    localparam int NUM_BANKS = NUM_TOTAL_BANKS / NUM_TILES;

    localparam int AXI_ADDR_WIDTH = 32;
    localparam int TILE_SEL_ADDR_WIDTH = $clog2(NUM_TILES);
    localparam int BANK_SEL_ADDR_WIDTH = $clog2(NUM_BANKS);

    localparam int GLB_ADDR_WIDTH = BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH + TILE_SEL_ADDR_WIDTH;
endpackage
