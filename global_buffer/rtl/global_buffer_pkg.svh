`ifndef GLOBAL_BUFFER_PKG
`define GLOBAL_BUFFER_PKG

package global_buffer_pkg;

import global_buffer_param::*;

//============================================================================//
// Packet struct definition
//============================================================================//
typedef enum logic[1:0] {PSEL_NONE=2'd0, PSEL_PROC=2'd1, PSEL_PCFG = 2'd2, PSEL_STRM=2'd3} packet_type_t; 

typedef struct packed 
{
    logic[TILE_SEL_ADDR_WIDTH-1:0] src;
    packet_type_t packet_type;
} packet_sel_t;

// SRAM write packet
typedef struct packed
{
    // packet_sel_t                    packet_sel;
    logic [0:0]                     wr_en;
    logic [BANK_DATA_WIDTH/8-1:0]   wr_strb;
    logic [GLB_ADDR_WIDTH-1:0]      wr_addr;
    logic [BANK_DATA_WIDTH-1:0]     wr_data;
} wr_packet_t;

// SRAM read req packet
typedef struct packed
{
    // packet_sel_t                    packet_sel;
    logic [0:0]                     rd_en;
    logic [GLB_ADDR_WIDTH-1:0]      rd_addr;
} rdrq_packet_t;

// SRAM read res packet
typedef struct packed
{
    // packet_sel_t                    packet_sel;
    logic [BANK_DATA_WIDTH-1:0]     rd_data;
    logic [0:0]                     rd_data_valid;
} rdrs_packet_t;

// rd_packet
typedef struct packed
{
    rdrq_packet_t   rdrq;
    rdrs_packet_t   rdrs;
} rd_packet_t;

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
localparam [1:0] DMA_OFF        = 2'b00;
localparam [1:0] NORMAL     = 2'b01;
localparam [1:0] REPEAT     = 2'b10;
localparam [1:0] AUTO_INCR  = 2'b11;


typedef struct packed
{
    logic [MAX_NUM_WORDS_WIDTH-1:0]     range;
    logic [MAX_STRIDE_WIDTH-1:0]    stride;
} loop_ctrl_t;

typedef struct packed
{
    logic [0:0]                     valid; // 1
    logic [GLB_ADDR_WIDTH-1:0]      start_addr; // 22
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

endpackage
`endif
