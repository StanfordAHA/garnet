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
    logic [   MU_ADDR_WIDTH-1:0] mu_addr_in;
    logic                         mu_addr_in_vld;
    logic                         mu_addr_in_rdy;
    logic [  MU_WORD_WIDTH-1:0] mu_rd_data;
    logic                         mu_rd_data_valid;
    logic                         mu_rd_data_ready;

endinterface
