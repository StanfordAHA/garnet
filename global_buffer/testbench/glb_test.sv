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
    constraint tile_addr_c {
        solve wr_en before wr_addr;
        solve rd_en before rd_addr;
        // address is set to tile 0
        length == 100;
        if (wr_en) {
            wr_addr == 0;
            // foreach(wr_data[i]) wr_data[i] == 1;
            // foreach(wr_strb[i]) wr_strb[i] == {{(BANK_DATA_WIDTH/8-1){1'b1}}, 1'b0};
        } else {
            rd_addr == 0;
        }
    };
endclass

program automatic glb_test (
    input logic clk, reset,
    proc_ifc p_ifc);

    Environment env;
    TileProcTransaction my_trans;

    initial begin
        $srandom(3);
        my_trans = new();

        env = new(p_ifc); 
        env.build();
        env.p_gen.repeat_cnt = 6;
        env.p_gen.blueprint = my_trans;
        env.run();
    end
    
endprogram
