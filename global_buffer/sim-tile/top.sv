/*=============================================================================
** Module: top.sv
** Description:
**              top testbench for glb_tile
** Author: Taeyoung Kong
** Change history:  04/03/2020 - Implement first version of testbench
**===========================================================================*/
`define CLK_PERIOD 1ns

import global_buffer_param::*;

module top;
timeunit 1ps;
timeprecision 1ps;

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
    // packet_sel_t                                         strm_wr_packet_sel_e2w_esti;
    // packet_sel_t                                         strm_rdrq_packet_sel_e2w_esti;
    // packet_sel_t                                         strm_rdrs_packet_sel_e2w_esti;
    logic                                                strm_wr_en_e2w_esti;
    logic [BANK_DATA_WIDTH/8-1:0]                        strm_wr_strb_e2w_esti;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_wr_addr_e2w_esti;
    logic [BANK_DATA_WIDTH-1:0]                          strm_wr_data_e2w_esti;
    logic                                                strm_rd_en_e2w_esti;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_rd_addr_e2w_esti;
    logic [BANK_DATA_WIDTH-1:0]                          strm_rd_data_e2w_esti;
    logic                                                strm_rd_data_valid_e2w_esti;

    // packet_sel_t                                         strm_wr_packet_sel_w2e_esto;
    // packet_sel_t                                         strm_rdrq_packet_sel_w2e_esto;
    // packet_sel_t                                         strm_rdrs_packet_sel_w2e_esto;
    logic                                                strm_wr_en_w2e_esto;
    logic [BANK_DATA_WIDTH/8-1:0]                        strm_wr_strb_w2e_esto;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_wr_addr_w2e_esto;
    logic [BANK_DATA_WIDTH-1:0]                          strm_wr_data_w2e_esto;
    logic                                                strm_rd_en_w2e_esto;
    logic [GLB_ADDR_WIDTH-1:0]                           strm_rd_addr_w2e_esto;
    logic [BANK_DATA_WIDTH-1:0]                          strm_rd_data_w2e_esto;
    logic                                                strm_rd_data_valid_w2e_esto;

    // packet_sel_t                                         strm_wr_packet_sel_w2e_wsti;
    // packet_sel_t                                         strm_rdrq_packet_sel_w2e_wsti;
    // packet_sel_t                                         strm_rdrs_packet_sel_w2e_wsti;
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

    // packet_sel_t                                         pc_rdrq_packet_sel_e2w_esti;
    // packet_sel_t                                         pc_rdrs_packet_sel_e2w_esti;
    logic                                                pc_rd_en_e2w_esti;
    logic [GLB_ADDR_WIDTH-1:0]                           pc_rd_addr_e2w_esti;
    logic [BANK_DATA_WIDTH-1:0]                          pc_rd_data_e2w_esti;
    logic                                                pc_rd_data_valid_e2w_esti;

    // packet_sel_t                                         pc_rdrq_packet_sel_w2e_esto;
    // packet_sel_t                                         pc_rdrs_packet_sel_w2e_esto;
    logic                                                pc_rd_en_w2e_esto;
    logic [GLB_ADDR_WIDTH-1:0]                           pc_rd_addr_w2e_esto;
    logic [BANK_DATA_WIDTH-1:0]                          pc_rd_data_w2e_esto;
    logic                                                pc_rd_data_valid_w2e_esto;

    // packet_sel_t                                         pc_rdrq_packet_sel_w2e_wsti;
    // packet_sel_t                                         pc_rdrs_packet_sel_w2e_wsti;
    logic                                                pc_rd_en_w2e_wsti;
    logic [GLB_ADDR_WIDTH-1:0]                           pc_rd_addr_w2e_wsti;
    logic [BANK_DATA_WIDTH-1:0]                          pc_rd_data_w2e_wsti;
    logic                                                pc_rd_data_valid_w2e_wsti;

    // packet_sel_t                                         pc_rdrq_packet_sel_e2w_wsto;
    // packet_sel_t                                         pc_rdrs_packet_sel_e2w_wsto;
    logic                                                pc_rd_en_e2w_wsto;
    logic [GLB_ADDR_WIDTH-1:0]                           pc_rd_addr_e2w_wsto;
    logic [BANK_DATA_WIDTH-1:0]                          pc_rd_data_e2w_wsto;
    logic                                                pc_rd_data_valid_e2w_wsto;

    // Config
    // cfg_ifc.master                                              if_cfg_est_m;
    logic                                                if_cfg_est_m_wr_en;
    logic                                                if_cfg_est_m_wr_clk_en;
    logic [AXI_ADDR_WIDTH-1:0]                           if_cfg_est_m_wr_addr;
    logic [AXI_DATA_WIDTH-1:0]                           if_cfg_est_m_wr_data;
    logic                                                if_cfg_est_m_rd_en;
    logic                                                if_cfg_est_m_rd_clk_en;
    logic [AXI_ADDR_WIDTH-1:0]                           if_cfg_est_m_rd_addr;
    logic [AXI_DATA_WIDTH-1:0]                           if_cfg_est_m_rd_data;
    logic                                                if_cfg_est_m_rd_data_valid;

    // cfg_ifc.slave                                               if_cfg_wst_s;
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
    // cfg_ifc.master                                              if_sram_cfg_est_m;
    logic                                                if_sram_cfg_est_m_wr_en;
    logic                                                if_sram_cfg_est_m_wr_clk_en;
    logic [GLB_ADDR_WIDTH-1:0]                           if_sram_cfg_est_m_wr_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      if_sram_cfg_est_m_wr_data;
    logic                                                if_sram_cfg_est_m_rd_en;
    logic                                                if_sram_cfg_est_m_rd_clk_en;
    logic [GLB_ADDR_WIDTH-1:0]                           if_sram_cfg_est_m_rd_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      if_sram_cfg_est_m_rd_data;
    logic                                                if_sram_cfg_est_m_rd_data_valid;

    // cfg_ifc.slave                                               if_sram_cfg_wst_s;
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
    logic                                                cfg_pc_tile_connected_wsti;
    logic                                                cfg_pc_tile_connected_esto;

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

    logic                                                cgra_cfg_pc_wsti_wr_en;
    logic                                                cgra_cfg_pc_wsti_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0]                      cgra_cfg_pc_wsti_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      cgra_cfg_pc_wsti_data;

    logic                                                cgra_cfg_pc_esto_wr_en;
    logic                                                cgra_cfg_pc_esto_rd_en;
    logic [CGRA_CFG_ADDR_WIDTH-1:0]                      cgra_cfg_pc_esto_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0]                      cgra_cfg_pc_esto_data;

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

    // soft reset
    logic                                                cgra_soft_reset;

    // trigger
    logic                                                strm_start_pulse;
    logic                                                pc_start_pulse;
    logic                                                strm_f2g_interrupt_pulse;
    logic                                                strm_g2f_interrupt_pulse;
    logic                                                pcfg_g2f_interrupt_pulse;

    // max cycle set
    initial begin
        int max_cycle = 10000;
        repeat(max_cycle) @(posedge clk);
        $display("\n%0t\tERROR: The %7d cycles marker has passed!", $time, max_cycle);
        $finish(2);
    end

    // back-annotation and dump
`ifdef SYNTHESIS
    initial begin
        $sdf_annotate("/sim/kongty/syn_annotate/glb_tile.sdf",top.dut);
        $dumpfile("glb_tile_syn.vcd");
        $dumpvars(0, top);
    end
