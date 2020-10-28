`ifndef GARNET_PARAM
`define GARNET_PARAM

package garnet_param;

localparam int NUM_GLB_TILES = 16;
localparam int NUM_COLS = 16;
localparam int NUM_BANKS = 32;
localparam int BANK_DATA_WIDTH = 64;
localparam int BANK_ADDR_WIDTH = 17;
localparam int GLB_ADDR_WIDTH = BANK_ADDR_WIDTH + $clog2(NUM_BANKS);

localparam int CGRA_DATA_WIDTH = 16;

localparam int AXI_ADDR_WIDTH = 13;
localparam int AXI_DATA_WIDTH = 32;

endpackage
`endif
