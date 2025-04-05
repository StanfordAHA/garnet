/*=============================================================================
** Module: top_glb_mu.sv
** Description:
**              top for glb mu testbench
** Author:  Michael Oduoza
** Change history:
**  03/13/2025 - Michael Oduoza: Implement the first version
**==============================================================================*/



`define DBG_TBTOP 0 // Set to '1' for debugging


`define MY_CLK_PERIOD 1ns

import global_buffer_param::*;
// import matrix_unit_param::*;

module top;
    // FIXME every other module assumes timescale == 1ps/1ps
    // FIXME this one should do the same !!!
    // (Also see time_check function in garnet_test.sv)
    timeunit 1ns; timeprecision 1ps;

    logic clk;
    logic reset;

    //============================================================================//
    // clk / reset generation
    //============================================================================//
    // clk generation
    initial begin
        clk = 0;
        forever #(`MY_CLK_PERIOD / 2.0) clk = !clk;
    end

    // Print a debug message every once in awhile
    initial begin
         $display("[%0t] Model running...\n", $time);
         $display("[%0t]", $time);
         forever #(`MY_CLK_PERIOD * 1000) $display("[%0t]", $time);
    end

    // max cycle set
    initial begin
        repeat (1000000) @(posedge clk);
        $display("\n%0t\tERROR: The 1000000 cycles marker has passed!", $time);
        $finish(2);
    end


     `ifdef verilator
        // Dump out the wave info
        // FIXME think about moving this to verilator top-level CGRA.cpp or whatever
        initial begin
            if ($test$plusargs("trace") != 0) begin
                $display("[%0t] Tracing to logs/vlt_dump.vcd...\n", $time);
                $dumpfile("logs/vlt_dump.vcd");
                $dumpvars();
            end
        end
    `endif

    // reset generation
    initial begin
        // Change reset to give a clear up-and-down pulse
        reset = 0; if (`DBG_TBTOP) $display("[%0t] reset = 0", $time);
        repeat (3) @(posedge clk);
        reset = 1; if (`DBG_TBTOP) $display("[%0t] reset = 1", $time);
        repeat (3) @(posedge clk);
        reset = 0; if (`DBG_TBTOP) $display("[%0t] reset = 0\n", $time);
    end

    //============================================================================//
    // Proc interface 
    //============================================================================//
    proc_ifc p_ifc (.clk(clk));


    //============================================================================//
    // GLB-MU interface 
    //============================================================================//
    glb_mu_ifc glb_mu_ifc (.clk(clk));


    //============================================================================//
    // instantiate test
    //============================================================================//
    glb_mu_test test (
        .clk     (clk),
        .reset   (reset),
        .p_ifc   (p_ifc),
        .glb_mu_ifc (glb_mu_ifc)
    );


    //============================================================================//
    // instantiate dut: with E64 signals 
    //============================================================================//
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0] strm_ctrl_f2g;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][3:0][CGRA_DATA_WIDTH-1:0] strm_data_f2g;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][3:0] strm_data_f2g_vld;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][3:0]  strm_data_g2f_rdy;
    logic [NUM_GLB_TILES-1:0] pcfg_broadcast_stall;


    logic [NUM_GLB_TILES-1:0] strm_f2g_start_pulse;
    logic [NUM_GLB_TILES-1:0] strm_g2f_start_pulse;
    logic [2*NUM_GLB_TILES-1:0] cgra_stall_in;
    logic [NUM_GLB_TILES-1:0] glb_clk_en_bank_master;
    logic [NUM_GLB_TILES-1:0] glb_clk_en_master;
    logic [NUM_GLB_TILES-1:0] pcfg_start_pulse;
    logic [2*NUM_GLB_TILES-1:0] flush_crossbar_sel;

    logic [GLB_ADDR_WIDTH-1:0] if_sram_cfg_rd_addr;
    logic [GLB_ADDR_WIDTH-1:0] if_sram_cfg_wr_addr;


    initial begin
        for (int i = 0; i < NUM_GLB_TILES; i++) begin     
            pcfg_broadcast_stall[i] = 1'b1;
            strm_f2g_start_pulse[i] = 1'b0;
            strm_g2f_start_pulse[i] = 1'b0;
            cgra_stall_in[2*i] = 1'b0;
            cgra_stall_in[2*i+1] = 1'b0;
            glb_clk_en_bank_master[i] = 1'b0;
            glb_clk_en_master[i] = 1'b0;
            pcfg_start_pulse[i] = 1'b0;
            flush_crossbar_sel[2*i] = 1'b0;
            flush_crossbar_sel[2*i+1] = 1'b0;
            for (int j = 0; j < CGRA_PER_GLB; j++) begin
                strm_ctrl_f2g[i][j] = 1'b0;
                for (int e64_packet = 0; e64_packet < 4; e64_packet++) begin
                    strm_data_f2g[i][j][e64_packet] = 16'b0;
                    strm_data_g2f_rdy[i][j][e64_packet] = 1'b0;
                    strm_data_f2g_vld[i][j][e64_packet] = 1'b0;
                end
            end
        end
    end


    initial begin
        for (int i = 0; i < GLB_ADDR_WIDTH; i++) begin
            if_sram_cfg_rd_addr[i] = 1'b0;
            if_sram_cfg_wr_addr[i] = 1'b0;
        end
    end


    global_buffer dut (
        .clk                      (clk),
        .reset                    (reset),

        // proc ifc
        .proc_wr_en               (p_ifc.wr_en),
        .proc_wr_strb             (p_ifc.wr_strb),
        .proc_wr_addr             (p_ifc.wr_addr),
        .proc_wr_data             (p_ifc.wr_data),
        .proc_rd_en               (p_ifc.rd_en),
        .proc_rd_addr             (p_ifc.rd_addr),
        .proc_rd_data             (p_ifc.rd_data),
        .proc_rd_data_valid       (p_ifc.rd_data_valid),

        // config ifc
        .if_cfg_wr_en             (1'b0),
        .if_cfg_wr_clk_en         (1'b0),
        .if_cfg_wr_addr           (12'b0),
        .if_cfg_wr_data           (32'b0),
        .if_cfg_rd_en             (1'b0),
        .if_cfg_rd_clk_en         (1'b0),
        .if_cfg_rd_addr           (12'b0),
        .if_cfg_rd_data           (),
        .if_cfg_rd_data_valid     (),
        // sram config ifc
        .if_sram_cfg_wr_en        (1'b0),
        .if_sram_cfg_wr_addr      (if_sram_cfg_wr_addr),
        .if_sram_cfg_wr_data      (32'b0),
        .if_sram_cfg_rd_en        (1'b0),
        .if_sram_cfg_rd_addr      (if_sram_cfg_rd_addr),
        .if_sram_cfg_rd_data      (),
        .if_sram_cfg_rd_data_valid(),

        // cgra-glb
        .strm_ctrl_f2g    (strm_ctrl_f2g),
        .strm_data_f2g    (strm_data_f2g),
        .strm_data_f2g_vld(strm_data_f2g_vld),
        .strm_data_f2g_rdy(),
        .strm_ctrl_g2f    (),
        .strm_data_g2f    (),
        .strm_data_g2f_vld(),
        .strm_data_g2f_rdy(strm_data_g2f_rdy),
        .strm_f2g_start_pulse(strm_f2g_start_pulse),
        .strm_g2f_start_pulse(strm_g2f_start_pulse),

        .strm_data_flush_g2f(),
        .flush_crossbar_sel(flush_crossbar_sel),


        // jtag
        .cgra_cfg_jtag_gc2glb_addr(32'b0),
        .cgra_cfg_jtag_gc2glb_data(32'b0),
        .cgra_cfg_jtag_gc2glb_rd_en(1'b0),
        .cgra_cfg_jtag_gc2glb_wr_en(1'b0),


        // other
        .cgra_stall_in(cgra_stall_in),
        .glb_clk_en_bank_master(glb_clk_en_bank_master),
        .glb_clk_en_master(glb_clk_en_master),
        .pcfg_broadcast_stall(pcfg_broadcast_stall),
        .pcfg_start_pulse(pcfg_start_pulse),
        .cgra_cfg_g2f_cfg_addr(),
        .cgra_cfg_g2f_cfg_data(),
        .cgra_cfg_g2f_cfg_rd_en(),
        .cgra_cfg_g2f_cfg_wr_en(),
        .cgra_stall(),
        .pcfg_g2f_interrupt_pulse(),
        .strm_f2g_interrupt_pulse(),
        .strm_g2f_interrupt_pulse(),


        // matrix unit ifc
        .mu_tl_addr_in (glb_mu_ifc.mu_tl_addr_in),
        .mu_tl_in_vld (glb_mu_ifc.mu_tl_in_vld),
        .mu_tl_in_rdy (glb_mu_ifc.mu_tl_in_rdy),
        .mu_tl_size_in (glb_mu_ifc.mu_tl_size_in),
        .mu_tl_data_out (glb_mu_ifc.mu_rd_data),
        .mu_tl_data_out_vld (glb_mu_ifc.mu_rd_data_valid),
        .mu_tl_data_out_rdy (glb_mu_ifc.mu_rd_data_ready)
    `ifdef PWR
            .VDD(VDD),
            .VSS(VSS),
    `endif
            // .*
    );


endmodule
