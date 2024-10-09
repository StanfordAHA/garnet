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


    realtime curr_time;

    // reset generation
    initial begin
        reset <= 1;
        repeat (3) @(posedge clk);
        curr_time = $realtime;
	     $display("reset released at %0t", curr_time);
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

    //============================================================================//
    // instantiate dut
    //============================================================================//

   supply1 VDD;
   supply0 VSS;

    GarnetSOC_pad_frame_Garnet dut (
    //Garnet dut (
        // clk/reset/interrupt
        .clk_in              (clk),
        //.reset_in            (~reset),
        .reset_in            (reset),
        .interrupt           (interrupt),
        .cgra_running_clk_out(  /*unused*/),
    //     .clk_in_clone1	     (clk),
	// .clk_in_clone2	     (clk),
    //     .FE_OFN1440_cgra_reset_n (~reset),
    //     .FE_OFN1397_cgra_reset_n (~reset),
    //     .FE_OFN1353_cgra_reset_n (reset),
    //     .FE_OFN1308_cgra_reset_n (~reset),
    //     .FE_OFN1287_cgra_reset_n (~reset),
    //     .FE_OFN1283_cgra_reset_n (~reset),
    //     .FE_OFN1277_cgra_reset_n (~reset),
    //     .FE_OFN3878_n (reset),
	// .FE_OFN3884_n (~reset),
    //     .p1           (~reset),

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

        //jtag ifc
        .jtag_tck   (  /*unused*/),
        .jtag_tdi   (  /*unused*/),
        .jtag_tdo   (  /*unused*/),
        .jtag_tms   (  /*unused*/),
        .jtag_trst_n(  /*unused*/)

	
        // .jtag_tck   (  1'b0 ),
        // .jtag_tdi   (  1'b0 ),
        // .jtag_tdo   (  1'b0 ),
        // .jtag_tms   (  1'b0 ),
        // .jtag_trst_n(  1'b0 )

        // Supplies
        // .VDD(VDD),
        // .VSS(VSS)


    );


endmodule
