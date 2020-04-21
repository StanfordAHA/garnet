/*=============================================================================
** Module: glb_test.sv
** Description:
**              program for global buffer testbench
** Author: Taeyoung Kong
** Change history:  04/10/2020 - Implement first version of global buffer program
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

class MyProcTransaction extends ProcTransaction;
    bit is_read;
    bit [GLB_ADDR_WIDTH-1:0] addr;
    int length_internal;
    constraint en_c {
        rd_en == is_read;
    };

    constraint addr_c {
        solve wr_en before wr_addr;
        solve rd_en before rd_addr;
        length == length_internal;
        if (wr_en) {
            wr_addr == addr;
            rd_addr == 0;
        } else {
            wr_addr == 0;
            wr_data.size() == 0;
            rd_addr == addr;
        }
    };

    constraint data_c {
        solve wr_en before wr_addr;
        solve rd_en before rd_addr;
        length == length_internal;
        if (wr_en) {
            wr_data.size() == length;
            foreach(wr_data[i]) wr_data[i] == (wr_addr + i);
        }
    };

    function new(bit[TILE_SEL_ADDR_WIDTH-1:0] tile=0, bit[BANK_ADDR_WIDTH-1:0] bank_addr=0, int length=128, bit is_read=0);
        this.is_read = is_read;
        this.addr = (tile << BANK_ADDR_WIDTH) + bank_addr;
        this.length_internal = length;
    endfunction
endclass

class MyRegTransaction extends RegTransaction;
    bit is_read;
    bit [AXI_ADDR_WIDTH-1:0] addr_internal;
    bit [AXI_DATA_WIDTH-1:0] data_internal;

    // en constraint
    constraint en_c {
        rd_en == is_read;
    };

    // addr constraint
    constraint addr_c {
        solve rd_en before rd_addr;
        solve wr_en before wr_addr;
        if (rd_en) {
            rd_addr == addr_internal;
            wr_addr == 0;
            wr_data == 0;
        } else {
            rd_addr == 0;
            wr_addr == addr_internal;
            wr_data == data_internal;
        }
    }

    function new(bit[TILE_SEL_ADDR_WIDTH-1:0] tile=0, bit[5:0] addr=0, bit[AXI_DATA_WIDTH-1:0] data=0, bit is_read=0);
        this.is_read = is_read;
        this.addr_internal = (tile << 8) + addr;
        this.data_internal = data;
    endfunction

endclass

program automatic glb_test (
    input logic clk, reset,
    proc_ifc p_ifc,
    reg_ifc r_ifc,
    strm_ifc s_ifc[NUM_GLB_TILES]
);

    Environment         env;
    Sequence            seq;
    MyProcTransaction   my_trans_p[$];
    MyRegTransaction    my_trans_c[$];

    initial begin
        $srandom(3);
        seq = new();

        // Processor write, Stream read
        my_trans_p[0] = new(0, 0, 128);
        
        my_trans_c[0] = new(0, 0, 11'h7ff);
        my_trans_c[1] = new(0, 0, 11'h7ff, 1);

        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);

        env = new(seq, p_ifc, r_ifc, s_ifc);

        env.build();
        env.run();




    end
    
endprogram
