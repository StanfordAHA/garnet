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
    logic [   MU_ADDR_WIDTH-1:0] mu_tl_addr_in;
    logic                         mu_tl_rq_in_vld;
    logic                         mu_tl_rq_in_rdy;
    logic [ MU_TL_NUM_BURST_BITS-1:0] mu_tl_size_in;
    logic [ MU_TL_NUM_BURST_BITS-1:0] mu_tl_size_out;
    logic [ MU_TL_SOURCE_WIDTH-1:0] mu_tl_source_in;
    logic [ MU_TL_SOURCE_WIDTH-1:0] mu_tl_source_out;
    logic [ MU_TL_OPCODE_WIDTH-1:0] mu_tl_opcode_out;
    logic [  MU_WORD_WIDTH-1:0] mu_rd_data;
    logic                         mu_rd_data_valid;
    logic                         mu_rd_data_ready;

endinterface
