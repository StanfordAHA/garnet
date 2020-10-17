/*=============================================================================
** Module: garnet_test.sv
** Description:
**              program for garnet testbench
** Author: Taeyoung Kong
** Change history:  10/14/2020 - Implement the first version
**===========================================================================*/

program garnet_test 
(
    input logic clk, reset, interrupt,
    proc_ifc p_ifc,
    axil_ifc axil_ifc
);

    initial begin

        wait(!reset)
        @(posedge clk);

        repeat(3) @(posedge clk);
        $finish;
    end

endprogram
