/*=============================================================================
** Module: top.sv
** Description:
**              top testbench for global buffer
** Author: Taeyoung Kong
** Change history:  04/03/2020 - Implement first version of testbench
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module top();
    logic                           clk;
    logic                           stall;
    logic                           reset;

    // proc
    logic                           proc_wr_en;
    logic [BANK_DATA_WIDTH/8-1:0]   proc_wr_strb;
    logic [GLB_ADDR_WIDTH-1:0]      proc_wr_addr;
    logic [BANK_DATA_WIDTH-1:0]     proc_wr_data;
    logic                           proc_rd_en;
    logic [GLB_ADDR_WIDTH-1:0]      proc_rd_addr;
    logic [BANK_DATA_WIDTH-1:0]     proc_rd_data;
    logic                           proc_rd_data_valid;

    // configuration of glb from glc
    logic                           if_cfg_wr_en;
    logic                           if_cfg_wr_clk_en;
    logic [AXI_ADDR_WIDTH-1:0]      if_cfg_wr_addr;
    logic [AXI_DATA_WIDTH-1:0]      if_cfg_wr_data;
    logic                           if_cfg_rd_en;
    logic                           if_cfg_rd_clk_en;
    logic [AXI_ADDR_WIDTH-1:0]      if_cfg_rd_addr;
    logic [AXI_DATA_WIDTH-1:0]      if_cfg_rd_data;
    logic                           if_cfg_rd_data_valid;

    // configuration of sram from glc
    logic                           if_sram_cfg_wr_en;
    logic                           if_sram_cfg_wr_clk_en;
    logic [GLB_ADDR_WIDTH-1:0]      if_sram_cfg_wr_addr;
    logic [AXI_DATA_WIDTH-1:0]      if_sram_cfg_wr_data;
    logic                           if_sram_cfg_rd_en;
    logic                           if_sram_cfg_rd_clk_en;
    logic [GLB_ADDR_WIDTH-1:0]      if_sram_cfg_rd_addr;
    logic [AXI_DATA_WIDTH-1:0]      if_sram_cfg_rd_data;
    logic                           if_sram_cfg_rd_data_valid;

    // cgra configuration from global controller
    logic                           cgra_cfg_jtag_gc2glb_wr_en;
    logic                           cgra_cfg_jtag_gc2glb_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0] cgra_cfg_jtag_gc2glb_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_jtag_gc2glb_data;

    // control pulse
    logic [NUM_GLB_TILES-1:0]       strm_start_pulse;
    logic [NUM_GLB_TILES-1:0]       pc_start_pulse;
    logic [3*NUM_GLB_TILES-1:0]     interrupt_pulse;

    // BOTTOM
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

    // stall generation
    initial begin
        stall = 0;
    end

    // clock generation
    clocker clocker_inst (.clk(clk), .reset(reset));

    // processor packet interface
    proc_ifc p_ifc(.clk(clk));

    // Instantiate test
    glb_test test (
        .clk(clk),
        .reset(reset),
        .p_ifc(p_ifc)
    );

    // Instantiate dut
    global_buffer dut (
        .proc_wr_en         ( p_ifc.wr_en           ),
        .proc_wr_strb       ( p_ifc.wr_strb         ),
        .proc_wr_addr       ( p_ifc.wr_addr         ),
        .proc_wr_data       ( p_ifc.wr_data         ),
        .proc_rd_en         ( p_ifc.rd_en           ),
        .proc_rd_addr       ( p_ifc.rd_addr         ),
        .proc_rd_data       ( p_ifc.rd_data         ),
        .proc_rd_data_valid ( p_ifc.rd_data_valid   ),
        .*);

endmodule
