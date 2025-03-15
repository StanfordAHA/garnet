/*=============================================================================
** Module: glb_mu_ifc.sv
** Description:
**              interface for glb-MU 
** Author: Michael Oduoza
** Change history:
**  03/13/2025 - Implement first version
**===========================================================================*/

interface glb_mu_ifc (
    input logic clk
);

    // declare the signals
    logic                         mu_rd_en;
    logic [   GLB_ADDR_WIDTH-1:0] mu_rd_addr;
    logic [  (BANK_DATA_WIDTH*MU_WORD_NUM_TILES)-1:0] mu_rd_data;
    logic                         mu_rd_data_valid;

    // modport glb(
    //     input clk,
    //     input wr_en, wr_strb, wr_addr, wr_data, rd_en, rd_addr,
    //     output rd_data, rd_data_valid
    // );

    // // clocking cbd @(posedge clk);
    // modport driver(
    //     input clk,
    //     output wr_en, wr_strb, wr_addr, wr_data, rd_en, rd_addr,
    //     input rd_data, rd_data_valid
    // );

    // // clocking cbm @(posedge clk);
    // modport monitor(
    //     input clk, wr_en, wr_strb, wr_addr, wr_data, rd_en, rd_addr, rd_data, rd_data_valid
    // );

endinterface
