`ifndef GARNET_PARAM
`define GARNET_PARAM

package garnet_param;

localparam int CGRA_WIDTH = `CGRA_WIDTH;
localparam int NUM_GLB_TILES = CGRA_WIDTH / 2;
localparam int GLB_TILE_MEM_SIZE = `GLB_TILE_MEM_SIZE;
localparam int GLB_ADDR_WIDTH = $clog2(GLB_TILE_MEM_SIZE) + $clog2(NUM_GLB_TILES) + 10;

localparam int AXI_ADDR_WIDTH = `AXI_ADDR_WIDTH;
localparam int AXI_DATA_WIDTH = `AXI_DATA_WIDTH;
localparam int BANK_DATA_WIDTH = 64;

endpackage
`endif
