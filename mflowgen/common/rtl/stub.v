
module Garnet (
    input [11:0] axi4_ctrl_araddr,
    output axi4_ctrl_arready,
    input axi4_ctrl_arvalid,
    input [11:0] axi4_ctrl_awaddr,
    output axi4_ctrl_awready,
    input axi4_ctrl_awvalid,
    output axi4_ctrl_interrupt,
    output [31:0] axi4_ctrl_rdata,
    input axi4_ctrl_rready,
    output [1:0] axi4_ctrl_rresp,
    output axi4_ctrl_rvalid,
    input [31:0] axi4_ctrl_wdata,
    output axi4_ctrl_wready,
    input axi4_ctrl_wvalid,
    output cgra_running_clk_out,
    input clk_in,
    input jtag_tck,
    input jtag_tdi,
    output jtag_tdo,
    input jtag_tms,
    input jtag_trst_n,
    input reset_in,
    input [31:0] soc_data_rd_addr,
    output [63:0] soc_data_rd_data,
    input soc_data_rd_en,
    input [31:0] soc_data_wr_addr,
    input [63:0] soc_data_wr_data,
    input [7:0] soc_data_wr_strb
);

  assign axi4_ctrl_arready = 'b0;
  assign axi4_ctrl_awready = 'b0;
  assign axi4_ctrl_interrupt = 'b0;
  assign axi4_ctrl_rdata = 'b0;
  assign axi4_ctrl_rresp = 'b0;
  assign axi4_ctrl_rvalid = 'b1;
  assign axi4_ctrl_wready = 'b0;
  assign cgra_running_clk_out = 'b0;
  assign jtag_tdo = 'b0;
  assign soc_data_rd_data = 'b0;

endmodule // Garnet
