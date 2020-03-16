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

endmodule
