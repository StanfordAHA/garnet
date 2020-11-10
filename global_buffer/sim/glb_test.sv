/*=============================================================================
** Module: glb_test.sv
** Description:
**              program for global buffer testbench
** Author: Taeyoung Kong
** Change history:  04/10/2020 - Implement first version of global buffer program
**===========================================================================*/
class MyProcTransaction extends ProcTransaction;
    bit is_read;
    bit [GLB_ADDR_WIDTH-1:0]  addr_internal;
    int length_internal;

    constraint rd_en_c {
        rd_en == is_read;
    }

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
    }

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
    }

    function new(bit[GLB_ADDR_WIDTH-1:0] addr=0, int length=128, bit is_read=0);
        this.is_read = is_read;
        this.addr_internal = addr;
        this.length_internal = length;
    endfunction
endclass

class MySramTransaction #(int ADDR_WIDTH=22) extends RegTransaction;
    function new(bit[ADDR_WIDTH-1:0] addr=0, bit[AXI_DATA_WIDTH-1:0] data=0, bit is_read=0);
        this.trans_type = SRAM;
        if (is_read) begin
            this.rd_en = 1;
            this.rd_addr = addr;
            this.wr_en = 0;
            this.wr_addr = 0;
            this.wr_data = data;
        end else begin
            this.rd_en = 0;
            this.rd_addr = 0;
            this.wr_en = 1;
            this.wr_addr = addr;
            this.wr_data = data;
        end
    endfunction
endclass

class MyRegTransaction #(int ADDR_WIDTH=12) extends RegTransaction;
    function new(bit[ADDR_WIDTH-1:0] addr=0, bit[AXI_DATA_WIDTH-1:0] data=0, bit is_read=0);
        this.trans_type = REG;
        if (is_read) begin
            this.rd_en = 1;
            this.rd_addr = addr;
            this.wr_en = 0;
            this.wr_addr = 0;
            this.wr_data = data;
        end else begin
            this.rd_en = 0;
            this.rd_addr = 0;
            this.wr_en = 1;
            this.wr_addr = addr;
            this.wr_data = data;
        end
    endfunction
endclass

class MyStrmTransaction extends StrmTransaction;
    int length_internal;
    bit is_st;
    bit [GLB_ADDR_WIDTH-1:0] addr_internal;

    constraint st_ld_c {
        if (is_st) {
            this.st_on == 1;
            this.ld_on == 0;
        } else {
            this.st_on == 0;
            this.ld_on == 1;
        }
    }

    constraint length_c {
        solve st_on before st_length;
        solve ld_on before ld_length;
        if (st_on) {
            this.st_length == length_internal;
            this.ld_length == 0;
        } else {
            this.ld_length == length_internal;
            this.st_length == 0;
        }
    }

    constraint addr_c {
        solve st_on before st_addr;
        solve ld_on before ld_addr;
        if (st_on) {
            this.st_addr == addr_internal;
            this.ld_addr == 0;
        } else {
            this.ld_addr == addr_internal;
            this.st_addr == 0;
        }
    }

    constraint data_c {
        solve st_on before st_data;
        solve st_length before st_data;
        if (st_on) {
            st_data.size() == st_length;
            foreach(st_data[i]) st_data[i] == i;
        } else {
            st_data.size() == 0;
        }
    }

    function new(bit [TILE_SEL_ADDR_WIDTH-1:0] tile, bit[GLB_ADDR_WIDTH-1:0] addr=0, int length=128, bit is_st=0);
        this.tile = tile;
        this.is_st = is_st;
        this.length_internal = length;
    endfunction
endclass

