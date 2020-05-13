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
    reg_ifc m_ifc,
    strm_ifc s_ifc[NUM_GLB_TILES],
    pcfg_ifc c_ifc[NUM_GLB_TILES]
);

    Environment         env;
    Sequence            seq;
    MyProcTransaction   my_trans_p[$];
    MyRegTransaction    my_trans_c[$];

    logic [BANK_DATA_WIDTH-1:0] data_expected;
    logic [BANK_DATA_WIDTH-1:0] addr_expected;
    logic [BANK_DATA_WIDTH-1:0] data_in;

    initial begin
        $srandom(3);

        //=============================================================================
        // configuration read/write
        //=============================================================================
        seq = new();
        my_trans_p = {};
        my_trans_c = {};
        my_trans_c[0] = new(15, 'h00, 'he4);

        my_trans_c[1] = new(15, 'h00, 'he4, 1);
        
        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);

        fork
            begin
                env = new(seq, p_ifc, r_ifc, s_ifc, c_ifc);
                env.build();
                env.run();
            end
            begin
                repeat(30) @(posedge clk);
                top.cgra_stall_in <= 1;
            end
        join

        repeat(300) @(posedge clk);


        //=============================================================================
        // Processor write tile 0, Processor read tile 0
        //=============================================================================
        seq = new();
        my_trans_p = {};
        my_trans_c = {};
        my_trans_p[0] = new(0, 128);
        my_trans_p[0].max_length_c.constraint_mode(0);
        
        my_trans_p[1] = new(0, 128, 1);
        my_trans_p[1].max_length_c.constraint_mode(0);
        
        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);

        fork
            begin
                env = new(seq, p_ifc, r_ifc, s_ifc, c_ifc);
                env.build();
                env.run();
            end
            begin
                @(p_ifc.rd_data_valid == 1)
                for (int i=0; i<128; i++) begin
                    data_expected = ((4*i+3) << 48) + ((4*i+2) << 32) + ((4*i+1) << 16) + (4*i);
                    assert(p_ifc.rd_data_valid == 1) else $error("rd_data_valid is not asserted");
                    assert(p_ifc.rd_data == data_expected) else $error("proc_rd_data expected: 0x%h, real: 0x%h", data_expected, p_ifc.rd_data);
                    @(posedge clk);
                end
            end
        join

        repeat(300) @(posedge clk);

        //=============================================================================
        // Processor write tile 0-1, Processor read tile 0-1
        //=============================================================================
        seq = new();
        my_trans_p = {};
        my_trans_c = {};
        my_trans_p[0] = new((2**(BANK_ADDR_WIDTH+1)) - 128, 512);
        my_trans_p[0].max_length_c.constraint_mode(0);
        
        my_trans_p[1] = new((2**(BANK_ADDR_WIDTH+1)) - 128, 512, 1);
        my_trans_p[1].max_length_c.constraint_mode(0);
        
        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);

        fork
            begin
                env = new(seq, p_ifc, r_ifc, s_ifc, c_ifc);
                env.build();
                env.run();
            end
            begin
                @(p_ifc.rd_data_valid == 1)
                for (int i=0; i<512; i++) begin
                    data_expected = ((4*i+3) << 48) + ((4*i+2) << 32) + ((4*i+1) << 16) + (4*i);
                    assert(p_ifc.rd_data_valid == 1) else $error("rd_data_valid is not asserted");
                    assert(p_ifc.rd_data == data_expected) else $error("proc_rd_data expected: 0x%h, real: 0x%h", data_expected, p_ifc.rd_data);
                    @(posedge clk);
                end
            end
        join

        repeat(300) @(posedge clk);


        //=============================================================================
        // Processor write tile 0, Stream read tile 0
        //=============================================================================
        seq = new();
        my_trans_p = {};
        my_trans_c = {};
        my_trans_p[0] = new(0, 128);
        my_trans_p[0].max_length_c.constraint_mode(0);
        
        my_trans_c[0] = new(0, 'h00, 'he4);

        my_trans_c[1] = new(0, 'h3c, 'h0);
        my_trans_c[2] = new(0, 'h40, 'h20008);
        my_trans_c[3] = new(0, 'h44, 'h200008);
        my_trans_c[4] = new(0, 'h48, 'h3000010);
        my_trans_c[5] = new(0, 'h38, 'h1);

        my_trans_c[6] = new(0, 'h58, 'h100);
        my_trans_c[7] = new(0, 'h5c, 'h20008);
        my_trans_c[8] = new(0, 'h60, 'h200008);
        my_trans_c[9] = new(0, 'h64, 'h3000010);
        my_trans_c[10] = new(0, 'h54, 'h1);

        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);

        fork
            begin
                env = new(seq, p_ifc, r_ifc, s_ifc, c_ifc);
                env.build();
                env.run();
            end
            begin
                repeat(300) @(posedge clk);
                s_ifc[0].cbd.strm_start_pulse <= 1;
                @(posedge clk);
                s_ifc[0].cbd.strm_start_pulse <= 0;

                data_expected = 0;

                @(s_ifc[0].data_valid_g2f == 1)
                for(int i=0; i<16; i++) begin
                    for (int j=0; j<10; j++) begin
                        if (j%10 < 8) begin
                            data_expected = i*24+j;
                            assert(s_ifc[0].data_valid_g2f == 1);
                            assert(s_ifc[0].data_g2f == data_expected) else $error("data_expected: 0x%h, real_data: 0x%h", data_expected, s_ifc[0].data_g2f);
                        end
                        else begin
                            assert(s_ifc[0].data_valid_g2f == 0);
                        end
                        @(posedge clk);
                    end
                end
                repeat(200) @(posedge clk);

            end
        join


        //=============================================================================
        // Processor write tile 0-1, Stream read tile 0-1
        //=============================================================================
        seq = new();
        my_trans_p = {};
        my_trans_c = {};
        my_trans_p[0] = new((2**(BANK_ADDR_WIDTH+1)) - 128, 1024);
        my_trans_p[0].max_length_c.constraint_mode(0);
        
        my_trans_c[0] = new(0, 'h00, 'h55);
        my_trans_c[1] = new(0, 'h3c, (2**(BANK_ADDR_WIDTH+1))-128);
        my_trans_c[2] = new(0, 'h40, 'h0);
        my_trans_c[3] = new(0, 'h44, 'h200400);
        my_trans_c[4] = new(0, 'h48, 'h0);
        my_trans_c[5] = new(0, 'h38, 'h1);
        my_trans_c[6] = new(0, 'h04, 'h2);

        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);

        fork
            begin
                env = new(seq, p_ifc, r_ifc, s_ifc, c_ifc);
                env.build();
                env.run();
            end
            begin
                repeat(1200) @(posedge clk);
                s_ifc[0].cbd.strm_start_pulse <= 1;
                @(posedge clk);
                s_ifc[0].cbd.strm_start_pulse <= 0;

                data_expected = 0;

                @(s_ifc[0].data_valid_g2f == 1)
                for(int i=0; i<128; i++) begin
                    for (int j=0; j<8; j++) begin
                        assert(s_ifc[0].data_valid_g2f == 1);
                        assert(s_ifc[0].data_g2f == data_expected) else $error("data_expected: 0x%h, real_data: 0x%h", data_expected, s_ifc[0].data_g2f);
                        data_expected++;
                        @(posedge clk);
                    end
                end
                assert(s_ifc[0].data_valid_g2f == 0);
                repeat(2000) @(posedge clk);

            end
        join



        //=============================================================================
        // Stream write tile 0
        //=============================================================================
        seq = new();
        
        my_trans_p = {};
        my_trans_c = {};

        my_trans_c[0] = new(0, 'h00, 'h310);
        my_trans_c[1] = new(0, 'h0c, 'h0);
        my_trans_c[2] = new(0, 'h10, 'd128);
        my_trans_c[3] = new(0, 'h08, 'h1);

        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);
        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);

        data_in = 0;
        env = new(seq, p_ifc, r_ifc, s_ifc, c_ifc);
        env.build();
        env.run();
        repeat(300) @(posedge clk);
        for (int i=0; i<16; i++) begin
            for (int j=0; j<10; j++) begin
                if(j%10 < 8) begin
                    s_ifc[0].cbd.data_f2g <= data_in++;
                    s_ifc[0].cbd.data_valid_f2g <= 1;
                end
                else begin
                    s_ifc[0].cbd.data_f2g <= 0;
                    s_ifc[0].cbd.data_valid_f2g <= 0;
                end
                @(posedge clk);
            end
        end
        s_ifc[0].cbd.data_f2g <= 0;
        s_ifc[0].cbd.data_valid_f2g <= 0;

        repeat(300) @(posedge clk);
        
        // now read
        my_trans_p = {};
        my_trans_c = {};

        my_trans_p[0] = new(0, 128, 1);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);
        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);

        fork
            begin
                env = new(seq, p_ifc, r_ifc, s_ifc, c_ifc);
                env.build();
                env.run();
            end
            begin
                @(p_ifc.rd_data_valid == 1)
                for (int i=0; i<128; i++) begin
                    data_expected = ((4*i+3) << 48) + ((4*i+2) << 32) + ((4*i+1) << 16) + (4*i);
                    assert(p_ifc.rd_data_valid == 1) else $error("rd_data_valid is not asserted");
                    assert(p_ifc.rd_data == data_expected) else $error("data expected: 0x%h, real_rd_data: 0x%h", data_expected, p_ifc.rd_data );

                    @(posedge clk);
                end
            end
        join

        repeat(300) @(posedge clk);


        //=============================================================================
        // Parallel Configuration test
        //=============================================================================
        seq = new();
        
        my_trans_p = {};
        my_trans_c = {};

        my_trans_p[0] = new((15 << (BANK_ADDR_WIDTH+1)), 128);
        my_trans_p[0].max_length_c.constraint_mode(0);
        
        my_trans_c[0] = new(0, 'h00, 'h402);
        for (int i=1; i<NUM_GLB_TILES-1; i++) begin
            my_trans_c[i] = new(i, 'h00, 'h2);
        end

        my_trans_c[15] = new(0, 'ha8, (15<<(BANK_ADDR_WIDTH+1)));
        my_trans_c[16] = new(0, 'hac, 128);
        my_trans_c[17] = new(0, 'h04, 15<<5);

        foreach(my_trans_p[i])
            seq.add(my_trans_p[i]);
        foreach(my_trans_c[i])
            seq.add(my_trans_c[i]);

        top.cgra_stall_in <= 1;
        top.stall <= 1;

        fork
            begin
                env = new(seq, p_ifc, r_ifc, s_ifc, c_ifc);
                env.build();
                env.run();
            end
            begin
                repeat(300) @(posedge clk);
                top.cgra_cfg_jtag_gc2glb_rd_en <= 1;
                top.cgra_cfg_jtag_gc2glb_addr <= 'h1234;
                top.cgra_cfg_jtag_gc2glb_data <= 'h5678;
                repeat(3) @(posedge clk);
                assert(c_ifc[0].cgra_cfg_addr == 'h0000123400001234);
                assert(c_ifc[0].cgra_cfg_rd_en == 2'b11);
                assert(c_ifc[0].cgra_cfg_wr_en == 0);
                assert(c_ifc[0].cgra_cfg_data == 'h0000567800005678);
                repeat(10) @(posedge clk);

                top.cgra_cfg_jtag_gc2glb_rd_en <= 0;
                top.cgra_cfg_jtag_gc2glb_addr <= 0;
                top.cgra_cfg_jtag_gc2glb_data <= 0;
                repeat(3) @(posedge clk);
                assert(c_ifc[0].cgra_cfg_addr == 0);
                assert(c_ifc[0].cgra_cfg_rd_en == 0);
                assert(c_ifc[0].cgra_cfg_wr_en == 0);
                assert(c_ifc[0].cgra_cfg_data == 0);

                repeat(300) @(posedge clk);
                c_ifc[0].pcfg_start_pulse <= 1;
                @(posedge clk);
                c_ifc[0].pcfg_start_pulse <= 0;

                @(c_ifc[15].cgra_cfg_wr_en == 2'b11)
                for (int i=0; i<128; i++) begin
                    top.cgra_stall_in <= 0;
                    data_expected = ((4*i+1) << 48) + ((4*i+0) << 32) + ((4*i+1) << 16) + (4*i);
                    addr_expected = ((4*i+3) << 48) + ((4*i+2) << 32) + ((4*i+3) << 16) + (4*i+2);
                    assert(c_ifc[15].cgra_cfg_addr == addr_expected) else $error("cfg_addr_expected: 0x%h, cfg_addr_real: 0x%h", addr_expected, c_ifc[15].cgra_cfg_addr);
                    assert(c_ifc[15].cgra_cfg_data == data_expected) else $error("cfg_data_expected: 0x%h, cfg_data_real: 0x%h", data_expected, c_ifc[15].cgra_cfg_data);
                    assert(c_ifc[15].cgra_cfg_wr_en == 2'b11);
                    @(posedge clk);
                end
                repeat(300) @(posedge clk);
            end
        join


        //=============================================================================
        // SRAM configuration read/write test
        //=============================================================================

        m_ifc.cbd_n.wr_clk_en <= 0;
        m_ifc.cbd.wr_en <= 0;
        m_ifc.cbd.wr_addr <= 0;
        m_ifc.cbd.wr_data <= 0;
        m_ifc.cbd_n.rd_clk_en <= 0;
        m_ifc.cbd.rd_en <= 0;
        m_ifc.cbd.rd_addr <= 0;

        // clk enable is set half clk cycle earlier
        @(m_ifc.cbd_n)
        m_ifc.cbd_n.wr_clk_en <= 1;

        @(m_ifc.cbd);
        m_ifc.cbd.wr_en   <= 1;
        m_ifc.cbd.wr_addr <= 'h0;
        m_ifc.cbd.wr_data <= 'h1234;

        repeat(4) @(m_ifc.cbd);
        m_ifc.cbd.wr_en   <= 0;
        m_ifc.cbd.wr_addr <= 0;
        m_ifc.cbd.wr_data <= 0;

        @(m_ifc.cbd_n)
        m_ifc.cbd_n.wr_clk_en <= 0;

        repeat(100) @(m_ifc.cbd);

        // clk enable is set half clk cycle earlier
        @(m_ifc.cbd_n)
        m_ifc.cbd_n.rd_clk_en <= 1;

        @(m_ifc.cbd);
        m_ifc.cbd.rd_en   <= 1;
        m_ifc.cbd.rd_addr <= 'h0;

        repeat(2) @(m_ifc.cbd);
        assert (m_ifc.rd_data_valid == 0);
        repeat(4) @(m_ifc.cbd)
        m_ifc.cbd.rd_en   <= 0;
        m_ifc.cbd.rd_addr <= 0;
        assert (m_ifc.rd_data == 'h1234);
        assert (m_ifc.rd_data_valid == 1);

        @(m_ifc.cbd_n)
        m_ifc.cbd_n.rd_clk_en <= 0;

        repeat(5) @(m_ifc.cbd);
        assert (m_ifc.rd_data == 0);
        assert (m_ifc.rd_data_valid == 0);


        repeat(100) @(m_ifc.cbd);

    end
    
endprogram
