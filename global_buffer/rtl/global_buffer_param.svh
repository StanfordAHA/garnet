`ifndef GLOBAL_BUFFER_PARAM
`define GLOBAL_BUFFER_PARAM
package global_buffer_param;
localparam int NUM_GLB_TILES = 16;
localparam int TILE_SEL_ADDR_WIDTH = 4;
localparam int NUM_CGRA_TILES = 32;
localparam int CGRA_PER_GLB = 2;
localparam int BANKS_PER_TILE = 2;
localparam int BANK_SEL_ADDR_WIDTH = 1;
localparam int BANK_DATA_WIDTH = 64;
localparam int BANK_ADDR_WIDTH = 17;
localparam int BANK_BYTE_OFFSET = 3;
localparam int GLB_ADDR_WIDTH = 22;
localparam int CGRA_DATA_WIDTH = 16;
localparam int CGRA_BYTE_OFFSET = 1;
localparam int AXI_ADDR_WIDTH = 12;
localparam int AXI_DATA_WIDTH = 32;
localparam int AXI_STRB_WIDTH = 4;
localparam int AXI_BYTE_OFFSET = 2;
localparam int MAX_NUM_WORDS_WIDTH = 21;
localparam int MAX_STRIDE_WIDTH = 11;
localparam int MAX_NUM_CFGS_WIDTH = 19;
localparam int CGRA_CFG_ADDR_WIDTH = 32;
localparam int CGRA_CFG_DATA_WIDTH = 32;
localparam int QUEUE_DEPTH = 4;
localparam int LOOP_LEVEL = 4;
localparam int LATENCY_WIDTH = 5;
endpackage
`endif
