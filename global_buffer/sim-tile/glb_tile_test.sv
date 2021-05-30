/*=============================================================================
** Module: glb_tile_test.sv
** Description:
**              simple top testbench for glb-tile
** Author: Taeyoung Kong
** Change history:  05/28/2021 - Implement first version of testbench
**===========================================================================*/
program glb_tile_test (
    // LEFT
    input  logic                           clk,
    output logic                           clk_en,
    input  logic                           reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0] glb_tile_id,

    // proc e2w
    output logic                         proc_wr_en_e2w_esti,
    output logic [BANK_DATA_WIDTH/8-1:0] proc_wr_strb_e2w_esti,
    output logic [GLB_ADDR_WIDTH-1:0]    proc_wr_addr_e2w_esti,
    output logic [BANK_DATA_WIDTH-1:0]   proc_wr_data_e2w_esti,
    output logic                         proc_rd_en_e2w_esti,
    output logic [GLB_ADDR_WIDTH-1:0]    proc_rd_addr_e2w_esti,
    output logic [BANK_DATA_WIDTH-1:0]   proc_rd_data_e2w_esti,
    output logic                         proc_rd_data_valid_e2w_esti,
    input  logic                         proc_wr_en_e2w_wsto,
    input  logic [BANK_DATA_WIDTH/8-1:0] proc_wr_strb_e2w_wsto,
    input  logic [GLB_ADDR_WIDTH-1:0]    proc_wr_addr_e2w_wsto,
    input  logic [BANK_DATA_WIDTH-1:0]   proc_wr_data_e2w_wsto,
    input  logic                         proc_rd_en_e2w_wsto,
    input  logic [GLB_ADDR_WIDTH-1:0]    proc_rd_addr_e2w_wsto,
    input  logic [BANK_DATA_WIDTH-1:0]   proc_rd_data_e2w_wsto,
    input  logic                         proc_rd_data_valid_e2w_wsto,

    // proc w2e
    output logic                         proc_wr_en_w2e_wsti,
    output logic [BANK_DATA_WIDTH/8-1:0] proc_wr_strb_w2e_wsti,
    output logic [GLB_ADDR_WIDTH-1:0]    proc_wr_addr_w2e_wsti,
    output logic [BANK_DATA_WIDTH-1:0]   proc_wr_data_w2e_wsti,
    output logic                         proc_rd_en_w2e_wsti,
    output logic [GLB_ADDR_WIDTH-1:0]    proc_rd_addr_w2e_wsti,
    output logic [BANK_DATA_WIDTH-1:0]   proc_rd_data_w2e_wsti,
    output logic                         proc_rd_data_valid_w2e_wsti,
    input  logic                         proc_wr_en_w2e_esto,
    input  logic [BANK_DATA_WIDTH/8-1:0] proc_wr_strb_w2e_esto,
    input  logic [GLB_ADDR_WIDTH-1:0]    proc_wr_addr_w2e_esto,
    input  logic [BANK_DATA_WIDTH-1:0]   proc_wr_data_w2e_esto,
    input  logic                         proc_rd_en_w2e_esto,
    input  logic [GLB_ADDR_WIDTH-1:0]    proc_rd_addr_w2e_esto,
    input  logic [BANK_DATA_WIDTH-1:0]   proc_rd_data_w2e_esto,
    input  logic                         proc_rd_data_valid_w2e_esto,

    // configuration of glb from glc
    input  logic                      if_cfg_est_m_wr_en,
    input  logic                      if_cfg_est_m_wr_clk_en,
    input  logic [AXI_ADDR_WIDTH-1:0] if_cfg_est_m_wr_addr,
    input  logic [AXI_DATA_WIDTH-1:0] if_cfg_est_m_wr_data,
    input  logic                      if_cfg_est_m_rd_en,
    input  logic                      if_cfg_est_m_rd_clk_en,
    input  logic [AXI_ADDR_WIDTH-1:0] if_cfg_est_m_rd_addr,
    output logic [AXI_DATA_WIDTH-1:0] if_cfg_est_m_rd_data,
    output logic                      if_cfg_est_m_rd_data_valid,

    output logic                      if_cfg_wst_s_wr_en,
    output logic                      if_cfg_wst_s_wr_clk_en,
    output logic [AXI_ADDR_WIDTH-1:0] if_cfg_wst_s_wr_addr,
    output logic [AXI_DATA_WIDTH-1:0] if_cfg_wst_s_wr_data,
    output logic                      if_cfg_wst_s_rd_en,
    output logic                      if_cfg_wst_s_rd_clk_en,
    output logic [AXI_ADDR_WIDTH-1:0] if_cfg_wst_s_rd_addr,
    input  logic [AXI_DATA_WIDTH-1:0] if_cfg_wst_s_rd_data,
    input  logic                      if_cfg_wst_s_rd_data_valid
);

    initial begin
        initialize();
        if ($test$plusargs("TEST_GLB_MEM_SIMPLE")) begin
            logic [BANK_DATA_WIDTH-1:0] data_arr [];
            logic [BANK_DATA_WIDTH-1:0] data_arr_out [];
            static int size = 8;
            data_arr = new [size];
            data_arr_out = new [size];
            foreach(data_arr[i]) begin
                data_arr[i] = i;
            end
            proc_write_burst(0, data_arr); 
            proc_read_burst(0, data_arr_out); 
            compare_64b_arr(data_arr, data_arr_out);
        end
        if ($test$plusargs("TEST_GLB_CFG")) begin
            logic [AXI_DATA_WIDTH-1:0] cfg_data;
            logic [AXI_DATA_WIDTH-1:0] cfg_data_out;
            int tile_id;
            if (!($value$plusargs("CFG_TEST_TILE_ID=%0d", tile_id)))
                tile_id = 0;

            cfg_data = 'hff;
            glb_cfg_write(((tile_id << 8) | `GLB_CFG_TILE_CTRL), cfg_data);
            glb_cfg_read(((tile_id << 8) | `GLB_CFG_TILE_CTRL), cfg_data_out);
            compare_cfg(cfg_data, cfg_data_out);

            cfg_data = 'hfff;
            glb_cfg_write(((tile_id << 8) | `GLB_CFG_LATENCY), cfg_data);
            glb_cfg_read(((tile_id << 8) | `GLB_CFG_LATENCY), cfg_data_out);
            compare_cfg(cfg_data, cfg_data_out);

            cfg_data = 'hff;
            glb_cfg_write(((tile_id << 8) | `GLB_CFG_ST_DMA_HEADER_0_START_ADDR), cfg_data);
            glb_cfg_read(((tile_id << 8) | `GLB_CFG_ST_DMA_HEADER_0_START_ADDR), cfg_data_out);
            compare_cfg(cfg_data, cfg_data_out);
        end
        // if ($test$plusargs("TEST_GLB_G2F_STREAM")) begin
        //     static int tile_id = 0;
        //     static int start_addr = 'h40000 * tile_id;
        //     logic [CGRA_DATA_WIDTH-1:0] cgra_data_arr [];
        //     logic [CGRA_DATA_WIDTH-1:0] cgra_data_arr_out [];
        //     logic [BANK_DATA_WIDTH-1:0] glb_data_arr [];
        //     static int size = 8;
        //     cgra_data_arr = new [size];
        //     cgra_data_arr_out = new [size];
        //     foreach(cgra_data_arr[i]) begin
        //         cgra_data_arr[i] = i;
        //     end
        //     convert_16b_to_64b(cgra_data_arr, glb_data_arr); 
        //     proc_write_burst(start_addr, glb_data_arr);
        //     g2f_dma_configure(tile_id, start_addr, size);
        //     g2f_start(tile_id, cgra_data_arr_out);
        //     compare_16b_arr(cgra_data_arr, cgra_data_arr_out);
        // end
        // if ($test$plusargs("TEST_GLB_F2G_STREAM")) begin
        //     static int tile_id = 0;
        //     static int start_addr = 'h40000 * tile_id;
        //     logic [CGRA_DATA_WIDTH-1:0] cgra_data_arr [];
        //     logic [BANK_DATA_WIDTH-1:0] glb_data_arr[];
        //     logic [BANK_DATA_WIDTH-1:0] glb_data_arr_out [];
        //     static int size = 8;
        //     cgra_data_arr = new [size];
        //     foreach(cgra_data_arr[i]) begin
        //         cgra_data_arr[i] = i;
        //     end
        //     f2g_dma_configure(tile_id, start_addr, size);
        //     f2g_start(tile_id, cgra_data_arr);

        //     convert_16b_to_64b(cgra_data_arr, glb_data_arr); 
        //     glb_data_arr_out = new[glb_data_arr.size()];
        //     proc_read_burst(start_addr, glb_data_arr_out);
        //     compare_64b_arr(glb_data_arr, glb_data_arr_out);
        // end
        // if ($test$plusargs("TEST_PCFG_STREAM")) begin
        //     static int tile_id = 0;
        //     static int start_addr = 'h40000 * tile_id;
        //     logic [CGRA_CFG_ADDR_WIDTH+CGRA_CFG_DATA_WIDTH-1:0] bs_arr [];
        //     logic [CGRA_CFG_ADDR_WIDTH+CGRA_CFG_DATA_WIDTH-1:0] bs_arr_out [];
        //     static int size = 8;
        //     bs_arr = new [size];
        //     bs_arr_out = new [size];
        //     foreach(bs_arr[i]) begin
        //         bs_arr[i] = i;
        //     end
        //     proc_write_burst(start_addr, bs_arr);
        //     pcfg_dma_configure(tile_id, start_addr, size);
        //     pcfg_start(tile_id, bs_arr_out);
        //     compare_64b_arr(bs_arr, bs_arr_out);
        // end
    end

    task initialize();
        // proc
        proc_wr_en_e2w_esti <= 0;
        proc_wr_strb_e2w_esti <= 0;
        proc_wr_addr_e2w_esti <= 0;
        proc_wr_data_e2w_esti <= 0;
        proc_rd_en_e2w_esti <= 0;
        proc_rd_addr_e2w_esti <= 0;
        proc_rd_data_e2w_esti <= 0;
        proc_rd_data_valid_e2w_esti <= 0;

        proc_wr_en_w2e_wsti <= 0;
        proc_wr_strb_w2e_wsti <= 0;
        proc_wr_addr_w2e_wsti <= 0;
        proc_wr_data_w2e_wsti <= 0;
        proc_rd_en_w2e_wsti <= 0;
        proc_rd_addr_w2e_wsti <= 0;
        proc_rd_data_w2e_wsti <= 0;
        proc_rd_data_valid_w2e_wsti <= 0;
        
        // wait for reset clear
        wait (reset == 0);
        repeat(10) @(posedge clk);
        $display("Initialization done");
    endtask

    // task pcfg_dma_configure(input int tile_id, [AXI_DATA_WIDTH-1:0] start_addr, [AXI_DATA_WIDTH-1:0] num_word);
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_TILE_CTRL, (1 << 10));
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_PC_DMA_HEADER_0_START_ADDR, start_addr);
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_PC_DMA_HEADER_0_NUM_CFG, num_word);
    // endtask

    // task g2f_dma_configure(input int tile_id, [AXI_DATA_WIDTH-1:0] start_addr, [AXI_DATA_WIDTH-1:0] num_word);
    //     // glb_cfg_write((tile_id << 8) + `GLB_CFG_TILE_CTRL, ((1 << 6) | (2'b01 << 2)));
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_TILE_CTRL, ((1 << 6) | (2'b01 << 2)));
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_LD_DMA_HEADER_0_START_ADDR, start_addr);
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_LD_DMA_HEADER_0_ITER_CTRL_0, ((num_word << 10) | (1 << 0)));
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_LD_DMA_HEADER_0_VALIDATE, 1);
    // endtask

    // task f2g_dma_configure(input int tile_id, [AXI_DATA_WIDTH-1:0] start_addr, [AXI_DATA_WIDTH-1:0] num_word);
    //     // glb_cfg_write((tile_id << 8) + `GLB_CFG_TILE_CTRL, ((1 << 8) | (2'b10 << 4)));
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_TILE_CTRL, ((1 << 8) | (2'b10 << 4)));
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_ST_DMA_HEADER_0_START_ADDR, start_addr);
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_ST_DMA_HEADER_0_NUM_WORDS, num_word);
    //     glb_cfg_write((tile_id << 8) + `GLB_CFG_ST_DMA_HEADER_0_VALIDATE, 1);
    // endtask

    task glb_cfg_write(input [AXI_ADDR_WIDTH-1:0] addr, input [AXI_DATA_WIDTH-1:0] data);
        repeat(5) @(posedge clk);
        #(`CLK_PERIOD*0.3)
        if_cfg_wst_s_wr_en <= 1;
        if_cfg_wst_s_wr_clk_en <= 1;
        if_cfg_wst_s_wr_addr <= addr;
        if_cfg_wst_s_wr_data <= data;
        @(posedge clk);
        #(`CLK_PERIOD*0.3)
        if_cfg_wst_s_wr_en <= 0;
        if_cfg_wst_s_wr_clk_en <= 0;
        if_cfg_wst_s_wr_addr <= 0;
        if_cfg_wst_s_wr_data <= 0;
        repeat(5) @(posedge clk);
    endtask

    task glb_cfg_read(input [AXI_ADDR_WIDTH-1:0] addr, output [AXI_DATA_WIDTH-1:0] data);
        repeat(5) @(posedge clk);
        #(`CLK_PERIOD*0.3)
        if_cfg_wst_s_rd_en <= 1;
        if_cfg_wst_s_rd_clk_en <= 1;
        if_cfg_wst_s_rd_addr <= addr;
        @(posedge clk);
        #(`CLK_PERIOD*0.3)
        if_cfg_wst_s_rd_en <= 0;
        if_cfg_wst_s_rd_clk_en <= 0;
        if_cfg_wst_s_rd_addr <= 0;
        fork : glb_cfg_read_timeout
        begin
            while (1) begin
                @(posedge clk);
                if (if_cfg_wst_s_rd_data_valid) begin
                    data = if_cfg_wst_s_rd_data;
                    break;
                end
            end
        end
        begin
            repeat (50) @(posedge clk);
            $display("@%0t: %m ERROR: glb cfg read timeout ", $time);
        end
        join_any
        disable fork;
        repeat(5) @(posedge clk);
    endtask

    task automatic proc_write_burst(input [GLB_ADDR_WIDTH-1:0] addr, ref [BANK_DATA_WIDTH-1:0] data[]);
        int size = data.size();
        repeat(5) @(posedge clk);
        $display("Start glb-mem burst write. addr: 0x%0h, size %0d", addr, size);
        foreach(data[i]) begin
            if ((glb_tile_id % 2) == 0) begin
                proc_write_w2e(addr + 8*i, data[i]);
            end else begin
                proc_write_e2w(addr + 8*i, data[i]);
            end
        end
        #(`CLK_PERIOD*0.3)
        proc_wr_en_w2e_wsti <= 0;
        proc_wr_strb_w2e_wsti <= 0;
        proc_wr_en_e2w_esti <= 0;
        proc_wr_strb_e2w_esti <= 0;
        $display("Finish glb-mem burst write");
        repeat(5) @(posedge clk);
    endtask

    task automatic proc_write_w2e(input [GLB_ADDR_WIDTH-1:0] addr, [BANK_DATA_WIDTH-1:0] data);
        #(`CLK_PERIOD*0.3)
        proc_wr_en_w2e_wsti <= 1;
        proc_wr_strb_w2e_wsti <= {(BANK_DATA_WIDTH/8){1'b1}};
        proc_wr_addr_w2e_wsti <= addr;
        proc_wr_data_w2e_wsti <= data;
        @(posedge clk);
    endtask

    task automatic proc_write_e2w(input [GLB_ADDR_WIDTH-1:0] addr, [BANK_DATA_WIDTH-1:0] data);
        #(`CLK_PERIOD*0.3)
        proc_wr_en_e2w_esti <= 1;
        proc_wr_strb_e2w_esti <= {(BANK_DATA_WIDTH/8){1'b1}};
        proc_wr_addr_e2w_esti <= addr;
        proc_wr_data_e2w_esti <= data;
        @(posedge clk);
    endtask

    task automatic proc_read_burst(input [GLB_ADDR_WIDTH-1:0] addr, ref [BANK_DATA_WIDTH-1:0] data[]);
        int size = data.size();
        repeat(5) @(posedge clk);
        $display("Start glb-mem burst read. addr: 0x%0h, size %0d", addr, size);
        fork : proc_read
        begin
            for(int i = 0; i < size; i++) begin
                #(`CLK_PERIOD*0.3)
                if ((glb_tile_id % 2) == 0) begin
                    proc_rd_en_w2e_wsti <= 1;
                    proc_rd_addr_w2e_wsti <= addr + 8*i;
                end else begin
                    proc_rd_en_e2w_esti <= 1;
                    proc_rd_addr_e2w_esti <= addr + 8*i;
                end
                @(posedge clk);
            end
            #(`CLK_PERIOD*0.3)
            proc_rd_en_w2e_wsti <= 0;
            proc_rd_en_e2w_esti <= 0;
        end
        begin
            fork : proc_read_timeout
            begin
                int cnt = 0;
                while (1) begin
                    @(posedge clk);
                    #(`CLK_PERIOD*0.3)
                    if ((glb_tile_id % 2) == 0) begin
                        if (proc_rd_data_valid_w2e_esto) begin
                            data[cnt] = proc_rd_data_w2e_esto;
                            cnt = cnt + 1;
                            if (cnt == size) break;
                        end
                    end else begin
                        if (proc_rd_data_valid_e2w_wsto) begin
                            data[cnt] = proc_rd_data_e2w_wsto;
                            cnt = cnt + 1;
                            if (cnt == size) break;
                        end
                    end
                end
            end
            begin
                repeat (size + 100) @(posedge clk);
                $display("@%0t: %m ERROR: glb-mem burst read timeout ", $time);
            end
            join_any
            disable fork;
        end
        join
        repeat(5) @(posedge clk);
        $display("Finish glb-mem burst read");
    endtask

    // task automatic g2f_start(input int tile_id, ref [CGRA_DATA_WIDTH-1:0] cgra_data_arr_out []);
    //     int cgra_data_arr_size = cgra_data_arr_out.size();
    //     $display("g2f streaming start. tile: %0d", tile_id);
    //     repeat(5) @(posedge clk);
    //     strm_start_pulse <= (1 << tile_id);
    //     @(posedge  clk);
    //     strm_start_pulse <= 0;

    //     fork : g2f_start
    //     begin
    //         fork : data_valid_timeout
    //         begin
    //             wait(stream_data_valid_g2f[tile_id][0]);
    //             @(posedge clk);
    //             for(int i=0; i < cgra_data_arr_size; i++) begin
    //                 cgra_data_arr_out[i] = stream_data_g2f[tile_id][0];
    //                 @(posedge clk);
    //             end
    //         end
    //         begin
    //             repeat (cgra_data_arr_size + 30) @(posedge clk);
    //             $display("@%0t: %m ERROR: glb stream g2f valid timeout ", $time);
    //         end
    //         join_any
    //         disable fork;
    //     end
    //     begin
    //         fork : interrupt_timeout
    //         begin
    //             wait(strm_g2f_interrupt_pulse[tile_id]);
    //         end
    //         begin
    //             repeat (cgra_data_arr_size + 30) @(posedge clk);
    //             $display("@%0t: %m ERROR: glb stream g2f interrupt timeout ", $time);
    //         end
    //         join_any
    //         disable fork;
    //     end
    //     join
    //     repeat(5) @(posedge clk);
    //     $display("g2f streaming done.");
    // endtask

    // task automatic f2g_start(input int tile_id, ref [CGRA_DATA_WIDTH-1:0] cgra_data_arr []);
    //     int cgra_data_arr_size = cgra_data_arr.size();
    //     $display("f2g streaming start. tile: %0d", tile_id);
    //     repeat(5) @(posedge clk);
    //     for(int i=0; i < cgra_data_arr_size; i++) begin
    //         stream_data_f2g[tile_id][1] <= cgra_data_arr[i];
    //         stream_data_valid_f2g[tile_id][1] <= 1;
    //         @(posedge clk);
    //     end
    //     stream_data_f2g[tile_id][1] <= 0;
    //     stream_data_valid_f2g[tile_id][1] <= 0;

    //     fork : interrupt_timeout
    //     begin
    //         wait(strm_f2g_interrupt_pulse[tile_id]);
    //     end
    //     begin
    //         repeat (30) @(posedge clk);
    //         $display("@%0t: %m ERROR: glb stream f2g interrupt timeout ", $time);
    //     end
    //     join_any
    //     disable fork;
    //     repeat(5) @(posedge clk);
    //     $display("f2g streaming done.");
    // endtask

    // task automatic pcfg_start(input int tile_id, ref [CGRA_CFG_ADDR_WIDTH+CGRA_CFG_DATA_WIDTH-1:0] bs_arr_out []);
    //     int bs_size = bs_arr_out.size();
    //     $display("pcfg streaming start. tile: %0d, num_bs: %0d", tile_id, bs_size);
    //     repeat(5) @(posedge clk);
    //     pc_start_pulse <= (1 << tile_id);
    //     @(posedge  clk);
    //     pc_start_pulse <= 0;

    //     fork : pcfg_start
    //     begin
    //         fork : data_valid_timeout
    //         begin
    //             wait(cgra_cfg_g2f_cfg_wr_en[tile_id][0]);
    //             for(int i=0; i < bs_size; i++) begin
    //                 bs_arr_out[i] = {cgra_cfg_g2f_cfg_addr[tile_id][0], cgra_cfg_g2f_cfg_data[tile_id][0]};
    //                 @(posedge clk);
    //             end
    //         end
    //         begin
    //             repeat (bs_size + 30) @(posedge clk);
    //             $display("@%0t: %m ERROR: glb stream pcfg timeout ", $time);
    //         end
    //         join_any
    //         disable fork;
    //     end
    //     begin
    //         fork : interrupt_timeout
    //         begin
    //             wait(pcfg_g2f_interrupt_pulse[tile_id]);
    //         end
    //         begin
    //             repeat (bs_size + 50) @(posedge clk);
    //             $display("@%0t: %m ERROR: glb stream pcfg interrupt timeout ", $time);
    //         end
    //         join_any
    //         disable fork;
    //     end
    //     join
    //     repeat(5) @(posedge clk);
    //     $display("pcfg streaming done.");
    // endtask

    function automatic int compare_64b_arr(ref [63:0] data_arr_0 [], ref [63:0] data_arr_1 []);
        int size_0 = data_arr_0.size();
        int size_1 = data_arr_1.size();
        int err;
        if (size_0 != size_1) begin
            $display("Data array size is different. data_arr_0: %0d, data_arr_1: %0d", size_0, size_1);
            err++;
        end
        foreach(data_arr_0[i]) begin
            if(data_arr_0[i] !== data_arr_1[i]) begin
                $display("Data array different. index: %0d, data_arr_0: 0x%0h, data_arr_1: 0x%0h", i, data_arr_0[i], data_arr_1[i]);
                err++;
            end
            else begin
                $display("Data array same. index: %0d, data_arr_0: 0x%0h, data_arr_1: 0x%0h", i, data_arr_0[i], data_arr_1[i]);
            end
        end
        if (err > 0) begin
            return 1;
        end
        $display("Two data array are same");
        return 0;
    endfunction

    function automatic int compare_16b_arr(ref [15:0] data_arr_0 [], ref [15:0] data_arr_1 []);
        int size_0 = data_arr_0.size();
        int size_1 = data_arr_1.size();
        int err;
        if (size_0 != size_1) begin
            $display("Data array size is different. data_arr_0: %0d, data_arr_1: %0d", size_0, size_1);
            err++;
        end
        foreach(data_arr_0[i]) begin
            if(data_arr_0[i] !== data_arr_1[i]) begin
                $display("Data array different. index: %0d, data_arr_0: %0d, data_arr_1: %0d", i, data_arr_0[i], data_arr_1[i]);
                err++;
            end
            else begin
                $display("Data array same. index: %0d, data_arr_0: %0d, data_arr_1: %0d", i, data_arr_0[i], data_arr_1[i]);
            end
        end
        if (err > 0) begin
            return 1;
        end
        $display("Two data array are same");
        return 0;
    endfunction

    function int compare_cfg(logic [BANK_DATA_WIDTH-1:0] cfg_0, logic [AXI_DATA_WIDTH-1:0] cfg_1); 
        if(cfg_0 !== cfg_1) begin
            $display("cfg data is different. cfg_0: 0x%0h, cfg_1: 0x%0h", cfg_0, cfg_1);
            return 1;
        end
        $display("Two cfg data are same. cfg_0: 0x%0h, cfg_1: 0x%0h", cfg_0, cfg_1);
        return 0;
    endfunction

    function automatic void convert_16b_to_64b(ref [15:0] data_in [], ref [63:0] data_out []);
        int num_data_in = data_in.size();
        int num_data_out = (num_data_in + 3) / 4;
        data_out = new [num_data_out];
        for(int i=0; i < num_data_in; i=i+4) begin
            if (i == (num_data_in-1)) begin
                if (num_data_in % 4 == 1) begin
                    data_out[i/4] = {{48{1'b1}}, data_in[i]};
                end
                else if (num_data_in % 4 == 2) begin
                    data_out[i/4] = {{32{1'b1}}, data_in[i+1], data_in[i]};
                end
                else if (num_data_in % 4 == 3) begin
                    data_out[i/4] = {{16{1'b1}}, data_in[i+2], data_in[i+1], data_in[i]};
                end
                else begin
                    data_out[i/4] = {data_in[i+3], data_in[i+2], data_in[i+1], data_in[i]};
                end
            end
            data_out[i/4] = {data_in[i+3], data_in[i+2], data_in[i+1], data_in[i]};
        end
    endfunction

    function automatic void convert_64b_to_16b(ref [63:0] data_in [], ref [15:0] data_out []);
        int num_data_in = data_in.size();
        int num_data_out = num_data_in * 4;
        data_out = new [num_data_out];
        for(int i=0; i < num_data_in; i++) begin
            data_out[i*4 + 0] = data_in[i][ 0+:16];
            data_out[i*4 + 1] = data_in[i][16+:16];
            data_out[i*4 + 2] = data_in[i][32+:16];
            data_out[i*4 + 3] = data_in[i][48+:16];
        end
    endfunction

endprogram
