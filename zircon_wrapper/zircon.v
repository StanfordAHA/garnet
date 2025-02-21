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
    input reset_in
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

    MatrixUnit matrixUnit_1 (
        .clk(1'b0),
        .rstn(1'b0),

        .serialMatrixParamsIn_vld(1'b0),
        .serialMatrixParamsIn_rdy( /*NO CONN*/ ),
        .serialMatrixParamsIn_dat(32'b0),

        .inputAddressRequest_vld( /*NO CONN*/ ),
        .inputAddressRequest_rdy(1'b0),
        .inputAddressRequest_dat( /*NO CONN*/ ),
        .inputDataResponse_vld(1'b0),
        .inputDataResponse_rdy( /*NO CONN*/ ),
        .inputDataResponse_dat(512'b0),

        .inputScaleAddressRequest_vld( /*NO CONN*/ ),
        .inputScaleAddressRequest_rdy(1'b0),
        .inputScaleAddressRequest_dat( /*NO CONN*/ ),
        .inputScaleDataResponse_vld(1'b0),
        .inputScaleDataResponse_rdy( /*NO CONN*/ ),
        .inputScaleDataResponse_dat(8'b0),

        .weightAddressRequest_vld( /*NO CONN*/ ),
        .weightAddressRequest_rdy(1'b0),
        .weightAddressRequest_dat( /*NO CONN*/ ),
        .weightDataResponse_vld(1'b0),
        .weightDataResponse_rdy( /*NO CONN*/ ),
        .weightDataResponse_dat(256'b0),

        .biasAddressRequest_vld( /*NO CONN*/ ),
        .biasAddressRequest_rdy(1'b0),
        .biasAddressRequest_dat( /*NO CONN*/ ),
        .biasDataResponse_vld(1'b0),
        .biasDataResponse_rdy( /*NO CONN*/ ),
        .biasDataResponse_dat(256'b0),

        .weightScaleAddressRequest_vld( /*NO CONN*/ ),
        .weightScaleAddressRequest_rdy(1'b0),
        .weightScaleAddressRequest_dat( /*NO CONN*/ ),
        .weightScaleDataResponse_vld(1'b0),
        .weightScaleDataResponse_rdy( /*NO CONN*/ ),
        .weightScaleDataResponse_dat(256'b0),

        .outputsFromSystolicArray_vld(mu2cgra_valid),
        .outputsFromSystolicArray_rdy(cgra2mu_ready),
        .outputsFromSystolicArray_dat(outputsFromSystolicArray_dat),

        .startSignal_vld( /*NO CONN*/ ),
        .startSignal_rdy(1'b0),
        .doneSignal_vld( /*NO CONN*/ ),
        .doneSignal_rdy(1'b0)
        );


endmodule 