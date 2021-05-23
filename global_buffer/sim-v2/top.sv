/*=============================================================================
** Module: top.sv
** Description:
**              simple top testbench for glb
** Author: Taeyoung Kong
** Change history:  05/22/2021 - Implement first version of testbench
**===========================================================================*/
`define CLK_PERIOD 1200ps

import global_buffer_pkg::*;
import global_buffer_param::*;

module top;
timeunit 1ps;
timeprecision 1ps;

`ifdef PWR
    supply1 VDD;
    supply0 VSS;
`endif

    logic                     clk;
    logic [NUM_GLB_TILES-1:0] stall;
    logic [NUM_GLB_TILES-1:0] cgra_stall_in;
    logic                     reset;
    logic                     cgra_soft_reset;

    // cgra configuration from global controller
    logic                           cgra_cfg_jtag_gc2glb_wr_en;
    logic                           cgra_cfg_jtag_gc2glb_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0] cgra_cfg_jtag_gc2glb_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_jtag_gc2glb_data;

    // control pulse
    logic [NUM_GLB_TILES-1:0] strm_start_pulse;
    logic [NUM_GLB_TILES-1:0] pc_start_pulse;
    logic [NUM_GLB_TILES-1:0] strm_f2g_interrupt_pulse;
    logic [NUM_GLB_TILES-1:0] strm_g2f_interrupt_pulse;
    logic [NUM_GLB_TILES-1:0] pcfg_g2f_interrupt_pulse;

    // Processor
    logic                         proc_wr_en;
    logic [BANK_DATA_WIDTH/8-1:0] proc_wr_strb;
    logic [GLB_ADDR_WIDTH-1:0]    proc_wr_addr;
    logic [BANK_DATA_WIDTH-1:0]   proc_wr_data;
    logic                         proc_rd_en;
    logic [GLB_ADDR_WIDTH-1:0]    proc_rd_addr;
    logic [BANK_DATA_WIDTH-1:0]   proc_rd_data;
    logic                         proc_rd_data_valid;

    // configuration of glb from glc
    logic                      if_cfg_wr_en;
    logic                      if_cfg_wr_clk_en;
    logic [AXI_ADDR_WIDTH-1:0] if_cfg_wr_addr;
    logic [AXI_DATA_WIDTH-1:0] if_cfg_wr_data;
    logic                      if_cfg_rd_en;
    logic                      if_cfg_rd_clk_en;
    logic [AXI_ADDR_WIDTH-1:0] if_cfg_rd_addr;
    logic [AXI_DATA_WIDTH-1:0] if_cfg_rd_data;
    logic                      if_cfg_rd_data_valid;

    // configuration of sram from glc
    logic                      if_sram_cfg_wr_en;
    logic                      if_sram_cfg_wr_clk_en;
    logic [GLB_ADDR_WIDTH-1:0] if_sram_cfg_wr_addr;
    logic [AXI_DATA_WIDTH-1:0] if_sram_cfg_wr_data;
    logic                      if_sram_cfg_rd_en;
    logic                      if_sram_cfg_rd_clk_en;
    logic [GLB_ADDR_WIDTH-1:0] if_sram_cfg_rd_addr;
    logic [AXI_DATA_WIDTH-1:0] if_sram_cfg_rd_data;
    logic                      if_sram_cfg_rd_data_valid;

    // BOTTOM
    // stall
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_stall;

    // cgra to glb streaming word
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0]     stream_data_f2g;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          stream_data_valid_f2g;

    // glb to cgra streaming word
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0]     stream_data_g2f;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          stream_data_valid_g2f;

    // cgra configuration to cgra
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_cfg_g2f_cfg_wr_en;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_cfg_g2f_cfg_rd_en;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_ADDR_WIDTH-1:0] cgra_cfg_g2f_cfg_addr;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_g2f_cfg_data;

    // max cycle set
    initial begin
        repeat(10000000) @(posedge clk);
        $display("\n%0t\tERROR: The 10000000 cycles marker has passed!", $time);
        $finish(2);
    end

    // back-annotation and dump
`ifdef SYNTHESIS
    initial begin
        if ($test$plusargs("VCD_ON")) begin
            $dumpfile("glb_syn.vcd");
            $dumpvars(0, top);
        end
    end
`elsif PNR 
    initial begin
        if ($test$plusargs("VCD_ON")) begin
            $dumpfile("glb_pnr.vcd");
            $dumpvars(0, top);
        end
    end
`else
    initial begin
        if ($test$plusargs("VCD_ON")) begin
            $dumpfile("glb.vcd");
            $dumpvars(0, top);
        end
    end
