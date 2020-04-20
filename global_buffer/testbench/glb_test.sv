/*=============================================================================
** Module: tb_global_buffer_prog.sv
** Description:
**              program for global buffer testbench
** Author: Taeyoung Kong
** Change history:  02/03/2020 - Implement first version of global buffer program
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

class TileProcTransaction extends ProcTransaction;
endclass

program automatic glb_test (
    input logic clk, reset,
    proc_ifc p_ifc);

    Environment env;
    TileProcTransaction my_trans;

    initial begin
        $srandom(10);
        my_trans = new();

        env = new(p_ifc); 
        env.build();
        env.p_gen.repeat_cnt = 10;
        env.p_gen.blueprint = my_trans;
        env.run();
    end
    
endprogram