program glb_test 
(
    input logic clk, reset,
    proc_ifc p_ifc,
    reg_ifc r_ifc,
    reg_ifc m_ifc,
    strm_ifc s_ifc[NUM_GLB_TILES],
    pcfg_ifc c_ifc[NUM_GLB_TILES]
);

    Environment         env;
    Sequence            seq;
    MyProcTransaction   p_trans_q[$];
    int                 p_cnt;
    MyRegTransaction #(AXI_ADDR_WIDTH) r_trans_q[$];
    MySramTransaction #(GLB_ADDR_WIDTH) m_trans_q[$];
    int                 r_cnt;
    int                 m_cnt;
    MyStrmTransaction   s_trans_q[$];
    int                 s_cnt;

    logic [BANK_DATA_WIDTH-1:0] data_expected;
    logic [BANK_DATA_WIDTH-1:0] addr_expected;
    logic [BANK_DATA_WIDTH-1:0] data_in;

    bit [AXI_ADDR_WIDTH-1:0] addr_dic[string];

    initial begin
        $srandom(3);

        seq = new();

        //=============================================================================
        // processor write
        //=============================================================================
        seq.empty();
        p_cnt = 0;
        p_trans_q[p_cnt++] = new(0, 128);
        p_trans_q[p_cnt++] = new(0, 128, 1);

        foreach(p_trans_q[i]) begin
            seq.add(p_trans_q[i]);
        end

        env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
        env.build();
        env.run();

        repeat(300) @(posedge clk);

        //=============================================================================
        // register read/write
        //=============================================================================
        seq.empty();
        r_cnt = 0;
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["TILE_CTRL"], 'h44);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["TILE_CTRL"], 'h44, 1);

        foreach(r_trans_q[i]) begin
            seq.add(r_trans_q[i]);
        end

        env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
        env.build();
        env.run();
        repeat(300) @(posedge clk);

        //=============================================================================
        // sram read/write
        //=============================================================================
        seq.empty();
        m_cnt = 0;
        m_trans_q[m_cnt++] = new('h10, 100);
        m_trans_q[m_cnt++] = new('h10, 100, 1);

        m_trans_q[m_cnt++] = new('h40000, 100);
        m_trans_q[m_cnt++] = new('h40000, 100, 1);

        foreach(m_trans_q[i]) begin
            seq.add(m_trans_q[i]);
        end

        env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
        env.build();
        env.run();
        repeat(300) @(posedge clk);

        //=============================================================================
        // stream write tile 0, read tile 0
        //=============================================================================
        seq.empty();
        r_cnt = 0;
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["TILE_CTRL"], 'h154);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_START_ADDR"], 'h0);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_NUM_WORDS"], 'd128);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_VALIDATE"], 'h1);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_START_ADDR"], 'h0);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_ITER_CTRL_0"], (128 << MAX_STRIDE_WIDTH) + 1);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_VALIDATE"], 'h1);

        s_cnt = 0;
        s_trans_q[s_cnt++] = new(0, 0, 128, 1);
        s_trans_q[s_cnt++] = new(0, 0, 128);

        foreach(r_trans_q[i]) begin
            seq.add(r_trans_q[i]);
        end
        foreach(s_trans_q[i]) begin
            seq.add(s_trans_q[i]);
        end

        env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
        env.build();
        env.run();
        repeat(300) @(posedge clk);

        //=============================================================================
        // stream write tile 0-1, read tile 0
        //=============================================================================
        seq.empty();
        r_cnt = 0;
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["TILE_CTRL"], 'h155);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LATENCY"], 'h2);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_START_ADDR"], (1 << 18)-64);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_NUM_WORDS"], 'd128);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_VALIDATE"], 'h1);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_START_ADDR"], (1 << 18)-64);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_ITER_CTRL_0"], (128 << MAX_STRIDE_WIDTH) + 1);
        r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_VALIDATE"], 'h1);

        s_cnt = 0;
        s_trans_q[s_cnt++] = new(0, (1 << 18) - 64, 128, 1);
        s_trans_q[s_cnt++] = new(0, (1 << 18) - 64, 128);

        foreach(r_trans_q[i]) begin
            seq.add(r_trans_q[i]);
        end
        foreach(s_trans_q[i]) begin
            seq.add(s_trans_q[i]);
        end

        env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
        env.build();
        env.run();
        repeat(300) @(posedge clk);
    end

    //=============================================================================
    // AXI address in associative array
    //=============================================================================
    initial begin
        addr_dic["TILE_CTRL"]                   = 'h00;
        addr_dic["LATENCY"]                     = 'h04;
        addr_dic["ST_DMA_HEADER_0_VALIDATE"]    = 'h08;
        addr_dic["ST_DMA_HEADER_0_START_ADDR"]  = 'h0C;
        addr_dic["ST_DMA_HEADER_0_NUM_WORDS"]   = 'h10;
        addr_dic["ST_DMA_HEADER_1_VALIDATE"]    = 'h14;
        addr_dic["ST_DMA_HEADER_1_START_ADDR"]  = 'h18;
        addr_dic["ST_DMA_HEADER_1_NUM_WORDS"]   = 'h1C;
        addr_dic["ST_DMA_HEADER_2_VALIDATE"]    = 'h20;
        addr_dic["ST_DMA_HEADER_2_START_ADDR"]  = 'h24;
        addr_dic["ST_DMA_HEADER_2_NUM_WORDS"]   = 'h28;
        addr_dic["ST_DMA_HEADER_3_VALIDATE"]    = 'h2C;
        addr_dic["ST_DMA_HEADER_3_START_ADDR"]  = 'h30; 
        addr_dic["ST_DMA_HEADER_3_NUM_WORDS"]   = 'h34;
        addr_dic["LD_DMA_HEADER_0_VALIDATE"]    = 'h38;
        addr_dic["LD_DMA_HEADER_0_START_ADDR"]  = 'h3C;
        addr_dic["LD_DMA_HEADER_0_ACTIVE_CTRL"] = 'h40;
        addr_dic["LD_DMA_HEADER_0_ITER_CTRL_0"] = 'h44;
        addr_dic["LD_DMA_HEADER_0_ITER_CTRL_1"] = 'h48;
        addr_dic["LD_DMA_HEADER_0_ITER_CTRL_2"] = 'h4C;
        addr_dic["LD_DMA_HEADER_0_ITER_CTRL_3"] = 'h50;
        addr_dic["LD_DMA_HEADER_1_VALIDATE"]    = 'h54;
        addr_dic["LD_DMA_HEADER_1_START_ADDR"]  = 'h58;
        addr_dic["LD_DMA_HEADER_1_ACTIVE_CTRL"] = 'h5C;
        addr_dic["LD_DMA_HEADER_1_ITER_CTRL_0"] = 'h60;
        addr_dic["LD_DMA_HEADER_1_ITER_CTRL_1"] = 'h64;
        addr_dic["LD_DMA_HEADER_1_ITER_CTRL_2"] = 'h68;
        addr_dic["LD_DMA_HEADER_1_ITER_CTRL_3"] = 'h6C;
        addr_dic["LD_DMA_HEADER_2_VALIDATE"]    = 'h70;
        addr_dic["LD_DMA_HEADER_2_START_ADDR"]  = 'h74;
        addr_dic["LD_DMA_HEADER_2_ACTIVE_CTRL"] = 'h78;
        addr_dic["LD_DMA_HEADER_2_ITER_CTRL_0"] = 'h7C;
        addr_dic["LD_DMA_HEADER_2_ITER_CTRL_1"] = 'h80;
        addr_dic["LD_DMA_HEADER_2_ITER_CTRL_2"] = 'h84;
        addr_dic["LD_DMA_HEADER_2_ITER_CTRL_3"] = 'h88;
        addr_dic["LD_DMA_HEADER_3_VALIDATE"]    = 'h8C;
        addr_dic["LD_DMA_HEADER_3_START_ADDR"]  = 'h90;
        addr_dic["LD_DMA_HEADER_3_ACTIVE_CTRL"] = 'h94;
        addr_dic["LD_DMA_HEADER_3_ITER_CTRL_0"] = 'h98;
        addr_dic["LD_DMA_HEADER_3_ITER_CTRL_1"] = 'h9C;
        addr_dic["LD_DMA_HEADER_3_ITER_CTRL_2"] = 'hA0;
        addr_dic["LD_DMA_HEADER_3_ITER_CTRL_3"] = 'hA4;
        addr_dic["PC_DMA_HEADER_0_START_ADDR"]  = 'hA8;
        addr_dic["PC_DMA_HEADER_0_NUM_CFG"]     = 'hAC;
    end

endprogram