`endif

    // clk generation
    initial begin
        #0.5ns
        clk = 0;
        forever
        #(`CLK_PERIOD/2.0) clk = !clk;
    end

    // reset generation
    initial begin
        reset <= 1;
        repeat(10) @(posedge clk);
        reset <= 0;
    end


    // instantiate test
    glb_test test (
        .clk(clk),
        .reset(reset),
        // proc ifc
        .proc_wr_en                 ( proc_wr_en         ),
        .proc_wr_strb               ( proc_wr_strb       ),
        .proc_wr_addr               ( proc_wr_addr       ),
        .proc_wr_data               ( proc_wr_data       ),
        .proc_rd_en                 ( proc_rd_en         ),
        .proc_rd_addr               ( proc_rd_addr       ),
        .proc_rd_data               ( proc_rd_data       ),
        .proc_rd_data_valid         ( proc_rd_data_valid ),
        // config ifc
        .if_cfg_wr_en               ( if_cfg_wr_en         ),
        .if_cfg_wr_clk_en           ( if_cfg_wr_clk_en     ),
        .if_cfg_wr_addr             ( if_cfg_wr_addr       ),
        .if_cfg_wr_data             ( if_cfg_wr_data       ),
        .if_cfg_rd_en               ( if_cfg_rd_en         ),
        .if_cfg_rd_clk_en           ( if_cfg_rd_clk_en     ),
        .if_cfg_rd_addr             ( if_cfg_rd_addr       ),
        .if_cfg_rd_data             ( if_cfg_rd_data       ),
        .if_cfg_rd_data_valid       ( if_cfg_rd_data_valid ),
        // sram config ifc
        .if_sram_cfg_wr_en          ( if_sram_cfg_wr_en         ),
        .if_sram_cfg_wr_clk_en      ( if_sram_cfg_wr_clk_en     ),
        .if_sram_cfg_wr_addr        ( if_sram_cfg_wr_addr       ),
        .if_sram_cfg_wr_data        ( if_sram_cfg_wr_data       ),
        .if_sram_cfg_rd_en          ( if_sram_cfg_rd_en         ),
        .if_sram_cfg_rd_clk_en      ( if_sram_cfg_rd_clk_en     ),
        .if_sram_cfg_rd_addr        ( if_sram_cfg_rd_addr       ),
        .if_sram_cfg_rd_data        ( if_sram_cfg_rd_data       ),
        .if_sram_cfg_rd_data_valid  ( if_sram_cfg_rd_data_valid ),
        .* );

    // instantiate dut
    global_buffer dut (
        // proc ifc
        .proc_wr_en                 ( proc_wr_en         ),
        .proc_wr_strb               ( proc_wr_strb       ),
        .proc_wr_addr               ( proc_wr_addr       ),
        .proc_wr_data               ( proc_wr_data       ),
        .proc_rd_en                 ( proc_rd_en         ),
        .proc_rd_addr               ( proc_rd_addr       ),
        .proc_rd_data               ( proc_rd_data       ),
        .proc_rd_data_valid         ( proc_rd_data_valid ),
        // config ifc
        .if_cfg_wr_en               ( if_cfg_wr_en         ),
        .if_cfg_wr_clk_en           ( if_cfg_wr_clk_en     ),
        .if_cfg_wr_addr             ( if_cfg_wr_addr       ),
        .if_cfg_wr_data             ( if_cfg_wr_data       ),
        .if_cfg_rd_en               ( if_cfg_rd_en         ),
        .if_cfg_rd_clk_en           ( if_cfg_rd_clk_en     ),
        .if_cfg_rd_addr             ( if_cfg_rd_addr       ),
        .if_cfg_rd_data             ( if_cfg_rd_data       ),
        .if_cfg_rd_data_valid       ( if_cfg_rd_data_valid ),
        // sram config ifc
        .if_sram_cfg_wr_en          ( if_sram_cfg_wr_en         ),
        .if_sram_cfg_wr_clk_en      ( if_sram_cfg_wr_clk_en     ),
        .if_sram_cfg_wr_addr        ( if_sram_cfg_wr_addr       ),
        .if_sram_cfg_wr_data        ( if_sram_cfg_wr_data       ),
        .if_sram_cfg_rd_en          ( if_sram_cfg_rd_en         ),
        .if_sram_cfg_rd_clk_en      ( if_sram_cfg_rd_clk_en     ),
        .if_sram_cfg_rd_addr        ( if_sram_cfg_rd_addr       ),
        .if_sram_cfg_rd_data        ( if_sram_cfg_rd_data       ),
        .if_sram_cfg_rd_data_valid  ( if_sram_cfg_rd_data_valid ),
`ifdef PWR
        .VDD (VDD),
        .VSS (VSS),
`endif
        .* );

endmodule
