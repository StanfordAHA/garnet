/*=============================================================================
** Module: behavioral_matrix_unit.sv
** Description:
**              A behavioral matrix unit with ready-valid interface that drives
                the CGRA 
** Author: Michael Oduoza
** Change history:  12/31/2024 - Implement the first version
**===========================================================================*/
interface behavioral_matrix_unit #(
    parameter MU_DATAWIDTH = 16,
    parameter OC_0 = 32
) (
    input logic clk,
    input logic reset,
    input logic cgra2mu_ready,
    output logic mu2cgra_valid,
    output logic [MU_DATAWIDTH-1:0] mu2cgra [OC_0-1:0]
);

endinterface