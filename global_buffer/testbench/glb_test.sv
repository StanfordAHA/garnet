/*=============================================================================
** Module: tb_global_buffer_prog.sv
** Description:
**              program for global buffer testbench
** Author: Taeyoung Kong
** Change history:  02/03/2020 - Implement first version of global buffer program
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

program automatic glb_test (
    input logic clk, reset,
    proc_ifc p_ifc);

    Environment env;

    initial begin
        env = new(p_ifc); 
        env.build();
        env.run();
    end
    
endprogram
