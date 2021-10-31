/*=============================================================================
** Module: top.sv
** Description:
**              top testbench for glb_tile
** Author: Taeyoung Kong
** Change history:  04/03/2020 - Implement first version of testbench
**===========================================================================*/
`define CLK_PERIOD 1000ps
`define GLB_TILE_ID 0

import global_buffer_param::*;

module top;
timeunit 100ps;
timeprecision 1ps;

`ifdef PWR
    supply1 VDD;
    supply0 VSS;
`endif

    logic                                                clk;
    logic                                                clk_en;
    logic                                                reset;
    logic [TILE_SEL_ADDR_WIDTH-1:0]                      glb_tile_id;

    // LEFT/RIGHT
    // processor packet
    logic                                                proc_wr_en_e2w_esti;
    logic [BANK_DATA_WIDTH/8-1:0]                        proc_wr_strb_e2w_esti;
    logic [GLB_ADDR_WIDTH-1:0]                           proc_wr_addr_e2w_esti;
    logic [BANK_DATA_WIDTH-1:0]                          proc_wr_data_e2w_esti;
    logic                                                proc_rd_en_e2w_esti;
    logic [GLB_ADDR_WIDTH-1:0]                           proc_rd_addr_e2w_esti;
    logic [BANK_DATA_WIDTH-1:0]                          proc_rd_data_e2w_esti;
    logic                                                proc_rd_data_valid_e2w_esti;

    logic                                                proc_wr_en_w2e_esto;
    logic [BANK_DATA_WIDTH/8-1:0]                        proc_wr_strb_w2e_esto;
    logic [GLB_ADDR_WIDTH-1:0]                           proc_wr_addr_w2e_esto;
    logic [BANK_DATA_WIDTH-1:0]                          proc_wr_data_w2e_esto;
    logic                                                proc_rd_en_w2e_esto;
    logic [GLB_ADDR_WIDTH-1:0]                           proc_rd_addr_w2e_esto;
    logic [BANK_DATA_WIDTH-1:0]                          proc_rd_data_w2e_esto;
    logic                                                proc_rd_data_valid_w2e_esto;

    logic                                                proc_wr_en_w2e_wsti;
    logic [BANK_DATA_WIDTH/8-1:0]                        proc_wr_strb_w2e_wsti;
    logic [GLB_ADDR_WIDTH-1:0]                           proc_wr_addr_w2e_wsti;
    logic [BANK_DATA_WIDTH-1:0]                          proc_wr_data_w2e_wsti;
    logic                                                proc_rd_en_w2e_wsti;
    logic [GLB_ADDR_WIDTH-1:0]                           proc_rd_addr_w2e_wsti;
    logic [BANK_DATA_WIDTH-1:0]                          proc_rd_data_w2e_wsti;
    logic                                                proc_rd_data_valid_w2e_wsti;

    logic                                                proc_wr_en_e2w_wsto;
    logic [BANK_DATA_WIDTH/8-1:0]                        proc_wr_strb_e2w_wsto;
    logic [GLB_ADDR_WIDTH-1:0]                           proc_wr_addr_e2w_wsto;
    logic [BANK_DATA_WIDTH-1:0]                          proc_wr_data_e2w_wsto;
    logic                                                proc_rd_en_e2w_wsto;
    logic [GLB_ADDR_WIDTH-1:0]                           proc_rd_addr_e2w_wsto;
    logic [BANK_DATA_WIDTH-1:0]                          proc_rd_data_e2w_wsto;
    logic                                                proc_rd_data_valid_e2w_wsto;

    // stream packet
    logic                                                strm_wr_en_e2w_esti;
    logic [BANK_DATA_WIDTH/8-1:0]                        strm_wr_strb_e2w_esti;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_wr_addr_e2w_esti;
    logic [BANK_DATA_WIDTH-1:0]                          strm_wr_data_e2w_esti;
    logic                                                strm_rd_en_e2w_esti;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_rd_addr_e2w_esti;
    logic [BANK_DATA_WIDTH-1:0]                          strm_rd_data_e2w_esti;
    logic                                                strm_rd_data_valid_e2w_esti;

    logic                                                strm_wr_en_w2e_esto;
    logic [BANK_DATA_WIDTH/8-1:0]                        strm_wr_strb_w2e_esto;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_wr_addr_w2e_esto;
    logic [BANK_DATA_WIDTH-1:0]                          strm_wr_data_w2e_esto;
    logic                                                strm_rd_en_w2e_esto;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_rd_addr_w2e_esto;
    logic [BANK_DATA_WIDTH-1:0]                          strm_rd_data_w2e_esto;
    logic                                                strm_rd_data_valid_w2e_esto;

    logic                                                strm_wr_en_w2e_wsti;
    logic [BANK_DATA_WIDTH/8-1:0]                        strm_wr_strb_w2e_wsti;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_wr_addr_w2e_wsti;
    logic [BANK_DATA_WIDTH-1:0]                          strm_wr_data_w2e_wsti;
    logic                                                strm_rd_en_w2e_wsti;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_rd_addr_w2e_wsti;
    logic [BANK_DATA_WIDTH-1:0]                          strm_rd_data_w2e_wsti;
    logic                                                strm_rd_data_valid_w2e_wsti;

    logic                                                strm_wr_en_e2w_wsto;
    logic [BANK_DATA_WIDTH/8-1:0]                        strm_wr_strb_e2w_wsto;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_wr_addr_e2w_wsto;
    logic [BANK_DATA_WIDTH-1:0]                          strm_wr_data_e2w_wsto;
    logic                                                strm_rd_en_e2w_wsto;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_rd_addr_e2w_wsto;
    logic [BANK_DATA_WIDTH-1:0]                          strm_rd_data_e2w_wsto;
    logic                                                strm_rd_data_valid_e2w_wsto;

    logic                                                pcfg_rd_en_e2w_esti;
    logic [GLB_ADDR_WIDTH-1:0]                           pcfg_rd_addr_e2w_esti;
    logic [BANK_DATA_WIDTH-1:0]                          pcfg_rd_data_e2w_esti;
    logic                                                pcfg_rd_data_valid_e2w_esti;

    logic                                                pcfg_rd_en_w2e_esto;
    logic [GLB_ADDR_WIDTH-1:0]                           pcfg_rd_addr_w2e_esto;
    logic [BANK_DATA_WIDTH-1:0]                          pcfg_rd_data_w2e_esto;
    logic                                                pcfg_rd_data_valid_w2e_esto;

    logic                                                pcfg_rd_en_w2e_wsti;
    logic [GLB_ADDR_WIDTH-1:0]                           pcfg_rd_addr_w2e_wsti;
    logic [BANK_DATA_WIDTH-1:0]                          pcfg_rd_data_w2e_wsti;
    logic                                                pcfg_rd_data_valid_w2e_wsti;

    logic                                                pcfg_rd_en_e2w_wsto;
    logic [GLB_ADDR_WIDTH-1:0]                           pcfg_rd_addr_e2w_wsto;
    logic [BANK_DATA_WIDTH-1:0]                          pcfg_rd_data_e2w_wsto;
    logic                                                pcfg_rd_data_valid_e2w_wsto;

    // Config
    logic                                                if_cfg_est_m_wr_en;
    logic                                                if_cfg_est_m_wr_clk_en;
    logic [AXI_ADDR_WIDTH-1:0]                           if_cfg_est_m_wr_addr;
    logic [AXI_DATA_WIDTH-1:0]                           if_cfg_est_m_wr_data;
    logic                                                if_cfg_est_m_rd_en;
    logic                                                if_cfg_est_m_rd_clk_en;
    logic [AXI_ADDR_WIDTH-1:0]                           if_cfg_est_m_rd_addr;
    logic [AXI_DATA_WIDTH-1:0]                           if_cfg_est_m_rd_data;
    logic                                                if_cfg_est_m_rd_data_valid;

    logic                                                if_cfg_wst_s_wr_en;
    logic                                                if_cfg_wst_s_wr_clk_en;
    logic [AXI_ADDR_WIDTH-1:0]                           if_cfg_wst_s_wr_addr;
    logic [AXI_DATA_WIDTH-1:0]                           if_cfg_wst_s_wr_data;
    logic                                                if_cfg_wst_s_rd_en;
    logic                                                if_cfg_wst_s_rd_clk_en;
    logic [AXI_ADDR_WIDTH-1:0]                           if_cfg_wst_s_rd_addr;
    logic [AXI_DATA_WIDTH-1:0]                           if_cfg_wst_s_rd_data;
    logic                                                if_cfg_wst_s_rd_data_valid;

    // SRAM Config
    logic                                                if_sram_cfg_est_m_wr_en;
    logic                                                if_sram_cfg_est_m_wr_clk_en;
    logic [GLB_ADDR_WIDTH-1:0]                           if_sram_cfg_est_m_wr_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      if_sram_cfg_est_m_wr_data;
    logic                                                if_sram_cfg_est_m_rd_en;
    logic                                                if_sram_cfg_est_m_rd_clk_en;
    logic [GLB_ADDR_WIDTH-1:0]                           if_sram_cfg_est_m_rd_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      if_sram_cfg_est_m_rd_data;
    logic                                                if_sram_cfg_est_m_rd_data_valid;

    logic                                                if_sram_cfg_wst_s_wr_en;
    logic                                                if_sram_cfg_wst_s_wr_clk_en;
    logic [GLB_ADDR_WIDTH-1:0]                           if_sram_cfg_wst_s_wr_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      if_sram_cfg_wst_s_wr_data;
    logic                                                if_sram_cfg_wst_s_rd_en;
    logic                                                if_sram_cfg_wst_s_rd_clk_en;
    logic [GLB_ADDR_WIDTH-1:0]                           if_sram_cfg_wst_s_rd_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      if_sram_cfg_wst_s_rd_data;
    logic                                                if_sram_cfg_wst_s_rd_data_valid;

    // configuration registers which should be connected
    logic                                                cfg_tile_connected_wsti;
    logic                                                cfg_tile_connected_esto;
    logic                                                cfg_pcfg_tile_connected_wsti;
    logic                                                cfg_pcfg_tile_connected_esto;

    // parallel configuration
    logic                                                cgra_cfg_jtag_wsti_wr_en;
    logic                                                cgra_cfg_jtag_wsti_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0]                      cgra_cfg_jtag_wsti_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      cgra_cfg_jtag_wsti_data;

    logic                                                cgra_cfg_jtag_esto_wr_en;
    logic                                                cgra_cfg_jtag_esto_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0]                      cgra_cfg_jtag_esto_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      cgra_cfg_jtag_esto_data;

    // cgra_cfg_jtag_addr bypass
    logic                                                cgra_cfg_jtag_wsti_rd_en_bypass;
    logic [CGRA_CFG_ADDR_WIDTH-1:0]                      cgra_cfg_jtag_wsti_addr_bypass;
    logic                                                cgra_cfg_jtag_esto_rd_en_bypass;
    logic [CGRA_CFG_ADDR_WIDTH-1:0]                      cgra_cfg_jtag_esto_addr_bypass;

    logic                                                cgra_cfg_pcfg_wsti_wr_en;
    logic                                                cgra_cfg_pcfg_wsti_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0]                      cgra_cfg_pcfg_wsti_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      cgra_cfg_pcfg_wsti_data;

    logic                                                cgra_cfg_pcfg_esto_wr_en;
    logic                                                cgra_cfg_pcfg_esto_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0]                      cgra_cfg_pcfg_esto_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      cgra_cfg_pcfg_esto_data;

    // BOTTOM
    // stream data
    logic [CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0]        stream_data_f2g;
    logic [CGRA_PER_GLB-1:0][0:0]                        stream_data_valid_f2g;
    logic [CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0]        stream_data_g2f;
    logic [CGRA_PER_GLB-1:0][0:0]                        stream_data_valid_g2f;

    logic [CGRA_PER_GLB-1:0]                             cgra_cfg_g2f_cfg_wr_en;
    logic [CGRA_PER_GLB-1:0]                             cgra_cfg_g2f_cfg_rd_en;
    logic [CGRA_PER_GLB-1:0][CGRA_CFG_ADDR_WIDTH-1:0]    cgra_cfg_g2f_cfg_addr;
    logic [CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0]    cgra_cfg_g2f_cfg_data;

    // trigger
    logic                                                strm_start_pulse;
    logic                                                pcfg_start_pulse;
    logic                                                strm_f2g_interrupt_pulse;
    logic                                                strm_g2f_interrupt_pulse;
    logic                                                pcfg_g2f_interrupt_pulse;

    // set tile id
    initial begin
        glb_tile_id = `GLB_TILE_ID;
    end

    // we do not use chaining
    initial begin
        cfg_tile_connected_wsti = 0;
        cfg_pcfg_tile_connected_wsti = 0;
    end

    initial begin
        static int max_cycle = 10000000;
        repeat(max_cycle) @(posedge clk);
        $display("\n%0t\tERROR: The %7d cycles marker has passed!", $time, max_cycle);
        $finish(2);
    end

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
    glb_tile_test test(
        .*
    );

    // instantiate dut
    glb_tile dut (
`ifdef PWR
        .VDD (VDD),
        .VSS (VSS),
`endif
        .*);

endmodule
