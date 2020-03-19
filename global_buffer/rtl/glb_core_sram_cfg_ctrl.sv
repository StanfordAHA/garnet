/*=============================================================================
** Module: glb_core_sram_cfg_ctrl.sv
** Description:
**              Controller of jtag config for sram
** Author: Taeyoung Kong
** Change history:
**      03/14/2020
**          - Implement first version of memory core
**===========================================================================*/
import global_buffer_pkg::*;

module glb_core_sram_cfg_ctrl (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // SRAM Config
    cfg_ifc.master                          if_sram_cfg_est_m,
    cfg_ifc.slave                           if_sram_cfg_wst_s,

    cfg_ifc.master                          if_sram_cfg_bank [BANKS_PER_TILE]
    // output logic                            sram_cfg_wr_en [BANKS_PER_TILE],
    // output logic                            sram_cfg_wr_clk_en [BANKS_PER_TILE],
    // output logic  [BANK_ADDR_WIDTH-1:0]     sram_cfg_wr_addr [BANKS_PER_TILE],
    // output logic  [BANK_DATA_WIDTH-1:0]     sram_cfg_wr_data [BANKS_PER_TILE],

    // output logic                            sram_cfg_rd_en [BANKS_PER_TILE],
    // output logic                            sram_cfg_rd_clk_en [BANKS_PER_TILE],
    // output logic  [BANK_ADDR_WIDTH-1:0]     sram_cfg_rd_addr [BANKS_PER_TILE],
    // input  logic  [BANK_DATA_WIDTH-1:0]     sram_cfg_rd_data [BANKS_PER_TILE],
    // input  logic                            sram_cfg_rd_data_valid [BANKS_PER_TILE]
);

//============================================================================//
// Dummy logic
//============================================================================//

generate
    for (genvar i=0; i<BANKS_PER_TILE; i=i+1) begin
        assign if_sram_cfg_bank[i].wr_en = (if_sram_cfg_wst_s.wr_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) ? if_sram_cfg_wst_s.wr_en : 0;
        assign if_sram_cfg_bank[i].wr_clk_en = (if_sram_cfg_wst_s.wr_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) ? if_sram_cfg_wst_s.wr_clk_en : 0;
        assign if_sram_cfg_bank[i].wr_addr = (if_sram_cfg_wst_s.wr_addr[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH] == i) ? if_sram_cfg_wst_s.wr_addr[0 +: BANK_ADDR_WIDTH] : '0;
        assign if_sram_cfg_bank[i].wr_data = 0;
        assign if_sram_cfg_bank[i].rd_en = (if_sram_cfg_wst_s.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) ? if_sram_cfg_wst_s.rd_en : 0;
        assign if_sram_cfg_bank[i].rd_clk_en = (if_sram_cfg_wst_s.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) ? if_sram_cfg_wst_s.rd_clk_en : 0;
        assign if_sram_cfg_bank[i].rd_addr = (if_sram_cfg_wst_s.rd_addr[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH] == i) ? if_sram_cfg_wst_s.rd_addr[0 +: BANK_ADDR_WIDTH] : '0;
    end
endgenerate

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_sram_cfg_est_m.wr_en <= 0;
        if_sram_cfg_est_m.wr_clk_en <= 0;
        if_sram_cfg_est_m.wr_addr <= 0;
        if_sram_cfg_est_m.wr_data <= 0;
        if_sram_cfg_est_m.rd_en <= 0;
        if_sram_cfg_est_m.rd_clk_en <= 0;
        if_sram_cfg_est_m.rd_addr <= 0;
        if_sram_cfg_wst_s.rd_data <= 0;
        if_sram_cfg_wst_s.rd_data_valid <= 0;
    end
    else begin
        if_sram_cfg_est_m.wr_en <= if_sram_cfg_wst_s.wr_en;
        if_sram_cfg_est_m.wr_clk_en <= if_sram_cfg_wst_s.wr_clk_en;
        if_sram_cfg_est_m.wr_addr <= if_sram_cfg_wst_s.wr_addr;
        if_sram_cfg_est_m.wr_data <= if_sram_cfg_wst_s.wr_data;
        if_sram_cfg_est_m.rd_en <= if_sram_cfg_wst_s.rd_en;
        if_sram_cfg_est_m.rd_clk_en <= if_sram_cfg_wst_s.rd_clk_en;
        if_sram_cfg_est_m.rd_addr <= if_sram_cfg_wst_s.rd_addr;
        if_sram_cfg_wst_s.rd_data <= if_sram_cfg_est_m.rd_data;
        if_sram_cfg_wst_s.rd_data_valid <= if_sram_cfg_est_m.rd_data_valid;
    end
end

endmodule
