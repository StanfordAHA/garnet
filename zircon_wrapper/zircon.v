module Zircon (
	input [12:0] axi4_slave_araddr,
    output axi4_slave_arready,
    input axi4_slave_arvalid,
    input [12:0] axi4_slave_awaddr,
    output axi4_slave_awready,
    input axi4_slave_awvalid,
    input axi4_slave_bready,
    output [1:0] axi4_slave_bresp,
    output axi4_slave_bvalid,
    output [31:0] axi4_slave_rdata,
    input axi4_slave_rready,
    output [1:0] axi4_slave_rresp,
    output axi4_slave_rvalid,
    input [31:0] axi4_slave_wdata,
    output axi4_slave_wready,
    input axi4_slave_wvalid,
    output cgra_running_clk_out,
    input clk_in,
    output interrupt,
    input jtag_tck,
    input jtag_tdi,
    output jtag_tdo,
    input jtag_tms,
    input jtag_trst_n,
    input [20:0] proc_packet_rd_addr,
    output [63:0] proc_packet_rd_data,
    output proc_packet_rd_data_valid,
    input proc_packet_rd_en,
    input [20:0] proc_packet_wr_addr,
    input [63:0] proc_packet_wr_data,
    input proc_packet_wr_en,
    input [7:0] proc_packet_wr_strb,
    input reset_in,

    // Axi for matrix unit
    output         auto_axi_in_aw_ready,
    input          auto_axi_in_aw_valid,
    input          auto_axi_in_aw_bits_id,
    input  [29:0]  auto_axi_in_aw_bits_addr,
    input  [7:0]   auto_axi_in_aw_bits_len,
    input  [2:0]   auto_axi_in_aw_bits_size,
    output         auto_axi_in_w_ready,
    input          auto_axi_in_w_valid,
    input  [63:0]  auto_axi_in_w_bits_data,
    input  [7:0]   auto_axi_in_w_bits_strb,
    input          auto_axi_in_w_bits_last,
    input          auto_axi_in_b_ready,
    output         auto_axi_in_b_valid,
    output         auto_axi_in_ar_ready,
    input          auto_axi_in_ar_valid,
    input          auto_axi_in_ar_bits_id,
    input  [29:0]  auto_axi_in_ar_bits_addr,
    input  [7:0]   auto_axi_in_ar_bits_len,
    input  [2:0]   auto_axi_in_ar_bits_size,
    input          auto_axi_in_r_ready,
    output         auto_axi_in_r_valid,
    output         auto_axi_in_r_bits_id,
    output [63:0]  auto_axi_in_r_bits_data,
    output [1:0]   auto_axi_in_r_bits_resp,
    output         auto_axi_in_r_bits_last
);

	// Interconnect declarations
    logic [15:0] mu2cgra [31:0];
	logic [511:0] outputsFromSystolicArray_dat;
    logic mu2cgra_valid;
    logic cgra2mu_ready;

    Garnet garnet_1 (
        // clk/reset/interrupt
        .clk_in              (clk_in),
        .reset_in            (reset_in),
        .interrupt           (interrupt),
        .cgra_running_clk_out(cgra_running_clk_out),

        // proc ifc
        .proc_packet_wr_en        (proc_packet_wr_en),
        .proc_packet_wr_strb      (proc_packet_wr_strb),
        .proc_packet_wr_addr      (proc_packet_wr_addr),
        .proc_packet_wr_data      (proc_packet_wr_data),
        .proc_packet_rd_en        (proc_packet_rd_en),
        .proc_packet_rd_addr      (proc_packet_rd_addr),
        .proc_packet_rd_data      (proc_packet_rd_data),
        .proc_packet_rd_data_valid(proc_packet_rd_data_valid),

        // axi4-lite ifc
        .axi4_slave_araddr (axi4_slave_araddr),
        .axi4_slave_arready(axi4_slave_arready),
        .axi4_slave_arvalid(axi4_slave_arvalid),
        .axi4_slave_awaddr (axi4_slave_awaddr),
        .axi4_slave_awready(axi4_slave_awready),
        .axi4_slave_awvalid(axi4_slave_awvalid),
        .axi4_slave_bready (axi4_slave_bready),
        .axi4_slave_bresp  (axi4_slave_bresp),
        .axi4_slave_bvalid (axi4_slave_bvalid),
        .axi4_slave_rdata  (axi4_slave_rdata),
        .axi4_slave_rready (axi4_slave_rready),
        .axi4_slave_rresp  (axi4_slave_rresp),
        .axi4_slave_rvalid (axi4_slave_rvalid),
        .axi4_slave_wdata  (axi4_slave_wdata),
        .axi4_slave_wready (axi4_slave_wready),
        .axi4_slave_wvalid (axi4_slave_wvalid),

        // jtag ifc
        .jtag_tck   (jtag_tck),
        .jtag_tdi   (jtag_tdi),
        .jtag_tdo   (jtag_tdo),
        .jtag_tms   (jtag_tms),
        .jtag_trst_n(jtag_trst_n),

        // matrix unit ifc 
        .mu2cgra_valid (mu2cgra_valid),
        .cgra2mu_ready (cgra2mu_ready),
        .mu2cgra(mu2cgra)

    );

	// interconnect 
	genvar i;
	generate
		for (i = 0; i < 32; i = i + 1) begin : assign_mu2cgra
			assign mu2cgra[i] = outputsFromSystolicArray_dat[(i+1)*16-1:i*16];
		end
	endgenerate



    MatrixUnitWrapper matrixUnit_1 (
        // clk /reset
        .auto_clock_in_clock(clk_in),
        .auto_clock_in_reset(reset_in),

        // Unified MU-GLB ifc
        .auto_unified_out_a_ready(1'b0),
        .auto_unified_out_a_valid( /* NO CONN */ ),
        .auto_unified_out_a_bits_opcode( /* NO CONN */ ),
        .auto_unified_out_a_bits_size( /* NO CONN */ ),
        .auto_unified_out_a_bits_source( /* NO CONN */ ),
        .auto_unified_out_a_bits_address( /* NO CONN */ ),
        .auto_unified_out_a_bits_mask( /* NO CONN */ ),
        .auto_unified_out_d_ready( /* NO CONN */ ),
        .auto_unified_out_d_valid(1'b0),
        .auto_unified_out_d_bits_opcode(3'b0),
        .auto_unified_out_d_bits_size(4'b0),
        .auto_unified_out_d_bits_source(7'b0),
        .auto_unified_out_d_bits_data(256'b0),

        // MU-CGRA tile array ifc (fused outputs)
        .io_outputsFromSystolicArray_vld(mu2cgra_valid),
        .io_outputsFromSystolicArray_rdy(cgra2mu_ready),
        .io_outputsFromSystolicArray_dat(outputsFromSystolicArray_dat),

        // MU Axi ifc
        .auto_axi_in_aw_ready(auto_axi_in_aw_ready),
        .auto_axi_in_aw_valid(auto_axi_in_aw_valid),
        .auto_axi_in_aw_bits_id(auto_axi_in_aw_bits_id),
        .auto_axi_in_aw_bits_addr(auto_axi_in_aw_bits_addr),
        .auto_axi_in_aw_bits_len(auto_axi_in_aw_bits_len),
        .auto_axi_in_aw_bits_size(auto_axi_in_aw_bits_size),
        .auto_axi_in_w_ready(auto_axi_in_w_ready),
        .auto_axi_in_w_valid(auto_axi_in_w_valid),
        .auto_axi_in_w_bits_data(auto_axi_in_w_bits_data),
        .auto_axi_in_w_bits_strb(auto_axi_in_w_bits_strb),
        .auto_axi_in_w_bits_last(auto_axi_in_w_bits_last),
        .auto_axi_in_b_ready(auto_axi_in_b_ready),
        .auto_axi_in_b_valid(auto_axi_in_b_valid),
        .auto_axi_in_ar_ready(auto_axi_in_ar_ready),
        .auto_axi_in_ar_valid(auto_axi_in_ar_valid),
        .auto_axi_in_ar_bits_id(auto_axi_in_ar_bits_id),
        .auto_axi_in_ar_bits_addr(auto_axi_in_ar_bits_addr),
        .auto_axi_in_ar_bits_len(auto_axi_in_ar_bits_len),
        .auto_axi_in_ar_bits_size(auto_axi_in_ar_bits_size),
        .auto_axi_in_r_ready(auto_axi_in_r_ready),
        .auto_axi_in_r_valid(auto_axi_in_r_valid),
        .auto_axi_in_r_bits_id(auto_axi_in_r_bits_id),
        .auto_axi_in_r_bits_data(auto_axi_in_r_bits_data),
        .auto_axi_in_r_bits_resp(auto_axi_in_r_bits_resp),
        .auto_axi_in_r_bits_last(auto_axi_in_r_bits_last)
    );
endmodule 