`elsif PNR 
    initial begin
        $sdf_annotate("/sim/kongty/pnr_annotate/glb_tile.sdf",top.dut);
        $dumpfile("glb_tile_pnr.vcd");
        $dumpvars(0, top);
    end
`else
    initial begin
        $dumpfile("glb_tile.vcd");
        $dumpvars(0, top);
    end
`endif

    // clk generation
    initial begin
        clk = 0;
        clk_en = 1;
        forever
        #(`CLK_PERIOD/2.0) clk = !clk;
    end

    // initialize all inputs to 0
    initial begin
        glb_tile_id = 0;

        proc_wr_en_e2w_esti = '0;
        proc_wr_strb_e2w_esti = '0;
        proc_wr_addr_e2w_esti = '0;
        proc_wr_data_e2w_esti = '0;
        proc_rd_en_e2w_esti = '0;
        proc_rd_addr_e2w_esti = '0;
        proc_rd_data_e2w_esti = '0;
        proc_rd_data_valid_e2w_esti = '0;

        proc_wr_en_w2e_wsti = '0;
        proc_wr_strb_w2e_wsti = '0;
        proc_wr_addr_w2e_wsti = '0;
        proc_wr_data_w2e_wsti = '0;
        proc_rd_en_w2e_wsti = '0;
        proc_rd_addr_w2e_wsti = '0;
        proc_rd_data_w2e_wsti = '0;
        proc_rd_data_valid_w2e_wsti = '0;

    end

    initial begin
        bit [BANK_DATA_WIDTH-1:0] data;

        reset <= 1;
        repeat(3) @(posedge clk);
        reset <= 0;

        wait(!reset)
        @(posedge clk);

        proc_write(0, 1);
        repeat(3) @(posedge clk);
        proc_read(0, data);

        repeat(3) @(posedge clk);
        $finish;
    end

    // instantiate dut
    glb_tile dut (
        .*);
    
    task automatic proc_write(input bit[GLB_ADDR_WIDTH-1:0] addr, input bit[BANK_DATA_WIDTH-1:0] data);
    begin
        proc_wr_en_w2e_wsti = '1;
        proc_wr_strb_w2e_wsti = {(BANK_DATA_WIDTH/8){1'b1}};
        proc_wr_addr_w2e_wsti = addr;
        proc_wr_data_w2e_wsti = data;
        proc_rd_en_w2e_wsti = '0;
        proc_rd_addr_w2e_wsti = '0;
        @(posedge clk);
        proc_wr_en_w2e_wsti = '0;
        proc_wr_strb_w2e_wsti = '0;
        proc_wr_addr_w2e_wsti = '0;
        proc_wr_data_w2e_wsti = '0;
    end
    endtask

    task automatic proc_read(input bit[GLB_ADDR_WIDTH-1:0] addr, output bit[BANK_DATA_WIDTH-1:0] data);
    begin
        fork
            begin
                proc_wr_en_w2e_wsti = '0;
                proc_wr_strb_w2e_wsti = '0;
                proc_wr_addr_w2e_wsti = '0;
                proc_wr_data_w2e_wsti = '0;
                proc_rd_en_w2e_wsti = '1;
                proc_rd_addr_w2e_wsti = addr;
                @(posedge clk);
                proc_rd_en_w2e_wsti = '0;
                proc_rd_addr_w2e_wsti = '0;
            end
            begin
                while (!proc_rd_data_valid_w2e_esto) begin
                    @(posedge clk);
                end
                $display("\n%0t\tREAD done", $time);
                data = proc_rd_data_w2e_esto;
            end
        join
    end
    endtask

endmodule
