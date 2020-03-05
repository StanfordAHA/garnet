package global_buffer_pkg;

//============================================================================//
// Parameter definition
//============================================================================//
// Tile parameters
localparam int NUM_TILES = 16;
localparam int TILE_SEL_ADDR_WIDTH = $clog2(NUM_TILES);

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
localparam int MAX_NUM_WORDS_WIDTH = GLB_ADDR_WIDTH - BANK_ADDR_BYTE_OFFSET + $clog2(BANK_DATA_WIDTH/CGRA_DATA_WIDTH);

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
    logic                           wr_en;
    logic [BANK_DATA_WIDTH/8-1:0]   wr_strb;
    logic [GLB_ADDR_WIDTH-1:0]      wr_addr;
    logic [BANK_DATA_WIDTH-1:0]     wr_data;
} wr_packet_t;

// SRAM read req packet
typedef struct packed
{
    logic                           rd_en;
    logic [GLB_ADDR_WIDTH-1:0]      rd_addr;
} rdrq_packet_t;

// SRAM read res packet
typedef struct packed
{
    logic [BANK_DATA_WIDTH-1:0]     rd_data;
    logic                           rd_data_valid;
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
    logic                           cfg_wr_en;
    logic                           cfg_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0] cfg_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0] cfg_data;
} cgra_cfg_t;

//============================================================================//
// DMA register struct definition
//============================================================================//
typedef struct packed
{
    logic                           valid;
    logic [GLB_ADDR_WIDTH-1:0]      start_addr;
    logic [MAX_NUM_WORDS_WIDTH-1:0] num_words;
} dma_st_header_t;

typedef struct packed
{
    logic                           valid;
    logic                           repeat_on;
    logic                           inactive_on;
    logic [GLB_ADDR_WIDTH-1:0]      start_addr;
    logic [MAX_NUM_WORDS_WIDTH-1:0] num_words;
    logic [MAX_NUM_WORDS_WIDTH-1:0] active_words_per_cycle;
    logic [MAX_NUM_WORDS_WIDTH-1:0] inactive_words_per_cycle;
} dma_ld_header_t;

//============================================================================//
// Address map
//============================================================================//
localparam int AXI_ADDR_IER = 'h0;
localparam int AXI_ADDR_ISR = 'h4;

endpackage
