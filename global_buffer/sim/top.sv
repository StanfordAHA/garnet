/*=============================================================================
** Module: top.sv
** Description:
**              new testbench for global buffer
** Author: Taeyoung Kong
** Change history:
**  09/19/2020 - Implement first version of uvm-style testbench
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

    logic                           clk;
    logic [NUM_GLB_TILES-1:0]       stall;
    logic [NUM_GLB_TILES-1:0]       cgra_stall_in;
    logic                           reset;
    logic                           cgra_soft_reset;

    // cgra configuration from global controller
    logic                           cgra_cfg_jtag_gc2glb_wr_en;
    logic                           cgra_cfg_jtag_gc2glb_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0] cgra_cfg_jtag_gc2glb_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_jtag_gc2glb_data;

    // control pulse
    logic [NUM_GLB_TILES-1:0]       strm_start_pulse;
    logic [NUM_GLB_TILES-1:0]       pc_start_pulse;
    logic [NUM_GLB_TILES-1:0]       strm_f2g_interrupt_pulse;
    logic [NUM_GLB_TILES-1:0]       strm_g2f_interrupt_pulse;
    logic [NUM_GLB_TILES-1:0]       pcfg_g2f_interrupt_pulse;

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

    // for jtag simulation
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_f2g_rd_data;
    logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_cfg_f2g_rd_data_valid;

    logic [CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_rd_data;
    logic                           cgra_cfg_rd_data_valid;

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

    // reset and stall generation
    initial begin
        reset <= 1;
        stall <= '0;
        cgra_stall_in <= '0;
        cgra_cfg_jtag_gc2glb_wr_en <= 0;
        cgra_cfg_jtag_gc2glb_rd_en <= 0;
        cgra_cfg_jtag_gc2glb_addr <= 0;
        cgra_cfg_jtag_gc2glb_data <= 0;
        for(int i=0; i<NUM_GLB_TILES; i++) begin
            pc_start_pulse[i] <= 0;
        end

        repeat(10) @(posedge clk);
        reset <= 0;
    end

    // interfaces
    proc_ifc p_ifc(.clk(clk));
    reg_ifc #(.ADDR_WIDTH(32), .DATA_WIDTH(AXI_DATA_WIDTH))  r_ifc(.clk(clk));
    reg_ifc #(.ADDR_WIDTH(32), .DATA_WIDTH(AXI_DATA_WIDTH))  m_ifc(.clk(clk));
    strm_ifc s_ifc[NUM_GLB_TILES](.clk(clk));
    pcfg_ifc c_ifc[NUM_GLB_TILES](.clk(clk));

    // instantiate test
    glb_test test (
        .clk(clk),
        .reset(reset),
        .p_ifc(p_ifc),
        .r_ifc(r_ifc),
        .m_ifc(m_ifc),
        .s_ifc(s_ifc),
        .c_ifc(c_ifc)
    );

    genvar i;
    generate
        for(i=0; i<NUM_GLB_TILES; i++) begin
            // strm
            assign strm_start_pulse[i]          = s_ifc[i].strm_start_pulse;
            assign stream_data_f2g[i]           = s_ifc[i].data_f2g;
            assign stream_data_valid_f2g[i]     = s_ifc[i].data_valid_f2g;
            assign s_ifc[i].data_g2f            = stream_data_g2f[i];
            assign s_ifc[i].data_valid_g2f      = stream_data_valid_g2f[i];
            assign s_ifc[i].strm_f2g_interrupt  = strm_f2g_interrupt_pulse[i];
            assign s_ifc[i].strm_g2f_interrupt  = strm_g2f_interrupt_pulse[i];

            //pcfg
            assign c_ifc[i].cgra_cfg_wr_en      = cgra_cfg_g2f_cfg_wr_en[i];
            assign c_ifc[i].cgra_cfg_rd_en      = cgra_cfg_g2f_cfg_rd_en[i];
            assign c_ifc[i].cgra_cfg_addr       = cgra_cfg_g2f_cfg_addr[i];
            assign c_ifc[i].cgra_cfg_data       = cgra_cfg_g2f_cfg_data[i];
        end
    endgenerate


    // instantiate dut
    global_buffer dut (
        // proc ifc
        .proc_wr_en                 ( p_ifc.wr_en           ),
        .proc_wr_strb               ( p_ifc.wr_strb         ),
        .proc_wr_addr               ( p_ifc.wr_addr         ),
        .proc_wr_data               ( p_ifc.wr_data         ),
        .proc_rd_en                 ( p_ifc.rd_en           ),
        .proc_rd_addr               ( p_ifc.rd_addr         ),
        .proc_rd_data               ( p_ifc.rd_data         ),
        .proc_rd_data_valid         ( p_ifc.rd_data_valid   ),
        // config ifc
        .if_cfg_wr_en               ( r_ifc.wr_en           ),
        .if_cfg_wr_clk_en           ( r_ifc.wr_clk_en       ),
        .if_cfg_wr_addr             ( r_ifc.wr_addr[AXI_ADDR_WIDTH-1:0] ),
        .if_cfg_wr_data             ( r_ifc.wr_data         ),
        .if_cfg_rd_en               ( r_ifc.rd_en           ),
        .if_cfg_rd_clk_en           ( r_ifc.rd_clk_en       ),
        .if_cfg_rd_addr             ( r_ifc.rd_addr[AXI_ADDR_WIDTH-1:0] ),
        .if_cfg_rd_data             ( r_ifc.rd_data         ),
        .if_cfg_rd_data_valid       ( r_ifc.rd_data_valid   ),
        // sram config ifc
        .if_sram_cfg_wr_en          ( m_ifc.wr_en           ),
        .if_sram_cfg_wr_clk_en      ( m_ifc.wr_clk_en       ),
        .if_sram_cfg_wr_addr        ( m_ifc.wr_addr[GLB_ADDR_WIDTH-1:0] ),
        .if_sram_cfg_wr_data        ( m_ifc.wr_data         ),
        .if_sram_cfg_rd_en          ( m_ifc.rd_en           ),
        .if_sram_cfg_rd_clk_en      ( m_ifc.rd_clk_en       ),
        .if_sram_cfg_rd_addr        ( m_ifc.rd_addr[GLB_ADDR_WIDTH-1:0] ),
        .if_sram_cfg_rd_data        ( m_ifc.rd_data         ),
        .if_sram_cfg_rd_data_valid  ( m_ifc.rd_data_valid   ),
`ifdef PWR
        .VDD (VDD),
        .VSS (VSS),
`endif
        .*);

        cgra #(
            .NUM_GLB_TILES          ( NUM_GLB_TILES ),
            .NUM_CGRA_TILES         ( NUM_CGRA_TILES ),
            .CGRA_CFG_DATA_WIDTH    ( CGRA_CFG_DATA_WIDTH ),
            .CGRA_PER_GLB           ( CGRA_PER_GLB )
        ) cgra (.*);

    always_comb begin
        cgra_cfg_rd_data_valid = 0;
        cgra_cfg_rd_data = 0;
        for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
            for (int j=0; j<CGRA_PER_GLB; j=j+1) begin
                cgra_cfg_rd_data_valid |= cgra_cfg_f2g_rd_data_valid[i][j];
                cgra_cfg_rd_data |= cgra_cfg_f2g_rd_data[i][j];
            end
        end
    end

endmodule
