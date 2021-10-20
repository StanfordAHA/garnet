`ifndef GARNET_PARAM
`define GARNET_PARAM

package tb_global_buffer_param;

localparam int NUM_PRR = 8;
localparam int NUM_PRR_WIDTH = $clog2(NUM_PRR);
localparam int PRR_CFG_REG_DEPTH = 16;

endpackage
`endif
