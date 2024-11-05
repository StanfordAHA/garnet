/*=============================================================================
** Module: top.sv
** Description:
**              top for garnet testbench
** Author: Taeyoung Kong
** Change history:
**  10/14/2020 - Implement the first version
**===========================================================================*/
`ifndef CLK_PERIOD
`define CLK_PERIOD 1ns
`endif

import global_buffer_param::*;

module top;
    timeunit 1ns; timeprecision 1ps;

    logic clk;
    logic reset;
    logic interrupt;

    //============================================================================//
    // clk / reset generation
    //============================================================================//
    // clk generation
    initial begin
        clk = 0;
        forever #(`CLK_PERIOD / 2.0) clk = !clk;
    end

    // reset generation
    initial begin
        reset <= 1;
        repeat (3) @(posedge clk);
        reset <= 0;
    end

    //============================================================================//
    // interfaces
    //============================================================================//
    proc_ifc p_ifc (.clk(clk));
    axil_ifc #(
        .ADDR_WIDTH(CGRA_AXI_ADDR_WIDTH),
        .DATA_WIDTH(CGRA_AXI_DATA_WIDTH)
    ) axil_ifc (
        .clk(clk)
    );

    //============================================================================//
    // instantiate test
    //============================================================================//
    garnet_test test (
        .clk     (clk),
        .reset   (reset),
        .p_ifc   (p_ifc),
        .axil_ifc(axil_ifc)
    );

    wire [16:0] mu2cgra [31:0];
    assign mu2cgra[0] = 17'b1;
    assign mu2cgra[1] = 17'b1;
    assign mu2cgra[2] = 17'b1;
    assign mu2cgra[3] = 17'b1;
    assign mu2cgra[4] = 17'b1;
    assign mu2cgra[5] = 17'b1;
    assign mu2cgra[6] = 17'b1;
    assign mu2cgra[7] = 17'b1;
    assign mu2cgra[8] = 17'b1;
    assign mu2cgra[9] = 17'b1;
    assign mu2cgra[10] = 17'b1;
    assign mu2cgra[11] = 17'b1;
    assign mu2cgra[12] = 17'b1;
    assign mu2cgra[13] = 17'b1;
    assign mu2cgra[14] = 17'b1;
    assign mu2cgra[15] = 17'b1;
    assign mu2cgra[16] = 17'b1;
    assign mu2cgra[17] = 17'b1;
    assign mu2cgra[18] = 17'b1;
    assign mu2cgra[19] = 17'b1;
    assign mu2cgra[20] = 17'b1;
    assign mu2cgra[21] = 17'b1;
    assign mu2cgra[22] = 17'b1;
    assign mu2cgra[23] = 17'b1;
    assign mu2cgra[24] = 17'b1;
    assign mu2cgra[25] = 17'b1;
    assign mu2cgra[26] = 17'b1;
    assign mu2cgra[27] = 17'b1;
    assign mu2cgra[28] = 17'b1;
    assign mu2cgra[29] = 17'b1;
    assign mu2cgra[30] = 17'b1;
    assign mu2cgra[31] = 17'b1;




    //============================================================================//
    // instantiate dut
    //============================================================================//
    Garnet dut (
        // clk/reset/interrupt
        .clk_in              (clk),
        .reset_in            (reset),
        .interrupt           (interrupt),
        .cgra_running_clk_out(  /*unused*/),

        // proc ifc
        .proc_packet_wr_en        (p_ifc.wr_en),
        .proc_packet_wr_strb      (p_ifc.wr_strb),
        .proc_packet_wr_addr      (p_ifc.wr_addr),
        .proc_packet_wr_data      (p_ifc.wr_data),
        .proc_packet_rd_en        (p_ifc.rd_en),
        .proc_packet_rd_addr      (p_ifc.rd_addr),
        .proc_packet_rd_data      (p_ifc.rd_data),
        .proc_packet_rd_data_valid(p_ifc.rd_data_valid),

        // axi4-lite ifc
        .axi4_slave_araddr (axil_ifc.araddr),
        .axi4_slave_arready(axil_ifc.arready),
        .axi4_slave_arvalid(axil_ifc.arvalid),
        .axi4_slave_awaddr (axil_ifc.awaddr),
        .axi4_slave_awready(axil_ifc.awready),
        .axi4_slave_awvalid(axil_ifc.awvalid),
        .axi4_slave_bready (axil_ifc.bready),
        .axi4_slave_bresp  (axil_ifc.bresp),
        .axi4_slave_bvalid (axil_ifc.bvalid),
        .axi4_slave_rdata  (axil_ifc.rdata),
        .axi4_slave_rready (axil_ifc.rready),
        .axi4_slave_rresp  (axil_ifc.rresp),
        .axi4_slave_rvalid (axil_ifc.rvalid),
        .axi4_slave_wdata  (axil_ifc.wdata),
        .axi4_slave_wready (axil_ifc.wready),
        .axi4_slave_wvalid (axil_ifc.wvalid),

        // jtag ifc
        .jtag_tck   (  /*unused*/),
        .jtag_tdi   (  /*unused*/),
        .jtag_tdo   (  /*unused*/),
        .jtag_tms   (  /*unused*/),
        .jtag_trst_n(  /*unused*/),

        // matrix unit ifc
        .mu2cgra_valid (1'b1),
        .cgra2mu_ready (),
        .mu2cgra(mu2cgra)
    );


endmodule
