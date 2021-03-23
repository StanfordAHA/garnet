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
    bit [BANK_DATA_WIDTH-1:0] data_internal [];
    int length_internal;

    function new(bit[GLB_ADDR_WIDTH-1:0] addr=0, int length=128, bit is_read=0, bit[BANK_DATA_WIDTH-1:0] data []= {});
        this.length = length;
        if (is_read) begin
            this.rd_en = 1;
            this.rd_addr = addr;
            this.wr_en = 0;
            this.wr_addr = 0;
            this.wr_data = {};
            this.rd_data = new[length];
            this.rd_data_valid = new[length];
        end else begin
            this.rd_en = 0;
            this.rd_addr = 0;
            this.wr_en = 1;
            this.wr_addr = addr;
            this.wr_data = new [length];
            this.wr_strb = new [length];
            if (data == {}) begin
                for (int i=0; i<length; i++) begin
                    this.wr_data[i] = ((4*i+3) << 48) + ((4*i+2) << 32) + ((4*i+1) << 16) + (4*i);
                end
            end else begin
                this.wr_data = data;
            end
            for (int i=0; i<length; i++) begin
                this.wr_strb[i] = 8'hFF;
            end
        end
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
        this.addr_internal = addr;
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

    bit [BANK_DATA_WIDTH-1:0] data64_arr [];
    bit [CGRA_DATA_WIDTH-1:0] data16_arr [];
    bit [CGRA_CFG_DATA_WIDTH-1:0] cfg_data_arr [];
    bit [CGRA_CFG_ADDR_WIDTH-1:0] cfg_addr_arr [];

    logic [BANK_DATA_WIDTH-1:0] data_expected;
    logic [BANK_DATA_WIDTH-1:0] addr_expected;
    logic [BANK_DATA_WIDTH-1:0] data_in;

    bit [AXI_ADDR_WIDTH-1:0] addr_dic[string];

    logic [4:0] cfg_col;
    logic [7:0] cfg_reg_addr;
    logic [CGRA_CFG_ADDR_WIDTH-1:0] cfg_addr;
    logic [CGRA_CFG_DATA_WIDTH-1:0] cfg_data;
    logic [CGRA_CFG_DATA_WIDTH-1:0] cfg_data_expected;

    int fd;
    int status;
    int num;
    bit [AXI_ADDR_WIDTH-1:0] glb_cfg_addr;
    bit [AXI_DATA_WIDTH-1:0] glb_cfg_data;

    localparam SRAM_MACRO_ADDR_WIDTH = 14;
    localparam SRAM_MACRO_SEL_WIDTH = BANK_ADDR_WIDTH - SRAM_MACRO_ADDR_WIDTH;
    localparam NUM_SRAM_MACRO_PER_TILE = 2 ** (BANK_ADDR_WIDTH - SRAM_MACRO_ADDR_WIDTH + $clog2(BANKS_PER_TILE)); // 16
    localparam int NUM_REG_TEST = 10;

    initial begin
        wait(!reset);
        repeat(10) @(posedge clk);
        seq = new();

        //=============================================================================
        // processor write/read first 256Byte for each bank 
        //=============================================================================
        if ($test$plusargs("TEST_PROC_SIMPLE")) begin
            empty_queues();

            for (int i=0; i<NUM_GLB_TILES*CGRA_PER_GLB; i=i+1) begin
                p_trans_q[p_cnt++] = new(i*(1<<BANK_ADDR_WIDTH), 2);
                p_trans_q[p_cnt++] = new(i*(1<<BANK_ADDR_WIDTH), 2, 1);
            end

            foreach(p_trans_q[i]) begin
                seq.add(p_trans_q[i]);
            end

            env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
            env.build();
            env.run();

            repeat(30) @(posedge clk);
        end

        //=============================================================================
        // processor write/read first 256Byte for each sram macro 
        //=============================================================================
        if ($test$plusargs("TEST_PROC_ALL")) begin
            empty_queues();

            for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
                for (int j=0; j<NUM_SRAM_MACRO_PER_TILE; j=j+1) begin
                    p_trans_q[p_cnt++] = new(((i*NUM_SRAM_MACRO_PER_TILE)+j)*(1<<SRAM_MACRO_ADDR_WIDTH), 32);
                    p_trans_q[p_cnt++] = new(((i*NUM_SRAM_MACRO_PER_TILE)+j)*(1<<SRAM_MACRO_ADDR_WIDTH), 32, 1);
                end
            end

            foreach(p_trans_q[i]) begin
                seq.add(p_trans_q[i]);
            end

            env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
            env.build();
            env.run();

            repeat(30) @(posedge clk);
        end

        //=============================================================================
        // JTAG configuration
        //=============================================================================
        if ($test$plusargs("TEST_JTAG")) begin
            empty_queues();

            for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
                for (int j=0; j<CGRA_PER_GLB; j=j+1) begin
                    // cfg_col = $urandom_range(0, 31);
                    cfg_col = i * 2 + j;
                    cfg_reg_addr = $urandom_range(0, 2**8-1);
                    cfg_addr = (cfg_reg_addr << 8) | cfg_col; 
                    cfg_data = $urandom;
                    jtag_write(cfg_addr, cfg_data);
                    jtag_read(cfg_addr, cfg_data);
                end
            end

            repeat(30) @(posedge clk);
        end

        //=============================================================================
        // configuration register read/write
        //=============================================================================
        if ($test$plusargs("TEST_CONFIG")) begin
            empty_queues();

            // for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
            for (int i=0; i<1; i=i+1) begin
                fd = $fopen("glb.regpair", "r");
                $fscanf(fd, "%d", num);
                // for (int j=0; j<num; j++) begin
                for (int j=0; j<3; j++) begin
                    status = $fscanf(fd, "%h %d", glb_cfg_addr, glb_cfg_data);
                    if(status != 2) $error("glb register pair read failed");
                    r_trans_q[r_cnt++] = new((i << (AXI_ADDR_WIDTH-TILE_SEL_ADDR_WIDTH))|glb_cfg_addr, glb_cfg_data);
                    r_trans_q[r_cnt++] = new((i << (AXI_ADDR_WIDTH-TILE_SEL_ADDR_WIDTH))|glb_cfg_addr, glb_cfg_data, 1);
                    // r_trans_q[r_cnt++] = new((i << (AXI_ADDR_WIDTH-TILE_SEL_ADDR_WIDTH))|glb_cfg_addr, 0);
                    // r_trans_q[r_cnt++] = new((i << (AXI_ADDR_WIDTH-TILE_SEL_ADDR_WIDTH))|glb_cfg_addr, 0, 1);
                end

                $fclose(fd);
            end

            foreach(r_trans_q[i]) begin
                seq.add(r_trans_q[i]);
            end

            env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
            env.build();
            env.run();
            repeat(30) @(posedge clk);
        end

        //=============================================================================
        // stream write tile 0, read tile 0
        //=============================================================================
        if ($test$plusargs("TEST_STRM")) begin
            empty_queues();

            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["TILE_CTRL"], 'h154);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_START_ADDR"], 'h0);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_NUM_WORDS"], 'd128);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_VALIDATE"], 'h1);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_START_ADDR"], 'h0);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_ITER_CTRL_0"], (128 << MAX_STRIDE_WIDTH) + 1);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_VALIDATE"], 'h1);

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
            repeat(30) @(posedge clk);
        end

        //=============================================================================
        // stream write tile 0-1, read tile 0
        //=============================================================================
        if ($test$plusargs("TEST_STRM_CHAIN")) begin
            empty_queues();

            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["TILE_CTRL"], 'h155);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LATENCY"], 'h4);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_START_ADDR"], (1 << (BANK_ADDR_WIDTH+$clog2(BANKS_PER_TILE)))-64);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_NUM_WORDS"], 'd128);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["ST_DMA_HEADER_0_VALIDATE"], 'h1);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_START_ADDR"], (1 << (BANK_ADDR_WIDTH+$clog2(BANKS_PER_TILE)))-64);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_ITER_CTRL_0"], (128 << MAX_STRIDE_WIDTH) + 1);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LD_DMA_HEADER_0_VALIDATE"], 'h1);

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
            repeat(30) @(posedge clk);
        end


        //=============================================================================
        // parallel config tile 0, read tile 0
        //=============================================================================
        if ($test$plusargs("TEST_PCFG")) begin
            empty_queues();

            fd = $fopen("glb.test.bs", "r");
            $fscanf(fd, "%d", num);
            cfg_addr_arr = new [num];
            cfg_data_arr = new [num];
            data64_arr = new [num];
            for (int i=0; i<num; i++) begin
                $fscanf(fd, "%d %d", cfg_addr, cfg_data);
                cfg_addr_arr[i] = cfg_addr;
                cfg_data_arr[i] = cfg_data;
                data64_arr[i] = (cfg_addr << 32) | cfg_data;
            end
            $fclose(fd);

            // num = NUM_CGRA_TILES*NUM_REG_TEST;
            // cfg_addr_arr = new [num];
            // cfg_data_arr = new [num];
            // data64_arr = new [num];
            // for (int i=0; i<NUM_CGRA_TILES; i++) begin
            //     for (int j=0; j<NUM_REG_TEST; j++) begin
            //         cfg_addr_arr[i*NUM_REG_TEST+j] = i + ($urandom_range(0, 2**8-1) << 8);
            //         cfg_data_arr[i*NUM_REG_TEST+j] = $urandom_range(0, 2**32-1);
            //         data64_arr[i*NUM_REG_TEST+j] = (cfg_addr_arr[i*NUM_REG_TEST+j] << 32) | cfg_data_arr[i*NUM_REG_TEST+j];
            //         $display("addr: %h, data: %h", cfg_addr_arr[i*NUM_REG_TEST+j], cfg_data_arr[i*NUM_REG_TEST+j]);
            //     end
            // end

            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["TILE_CTRL"], (1 << 10));
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LATENCY"], 'h4);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["PC_DMA_HEADER_0_START_ADDR"], 0);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["PC_DMA_HEADER_0_NUM_CFG"], num);
            p_trans_q[p_cnt++] = new(0, num, 0, data64_arr);

            foreach(p_trans_q[i]) begin
                seq.add(p_trans_q[i]);
            end
            foreach(r_trans_q[i]) begin
                seq.add(r_trans_q[i]);
            end

            env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
            env.build();
            env.run();

            repeat(10) @(posedge clk);
            #300ps top.pc_start_pulse[0] <= 1;
            @(posedge clk);
            #300ps top.pc_start_pulse[0] <= 0;
            while(1) begin
                @(posedge clk);
                if (top.pcfg_g2f_interrupt_pulse[0]) begin
                    break;
                end
            end

            repeat(50) @(posedge clk);
            for (int i=0; i<num; i++) begin
                cfg_addr = cfg_addr_arr[i];
                cfg_data = cfg_data_arr[i];
                cfg_check(cfg_addr, cfg_data);
            end

            repeat(30) @(posedge clk);
        end

        //=============================================================================
        // parallel config tile 0 bitstream relocation
        //=============================================================================
        if ($test$plusargs("TEST_BS_RELOCATION")) begin
            empty_queues();

            fd = $fopen("glb.test.bs.half", "r");
            $fscanf(fd, "%d", num);
            cfg_addr_arr = new [num];
            cfg_data_arr = new [num];
            data64_arr = new [num];
            for (int i=0; i<num; i++) begin
                $fscanf(fd, "%d %d", cfg_addr, cfg_data);
                cfg_addr_arr[i] = cfg_addr;
                cfg_data_arr[i] = cfg_data;
                data64_arr[i] = (cfg_addr << 32) | cfg_data;
            end
            $fclose(fd);

            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["TILE_CTRL"], (1 << 10));
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["LATENCY"], 'h4);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["PC_DMA_HEADER_0_START_ADDR"], 0);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["PC_DMA_HEADER_0_NUM_CFG"], num);
            r_trans_q[r_cnt++] = new((0 << 8) + addr_dic["PC_DMA_BS_RELOCATION"], 16);
            p_trans_q[p_cnt++] = new(0, num, 0, data64_arr);

            foreach(p_trans_q[i]) begin
                seq.add(p_trans_q[i]);
            end
            foreach(r_trans_q[i]) begin
                seq.add(r_trans_q[i]);
            end

            env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
            env.build();
            env.run();

            repeat(10) @(posedge clk);
            #300ps top.pc_start_pulse[0] <= 1;
            @(posedge clk);
            #300ps top.pc_start_pulse[0] <= 0;
            while(1) begin
                @(posedge clk);
                if (top.pcfg_g2f_interrupt_pulse[0]) begin
                    break;
                end
            end

            repeat(50) @(posedge clk);
            for (int i=0; i<num; i++) begin
                cfg_addr = cfg_addr_arr[i] + 16;
                cfg_data = cfg_data_arr[i];
                cfg_check(cfg_addr, cfg_data);
            end

            repeat(30) @(posedge clk);
        end

        // //=============================================================================
        // // sram read/write
        // //=============================================================================
        // seq.empty();
        // m_cnt = 0;
        // m_trans_q[m_cnt++] = new('h10, 100);
        // m_trans_q[m_cnt++] = new('h10, 100, 1);

        // m_trans_q[m_cnt++] = new('h40000, 100);
        // m_trans_q[m_cnt++] = new('h40000, 100, 1);

        // foreach(m_trans_q[i]) begin
        //     seq.add(m_trans_q[i]);
        // end

        // env = new(seq, p_ifc, r_ifc, s_ifc, m_ifc);
        // env.build();
        // env.run();
        // repeat(300) @(posedge clk);
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
        addr_dic["PC_DMA_BS_RELOCATION"]        = 'hB0;
    end

    function void empty_queues;
        // empty queue
        seq.empty();
        p_trans_q.delete();
        r_trans_q.delete();
        m_trans_q.delete();
        s_trans_q.delete();
        p_cnt = 0;
        r_cnt = 0;
        m_cnt = 0;
        s_cnt = 0;
        cfg_addr_arr.delete();
        cfg_data_arr.delete();
        data64_arr.delete();
        data16_arr.delete();
    endfunction

    function void cfg_check(input bit[CGRA_CFG_ADDR_WIDTH-1:0] cfg_addr, bit[CGRA_CFG_DATA_WIDTH-1:0] cfg_data);
        bit[7:0] col_id;
        bit[7:0] reg_id;
        int cgra_reg; 
        col_id = cfg_addr[7:0];
        reg_id = cfg_addr[15:8];
        cgra_reg = top.cgra.reg_file[col_id][reg_id];
        assert(cgra_reg == cfg_data) 
        else $error("cgra register value: %h, expected value: %h", cgra_reg, cfg_data);
    endfunction


    task jtag_write (input bit [CGRA_CFG_ADDR_WIDTH-1:0] addr, bit [CGRA_CFG_DATA_WIDTH-1:0] data);
        $display("[JTAG-WR] @%0t: addr: 0x%0h, data: 0x%0h", $time, addr, data);
        @(posedge clk);
        top.cgra_cfg_jtag_gc2glb_wr_en <= 1;
        top.cgra_cfg_jtag_gc2glb_rd_en <= 0;
        top.cgra_cfg_jtag_gc2glb_addr <= addr;
        top.cgra_cfg_jtag_gc2glb_data <= data;
        @(posedge clk);
        top.cgra_cfg_jtag_gc2glb_wr_en <= 0;
        top.cgra_cfg_jtag_gc2glb_rd_en <= 0;
        top.cgra_cfg_jtag_gc2glb_addr <= 0;
        top.cgra_cfg_jtag_gc2glb_data <= 0;
        repeat(30) @(posedge clk);
    endtask

    task jtag_read (input bit [CGRA_CFG_ADDR_WIDTH-1:0] addr, bit [CGRA_CFG_DATA_WIDTH-1:0] data);
        @(posedge clk);
        top.cgra_cfg_jtag_gc2glb_wr_en <= 0;
        top.cgra_cfg_jtag_gc2glb_rd_en <= 1;
        top.cgra_cfg_jtag_gc2glb_addr <= addr;
        top.cgra_cfg_jtag_gc2glb_data <= 0;
        repeat(10) @(posedge clk);
        top.cgra_cfg_jtag_gc2glb_wr_en <= 0;
        top.cgra_cfg_jtag_gc2glb_rd_en <= 0;
        top.cgra_cfg_jtag_gc2glb_addr <= 0;
        top.cgra_cfg_jtag_gc2glb_data <= 0;
        fork : jtag_timeout
            begin
                while (1) begin
                    @(posedge clk);
                    if (top.cgra_cfg_rd_data_valid) begin
                        if (data != top.cgra_cfg_rd_data) begin
                            $error("[JTAG-FAIL] #JTAG addr: 0x%0h, data expected: 0x%0h, data real: 0x%0h", addr, data, top.cgra_cfg_rd_data);
                        end
                        $display("[JTAG-RD] @%0t: addr: 0x%0h, data: 0x%0h", $time, addr, data);
                        break;
                    end
                end
            end
            begin
                repeat (32) @(posedge clk);
                $display("@%0t: %m ERROR: jtag read timeout ", $time);
            end
        join_any
        disable fork;
        @(posedge clk);
    endtask

    // function void write_glb(input bit [GLB_ADDR_WIDTH-1:0] addr, input bit [BANK_DATA_WIDTH-1:0] data);
    //     bit [TILE_SEL_ADDR_WIDTH-1:0] tile_id;
    //     bit bank_id;
    //     bit [SRAM_MACRO_SEL_WIDTH-1:0] sram_id;
    //     bit [SRAM_MACRO_ADDR_WIDTH-1:0] sram_addr;
    //     tile_id = addr[GLB_ADDR_WIDTH-1 -: TILE_SEL_ADDR_WIDTH];
    //     bank_id = addr[GLB_ADDR_WIDTH-TILE_SEL_ADDR_WIDTH-1 -: 1];
    //     sram_id = addr[GLB_ADDR_WIDTH-TILE_SEL_ADDR_WIDTH-1-1 -: SRAM_MACRO_SEL_WIDTH];
    //     sram_addr = addr[0 +: SRAM_MACRO_ADDR_WIDTH];
    //     top.dut.glb_tile_gen[tile_id].glb_tile.glb_tile_int.glb_core.glb_bank_gen[bank_id].glb_bank_memory.glb_bank_sram_gen.sram_gen[sram_id].data_array[sram_addr] = data;
    // endfunction


endprogram
