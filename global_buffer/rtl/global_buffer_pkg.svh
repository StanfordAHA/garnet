package global_buffer_pkg;

//============================================================================//
// Parameter definition
//============================================================================//
// Tile parameters
localparam int NUM_GLB_TILES = 16;
localparam int TILE_SEL_ADDR_WIDTH = $clog2(NUM_GLB_TILES);

// CGRA Tiles
localparam int NUM_CGRA_TILES = 32;

// CGRA tiles per GLB tile
localparam int CGRA_PER_GLB = NUM_CGRA_TILES / NUM_GLB_TILES; // 2

// Bank parameters
localparam int BANKS_PER_TILE = 2;
localparam int BANK_SEL_ADDR_WIDTH = $clog2(BANKS_PER_TILE);
localparam int BANK_DATA_WIDTH = 64;
localparam int BANK_ADDR_WIDTH = 17;
localparam int BANK_ADDR_BYTE_OFFSET = $clog2(BANK_DATA_WIDTH/8);

// Glb parameters
localparam int GLB_ADDR_WIDTH = BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH + TILE_SEL_ADDR_WIDTH;

// CGRA data parameters
localparam int CGRA_DATA_WIDTH = 16;

// MAX_NUM_WORDS
localparam int MAX_NUM_WORDS_WIDTH = GLB_ADDR_WIDTH - BANK_ADDR_BYTE_OFFSET + $clog2(BANK_DATA_WIDTH/CGRA_DATA_WIDTH); // 21
// MAX_NUM_CFG
localparam int MAX_NUM_CFGS_WIDTH = GLB_ADDR_WIDTH - BANK_ADDR_BYTE_OFFSET; // 19

// Glb config parameters
localparam int AXI_ADDR_WIDTH = 12;
localparam int AXI_DATA_WIDTH = 32;
localparam int AXI_STRB_WIDTH = (AXI_DATA_WIDTH / 8);
localparam int AXI_BYTE_OFFSET = $clog2(AXI_DATA_WIDTH/8);
localparam int CFG_REG_SEL_WIDTH = AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH - AXI_BYTE_OFFSET;

// CGRA config parameters
localparam int CGRA_CFG_ADDR_WIDTH = 32;
localparam int CGRA_CFG_DATA_WIDTH = 32;

// DMA header queue depth
localparam int QUEUE_DEPTH = 4;

//============================================================================//
// Packet struct definition
//============================================================================//
// SRAM write packet
typedef struct packed
{
    logic [0:0]                     wr_en;
    logic [BANK_DATA_WIDTH/8-1:0]   wr_strb;
    logic [GLB_ADDR_WIDTH-1:0]      wr_addr;
    logic [BANK_DATA_WIDTH-1:0]     wr_data;
} wr_packet_t;

// SRAM read req packet
typedef struct packed
{
    logic [0:0]                     rd_en;
    logic [GLB_ADDR_WIDTH-1:0]      rd_addr;
} rdrq_packet_t;

// SRAM read res packet
typedef struct packed
{
    logic [BANK_DATA_WIDTH-1:0]     rd_data;
    logic [0:0]                     rd_data_valid;
} rdrs_packet_t;

// packet
typedef struct packed
{
    wr_packet_t     wr;
    rdrq_packet_t   rdrq;
    rdrs_packet_t   rdrs;
} packet_t;

typedef struct packed
{
    logic [0:0]                     cfg_wr_en;
    logic [0:0]                     cfg_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0] cfg_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0] cfg_data;
} cgra_cfg_t;

//============================================================================//
// DMA register struct definition
//============================================================================//
localparam int MAX_RANGE_WIDTH = MAX_NUM_WORDS_WIDTH; // 21
localparam int MAX_STRIDE_WIDTH = AXI_DATA_WIDTH - MAX_RANGE_WIDTH; // 11
localparam int LOOP_LEVEL = 4;

localparam [1:0] OFF        = 2'b00;
localparam [1:0] NORMAL     = 2'b01;
localparam [1:0] REPEAT     = 2'b10;
localparam [1:0] AUTO_INCR  = 2'b11;


typedef struct packed
{
    logic [MAX_RANGE_WIDTH-1:0]     range;
    logic [MAX_STRIDE_WIDTH-1:0]    stride;
} loop_ctrl_t;

typedef struct packed
{
    logic [0:0]                     valid;
    logic [GLB_ADDR_WIDTH-1:0]      start_addr;
    logic [MAX_NUM_WORDS_WIDTH-1:0] num_words;
} dma_st_header_t;

typedef struct packed
{
    logic [0:0]                     valid;
    logic [GLB_ADDR_WIDTH-1:0]      start_addr;
    loop_ctrl_t [LOOP_LEVEL-1:0]    iteration;
    logic [MAX_NUM_WORDS_WIDTH-1:0] num_active_words;
    logic [MAX_NUM_WORDS_WIDTH-1:0] num_inactive_words; // if it is not 0, active cycles + inactive cycles repeat
} dma_ld_header_t;

// for itr2 in range2:
//     for itr1 in range1:
//         for itr0 in range0:
//            addr = start_addr + itr0 * str0 + itr1 * str1 + itr2 * str2

typedef struct packed
{
    logic [GLB_ADDR_WIDTH-1:0]      start_addr;
    logic [MAX_NUM_CFGS_WIDTH-1:0]  num_cfgs;
} dma_pc_header_t;

//============================================================================//
// Address map
//============================================================================//
localparam int AXI_ADDR_IER_1       = 'h00;
localparam int AXI_ADDR_IER_2       = 'h04;
localparam int AXI_ADDR_ISR_1       = 'h08;
localparam int AXI_ADDR_ISR_2       = 'h0c;
localparam int AXI_ADDR_STRM_START  = 'h10;

endpackage
