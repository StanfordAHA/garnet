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
    bit [GLB_ADDR_WIDTH-1:0]  addr_internal;
    int length_internal;

    constraint en_c {
        rd_en == is_read;
    };

    constraint addr_c {
        solve wr_en before wr_addr;
        solve rd_en before rd_addr;
        length == length_internal;
        if (wr_en) {
            wr_addr == addr_internal;
            rd_addr == 0;
        } else {
            wr_addr == 0;
            wr_data.size() == 0;
            rd_addr == addr_internal;
        }
    };

    constraint data_c {
        solve wr_en before wr_addr;
        solve rd_en before rd_addr;
        length == length_internal;
        if (wr_en) {
            wr_data.size() == length;
            wr_strb.size() == length;
            foreach(wr_data[i]) wr_data[i] == ((4*i+3) << 48) + ((4*i+2) << 32) + ((4*i+1) << 16) + (4*i);
            foreach(wr_strb[i]) wr_strb[i] == 8'hFF;
        }
    };

    function new(bit[GLB_ADDR_WIDTH-1:0] addr=0, int length=128, bit is_read=0);
        this.is_read = is_read;
        this.addr_internal = addr;
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

    function new(bit[TILE_SEL_ADDR_WIDTH-1:0] tile=0, bit[7:0] addr=0, bit[AXI_DATA_WIDTH-1:0] data=0, bit is_read=0);
        this.is_read = is_read;
        this.addr_internal = tile;
        this.addr_internal = (this.addr_internal << 8) + addr;
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

        //=============================================================================
        // // Processor write tile 0, Stream read tile 0
        //=============================================================================
        // seq = new();
        // my_trans_p[0] = new(0, 128);
        // my_trans_p[0].max_length_c.constraint_mode(0);
        // 
        // my_trans_c[0] = new(0, 'h00, 'he4);

        // my_trans_c[1] = new(0, 'h3c, 'h0);
        // my_trans_c[2] = new(0, 'h40, 'h20008);
        // my_trans_c[3] = new(0, 'h44, 'h200008);
        // my_trans_c[4] = new(0, 'h48, 'h3000010);
        // my_trans_c[5] = new(0, 'h38, 'h1);

        // my_trans_c[6] = new(0, 'h58, 'h100);
        // my_trans_c[7] = new(0, 'h5c, 'h20008);
        // my_trans_c[8] = new(0, 'h60, 'h200008);
        // my_trans_c[9] = new(0, 'h64, 'h3000010);
        // my_trans_c[10] = new(0, 'h54, 'h1);

        // foreach(my_trans_p[i])
        //     seq.add(my_trans_p[i]);
        // foreach(my_trans_c[i])
        //     seq.add(my_trans_c[i]);

        // env = new(seq, p_ifc, r_ifc, s_ifc);
        // env.build();
        // env.run();

        // repeat(300) @(posedge clk);
        // s_ifc[0].cbd.strm_start_pulse <= 1;
        // @(posedge clk);
        // s_ifc[0].cbd.strm_start_pulse <= 0;
        // repeat(2000) @(posedge clk);

        // repeat(300) @(posedge clk);
        // s_ifc[0].cbd.strm_start_pulse <= 1;
        // @(posedge clk);
        // s_ifc[0].cbd.strm_start_pulse <= 0;
        // repeat(2000) @(posedge clk);


        //=============================================================================
        // // Processor write tile 1, Stream read tile 1
        //=============================================================================
        // seq = new();
        // my_trans_p[0] = new((1<<(BANK_ADDR_WIDTH+1)), 128);
        // my_trans_p[0].max_length_c.constraint_mode(0);
        // 
        // my_trans_c[0] = new(1, 'h00, 'h54);
        // my_trans_c[1] = new(1, 'h3c, (1<<(BANK_ADDR_WIDTH+1)));
        // my_trans_c[2] = new(1, 'h44, 'h200008);
        // my_trans_c[3] = new(1, 'h48, 'h3000008);
        // my_trans_c[4] = new(1, 'h38, 'h1);

        // foreach(my_trans_p[i])
        //     seq.add(my_trans_p[i]);
        // foreach(my_trans_c[i])
        //     seq.add(my_trans_c[i]);

        // env = new(seq, p_ifc, r_ifc, s_ifc);
        // env.build();
        // env.run();

        // repeat(300) @(posedge clk);
        // s_ifc[1].cbd.strm_start_pulse <= 1;
        // @(posedge clk);
        // s_ifc[1].cbd.strm_start_pulse <= 0;
        // repeat(300) @(posedge clk);





        //=============================================================================
        // Processor write tile 0-1, Stream read tile 0-1
        //=============================================================================
        // seq = new();
        // my_trans_p[0] = new((2**(BANK_ADDR_WIDTH+1)) - 128, 1024);
        // my_trans_p[0].max_length_c.constraint_mode(0);
        // 
        // my_trans_c[0] = new(0, 'h00, 'h55);
        // my_trans_c[1] = new(0, 'h3c, (2**(BANK_ADDR_WIDTH+1))-128);
        // my_trans_c[2] = new(0, 'h44, 'h200400);
        // my_trans_c[3] = new(0, 'h38, 'h1);
        // my_trans_c[4] = new(0, 'h04, 'h1);

        // foreach(my_trans_p[i])
        //     seq.add(my_trans_p[i]);
        // foreach(my_trans_c[i])
        //     seq.add(my_trans_c[i]);

        // env = new(seq, p_ifc, r_ifc, s_ifc);
        // env.build();
        // env.run();

        // repeat(300) @(posedge clk);
        // s_ifc[0].cbd.strm_start_pulse <= 1;
        // @(posedge clk);
        // s_ifc[0].cbd.strm_start_pulse <= 0;
        // repeat(2000) @(posedge clk);



        //=============================================================================
        // // Stream write tile 0, Stream read tile 0
        //=============================================================================
        seq = new();
        
        my_trans_c[0] = new(0, 'h00, 'h310);

        my_trans_c[1] = new(0, 'h0c, 'h0);
        my_trans_c[2] = new(0, 'h10, 'd128);
        my_trans_c[3] = new(0, 'h08, 'h1);

        my_trans_c[4] = new(0, 'h18, 'h2);
        my_trans_c[5] = new(0, 'h1c, 'd127);
        my_trans_c[6] = new(0, 'h14, 'h1);

        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);

        env = new(seq, p_ifc, r_ifc, s_ifc);
        env.build();
        env.run();

        repeat(300) @(posedge clk);
        for (int i=0; i<128; i++) begin
            s_ifc[0].cbd.data_f2g <= i;
            s_ifc[0].cbd.data_valid_f2g <= 1;
            @(posedge clk);
        end
        s_ifc[0].cbd.data_f2g <= 0;
        s_ifc[0].cbd.data_valid_f2g <= 0;

        repeat(300) @(posedge clk);
        for (int i=0; i<128; i++) begin
            s_ifc[0].cbd.data_f2g <= i;
            s_ifc[0].cbd.data_valid_f2g <= 1;
            @(posedge clk);
        end
        s_ifc[0].cbd.data_f2g <= 0;
        s_ifc[0].cbd.data_valid_f2g <= 0;

        repeat(300) @(posedge clk);
    end
    
endprogram
