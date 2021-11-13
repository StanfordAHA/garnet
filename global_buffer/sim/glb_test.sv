/*=============================================================================
** Module: glb_test.sv
** Description:
**              simple top testbench for glb
** Author: Taeyoung Kong
** Change history:  05/22/2021 - Implement first version of testbench
**===========================================================================*/
program glb_test (
    // LEFT
    input  logic                     clk,
    input  logic                     reset,
    output logic [NUM_GLB_TILES-1:0] stall,
    output logic [NUM_GLB_TILES-1:0] cgra_stall_in,

    // proc
    output logic                         proc_wr_en,
    output logic [BANK_DATA_WIDTH/8-1:0] proc_wr_strb,
    output logic [GLB_ADDR_WIDTH-1:0]    proc_wr_addr,
    output logic [BANK_DATA_WIDTH-1:0]   proc_wr_data,
    output logic                         proc_rd_en,
    output logic [GLB_ADDR_WIDTH-1:0]    proc_rd_addr,
    input  logic [BANK_DATA_WIDTH-1:0]   proc_rd_data,
    input  logic                         proc_rd_data_valid,

    // configuration of glb from glc
    output logic                      if_cfg_wr_en,
    output logic [AXI_ADDR_WIDTH-1:0] if_cfg_wr_addr,
    output logic [AXI_DATA_WIDTH-1:0] if_cfg_wr_data,
    output logic                      if_cfg_rd_en,
    output logic [AXI_ADDR_WIDTH-1:0] if_cfg_rd_addr,
    input  logic [AXI_DATA_WIDTH-1:0] if_cfg_rd_data,
    input  logic                      if_cfg_rd_data_valid,

    // configuration of sram from glc
    output logic                      if_sram_cfg_wr_en,
    output logic [GLB_ADDR_WIDTH-1:0] if_sram_cfg_wr_addr,
    output logic [AXI_DATA_WIDTH-1:0] if_sram_cfg_wr_data,
    output logic                      if_sram_cfg_rd_en,
    output logic [GLB_ADDR_WIDTH-1:0] if_sram_cfg_rd_addr,
    input  logic [AXI_DATA_WIDTH-1:0] if_sram_cfg_rd_data,
    input  logic                      if_sram_cfg_rd_data_valid,

    // cgra configuration from global controller
    output logic                           cgra_cfg_jtag_gc2glb_wr_en,
    output logic                           cgra_cfg_jtag_gc2glb_rd_en,
    output logic [CGRA_CFG_ADDR_WIDTH-1:0] cgra_cfg_jtag_gc2glb_addr,
    output logic [CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_jtag_gc2glb_data,

    // control pulse
    output logic [NUM_GLB_TILES-1:0] strm_start_pulse,
    output logic [NUM_GLB_TILES-1:0] pcfg_start_pulse,
    input  logic [NUM_GLB_TILES-1:0] strm_g2f_interrupt_pulse,
    input  logic [NUM_GLB_TILES-1:0] strm_f2g_interrupt_pulse,
    input  logic [NUM_GLB_TILES-1:0] pcfg_g2f_interrupt_pulse,

    // cgra configuration to cgra
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_stall,
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_cfg_g2f_cfg_wr_en,
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_cfg_g2f_cfg_rd_en,
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_ADDR_WIDTH-1:0] cgra_cfg_g2f_cfg_addr,
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_g2f_cfg_data
);
	string timestamp_folder;

    int tile_offset = 1 << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH);
    int tile_id = 0;
    bit [NUM_GLB_TILES-1:0] tile_id_mask = 0;

    initial begin
        initialize();

        if ($test$plusargs("TEST_GLB_MEM_SIMPLE")) begin
            static string test_name = "TEST_GLB_MEM_SIMPLE";
            logic [BANK_DATA_WIDTH-1:0] data_arr [];
            logic [BANK_DATA_WIDTH-1:0] data_arr_out [];
            static int size = 256;

            tile_id = 0;
            tile_id_mask = 0;

            $display("\n**** TEST_GLB_MEM_W/R START ****");

            data_arr = new [size];
            data_arr_out = new [size];
            foreach(data_arr[i]) begin
                data_arr[i] = i;
            end

            // start
            timestamp(test_name);
            proc_write_burst(0, data_arr); 
            timestamp(test_name);
            // end

            proc_read_burst(0, data_arr_out); 
            void'(compare_64b_arr(data_arr, data_arr_out));

            $display("**** TEST_GLB_MEM_W/R END ****\n");
        end

        if ($test$plusargs("TEST_GLB_CFG")) begin
            static int err = 0;
            logic [AXI_DATA_WIDTH-1:0] cfg_data;
            logic [AXI_DATA_WIDTH-1:0] cfg_data_out;

            $display("\n**** TEST_GLB_CFG_W/R START ****");
            for(int i=0; i < NUM_GLB_TILES; i++) begin
                // TODO: Read from glb.pair test
                cfg_data = {`GLB_DATA_NETWORK_R_MSB{1'b1}};
                glb_cfg_write(((i << 8) | `GLB_DATA_NETWORK_R), cfg_data);
                glb_cfg_read(((i << 8) | `GLB_DATA_NETWORK_R), cfg_data_out);
                err += compare_cfg(cfg_data, cfg_data_out);
            end
            for(int i=0; i < NUM_GLB_TILES; i++) begin
                // TODO: Read from glb.pair test
                cfg_data = {`GLB_DATA_NETWORK_R_MSB{1'b0}};
                glb_cfg_write(((i << 8) | `GLB_DATA_NETWORK_R), cfg_data);
                glb_cfg_read(((i << 8) | `GLB_DATA_NETWORK_R), cfg_data_out);
                err += compare_cfg(cfg_data, cfg_data_out);
            end
            if (err > 0) begin
                $error("glb configuration read/write fail");
            end else begin
                $display("glb configuration read/write success");
            end

            $display("**** TEST_GLB_CFG_W/R END ****\n");
        end

        if ($test$plusargs("TEST_GLB_G2F_STREAM")) begin
            static string test_name = "TEST_GLB_G2F";
            static int start_addr;
            logic [CGRA_DATA_WIDTH-1:0] cgra_data_arr [];
            logic [CGRA_DATA_WIDTH-1:0] cgra_data_arr_out [];
            logic [BANK_DATA_WIDTH-1:0] glb_data_arr [];
            static int size = 8;

            tile_id = 0;
            tile_id_mask = 0;
            start_addr = tile_offset * tile_id;

            $display("\n**** TEST_GLB_G2F_STREAM START ****");
            cgra_data_arr = new [size];
            cgra_data_arr_out = new [size];
            foreach(cgra_data_arr[i]) begin
                cgra_data_arr[i] = i;
            end
            convert_16b_to_64b(cgra_data_arr, glb_data_arr); 
            proc_write_burst(start_addr, glb_data_arr);
            g2f_dma_configure(tile_id, start_addr, size);

            tile_id_mask = update_tile_mask(tile_id, tile_id_mask);

            // Start
            timestamp(test_name);
            g2f_start(tile_id_mask);
            g2f_run(tile_id, size);
            timestamp(test_name);
            // End

            repeat(10) @(posedge clk);
            read_prr(tile_id, cgra_data_arr_out);
            void'(compare_16b_arr(cgra_data_arr, cgra_data_arr_out));

            $display("**** TEST_GLB_G2F_STREAM END ****\n");
        end

        if ($test$plusargs("TEST_GLB_F2G_STREAM")) begin
            static string test_name = "TEST_GLB_F2G";
            static int start_addr = tile_offset * tile_id;
            logic [CGRA_DATA_WIDTH-1:0] cgra_data_arr [];
            logic [BANK_DATA_WIDTH-1:0] glb_data_arr[];
            logic [BANK_DATA_WIDTH-1:0] glb_data_arr_out [];
            static int size = 8;

            tile_id = 0;
            tile_id_mask = 0;
            start_addr = tile_offset * tile_id;

            $display("\n**** TEST_GLB_F2G_STREAM START ****");

            cgra_data_arr = new [size];
            foreach(cgra_data_arr[i]) begin
                cgra_data_arr[i] = i;
            end
            f2g_dma_configure(tile_id, start_addr, size);

            tile_id_mask = update_tile_mask(tile_id, tile_id_mask);
            write_prr(tile_id, cgra_data_arr);

            // start
            timestamp(test_name);
            f2g_start(tile_id_mask);
            f2g_run(tile_id, size);
            timestamp(test_name);
            // end

            convert_16b_to_64b(cgra_data_arr, glb_data_arr); 
            glb_data_arr_out = new[glb_data_arr.size()];
            proc_read_burst(start_addr, glb_data_arr_out);
            void'(compare_64b_arr(glb_data_arr, glb_data_arr_out));

            $display("**** TEST_GLB_F2G_STREAM END ****\n");
        end

        if ($test$plusargs("TEST_PCFG_STREAM")) begin
            static string test_name = "TEST_GLB_PCFG";
            static int start_addr;
            logic [CGRA_CFG_ADDR_WIDTH+CGRA_CFG_DATA_WIDTH-1:0] bs_arr [];
            static int size = 8;

            tile_id = 0;
            tile_id_mask = 0;
            start_addr = tile_offset * tile_id;

            $display("\n**** TEST_PCFG START ****");
            bs_arr = new [size];
            foreach(bs_arr[i]) begin
                bs_arr[i] = (i << CGRA_CFG_DATA_WIDTH) | i;
            end

            proc_write_burst(start_addr, bs_arr);
            pcfg_dma_configure(tile_id, start_addr, size);

            tile_id_mask = update_tile_mask(tile_id, tile_id_mask);

            // start
            timestamp(test_name);
            pcfg_start(tile_id_mask);
            pcfg_run(tile_id, size);
            timestamp(test_name);
            // end

            void'(read_cgra_cfg(bs_arr));

            $display("**** TEST_PCFG END ****\n");
        end
    end

	task initialize();
        if (!($value$plusargs("TIMESTAMP=%s", timestamp_folder))) begin
			timestamp_folder = "timestamp";
		end

		void'($system($sformatf("rm -rf %s", timestamp_folder)));
		void'($system($sformatf("mkdir %s", timestamp_folder)));

		$display("Timestamp folder is %s", timestamp_folder);

		initialize_signals();

        $display("Initialization done");
	endtask

    task initialize_signals();
        // control
        stall <= 0;
        cgra_stall_in <= 0;
        pcfg_start_pulse <= 0;
        strm_start_pulse <= 0;

        // proc
        proc_wr_en <= 0;
        proc_wr_strb <= 0;
        proc_wr_addr <= 0;
        proc_wr_data <= 0;
        proc_rd_en <= 0;
        proc_rd_addr <= 0;
        
        // cfg ifc
        if_cfg_wr_en <= 0;
        if_cfg_wr_addr <= 0;
        if_cfg_wr_data <= 0;
        if_cfg_rd_en <= 0;
        if_cfg_rd_addr <= 0;

        // sram ifc
        if_sram_cfg_wr_en <= 0;
        if_sram_cfg_wr_addr <= 0;
        if_sram_cfg_wr_data <= 0;
        if_sram_cfg_rd_en <= 0;
        if_sram_cfg_rd_addr <= 0;

        // jtag
        cgra_cfg_jtag_gc2glb_wr_en <= 0;
        cgra_cfg_jtag_gc2glb_rd_en <= 0;
        cgra_cfg_jtag_gc2glb_addr <= 0;
        cgra_cfg_jtag_gc2glb_data <= 0;

        // wait for reset clear
        wait (reset == 0);
        repeat(10) @(posedge clk);
    endtask

    task glb_tile_stall(logic [NUM_GLB_TILES-1:0] tile_sel);

        $display("Glb tiles are stalled");
        stall <= tile_sel;
        repeat(1) @(posedge clk);

    endtask

    task pcfg_dma_configure(input int tile_id, [AXI_DATA_WIDTH-1:0] start_addr, [AXI_DATA_WIDTH-1:0] num_word);
        glb_cfg_write((tile_id << 8) + `GLB_PCFG_DMA_CTRL_R, (1 << `GLB_PCFG_DMA_CTRL_MODE_F_LSB));
        glb_cfg_write((tile_id << 8) + `GLB_PCFG_DMA_HEADER_START_ADDR_R, (start_addr << `GLB_PCFG_DMA_HEADER_START_ADDR_START_ADDR_F_LSB));
        glb_cfg_write((tile_id << 8) + `GLB_PCFG_DMA_HEADER_NUM_CFG_R, (num_word << `GLB_PCFG_DMA_HEADER_NUM_CFG_NUM_CFG_F_LSB));
    endtask

    task g2f_dma_configure(input int tile_id, [AXI_DATA_WIDTH-1:0] start_addr, [AXI_DATA_WIDTH-1:0] num_word);
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_DATA_NETWORK_R, (2'b01 << `GLB_DATA_NETWORK_G2F_MUX_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_LD_DMA_CTRL_R, (1 << `GLB_LD_DMA_CTRL_MODE_F_LSB) | (1 << `GLB_LD_DMA_CTRL_USE_VALID_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_LD_DMA_HEADER_0_START_ADDR_R, (start_addr << `GLB_LD_DMA_HEADER_0_START_ADDR_START_ADDR_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_LD_DMA_HEADER_0_RANGE_0_R, (num_word << `GLB_LD_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_LD_DMA_HEADER_0_STRIDE_0_R, (1 << `GLB_LD_DMA_HEADER_0_STRIDE_0_STRIDE_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_LD_DMA_HEADER_0_VALIDATE_R, (1 << `GLB_LD_DMA_HEADER_0_VALIDATE_VALIDATE_F_LSB));
    endtask

    task f2g_dma_configure(input int tile_id, [AXI_DATA_WIDTH-1:0] start_addr, [AXI_DATA_WIDTH-1:0] num_word);
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_DATA_NETWORK_R, (2'b10 << `GLB_DATA_NETWORK_F2G_MUX_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_ST_DMA_CTRL_R, (1 << `GLB_ST_DMA_CTRL_MODE_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_ST_DMA_HEADER_0_START_ADDR_R, (start_addr << `GLB_ST_DMA_HEADER_0_START_ADDR_START_ADDR_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_ST_DMA_HEADER_0_NUM_WORDS_R, (num_word << `GLB_ST_DMA_HEADER_0_NUM_WORDS_NUM_WORDS_F_LSB));
        glb_cfg_write((tile_id << AXI_ADDR_REG_WIDTH) + `GLB_ST_DMA_HEADER_0_VALIDATE_R, (1 << `GLB_ST_DMA_HEADER_0_VALIDATE_VALIDATE_F_LSB));
    endtask

    task glb_cfg_write(input [AXI_ADDR_WIDTH-1:0] addr, input [AXI_DATA_WIDTH-1:0] data);
        repeat(5) @(posedge clk);
        #(`CLK_PERIOD*0.3)
        if_cfg_wr_en <= 1;
        if_cfg_wr_addr <= addr;
        if_cfg_wr_data <= data;
        @(posedge clk);
        #(`CLK_PERIOD*0.3)
        if_cfg_wr_en <= 0;
        if_cfg_wr_addr <= 0;
        if_cfg_wr_data <= 0;
        repeat(2) @(posedge clk);
    endtask

    task glb_cfg_read(input [AXI_ADDR_WIDTH-1:0] addr, output [AXI_DATA_WIDTH-1:0] data);
        repeat(5) @(posedge clk);
        #(`CLK_PERIOD*0.3)
        if_cfg_rd_en <= 1;
        if_cfg_rd_addr <= addr;
        @(posedge clk);
        #(`CLK_PERIOD*0.3)
        if_cfg_rd_en <= 0;
        if_cfg_rd_addr <= 0;
        fork : glb_cfg_read_timeout
        begin
            while (1) begin
                @(posedge clk);
                if (if_cfg_rd_data_valid) begin
                    data = if_cfg_rd_data;
                    break;
                end
            end
        end
        begin
            repeat (20 + 2 * NUM_GLB_TILES) @(posedge clk);
            $display("@%0t: %m ERROR: glb cfg read timeout ", $time);
        end
        join_any
        disable fork;
        repeat(2) @(posedge clk);
    endtask

    task automatic proc_write_burst(input [GLB_ADDR_WIDTH-1:0] addr, ref [BANK_DATA_WIDTH-1:0] data[]);
        int size = data.size();
        repeat(5) @(posedge clk);
        $display("Start glb-mem burst write. addr: 0x%0h, size %0d", addr, size);
        foreach(data[i]) begin
            proc_write(addr + 8*i, data[i]);
        end
        #(`CLK_PERIOD*0.3)
        proc_wr_en <= 0;
        proc_wr_strb <= 0;
        $display("Finish glb-mem burst write");
        repeat(5) @(posedge clk);
    endtask

    task automatic proc_write(input [GLB_ADDR_WIDTH-1:0] addr, [BANK_DATA_WIDTH-1:0] data);
        #(`CLK_PERIOD*0.3)
        proc_wr_en <= 1;
        proc_wr_strb <= {(BANK_DATA_WIDTH/8){1'b1}};
        proc_wr_addr <= addr;
        proc_wr_data <= data;
        @(posedge clk);
    endtask

    task automatic proc_read_burst(input [GLB_ADDR_WIDTH-1:0] addr, ref [BANK_DATA_WIDTH-1:0] data[]);
        int size = data.size();
        repeat(5) @(posedge clk);
        $display("Start glb-mem burst read. addr: 0x%0h, size %0d", addr, size);
        fork : proc_read
        begin
            for(int i = 0; i < size; i++) begin
                #(`CLK_PERIOD*0.4)
                proc_rd_en <= 1;
                proc_rd_addr <= addr + 8*i;
                @(posedge clk);
            end
            #(`CLK_PERIOD*0.4)
            proc_rd_en <= 0;
        end
        begin
            fork : proc_read_timeout
            begin
                int cnt = 0;
                while (1) begin
                    @(posedge clk);
                    if (proc_rd_data_valid) begin
                        data[cnt] = proc_rd_data;
                        cnt = cnt + 1;
                        if (cnt == size) break;
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

    task automatic g2f_start(input [NUM_GLB_TILES-1:0] tile_id_mask);
        $display("g2f streaming start. tiles: 0x%4h", tile_id_mask);

        // Enable glb2prr
        for (int i=0; i<NUM_PRR; i++) begin
            if (tile_id_mask[i] == 1) begin
                void'($root.top.cgra.glb2prr_on(i));
            end
        end

        repeat(2) @(posedge clk);
        #(`CLK_PERIOD*0.3)
        strm_start_pulse <= tile_id_mask;
        @(posedge  clk);
        #(`CLK_PERIOD*0.3)
        strm_start_pulse <= 0;
    endtask

    task automatic g2f_run(input int tile_id, int max_num_data);
        fork : interrupt_timeout
        begin
            wait(strm_g2f_interrupt_pulse[tile_id]);
            $display("g2f streaming done.");
        end
        begin
            repeat (max_num_data + 30) @(posedge clk);
            $display("@%0t: %m ERROR: glb stream g2f interrupt timeout ", $time);
        end
        join_any
        disable fork;
        @(posedge clk);
    endtask

    function automatic void read_prr(input int prr_id, ref [CGRA_DATA_WIDTH-1:0] cgra_data_arr_out[]);
        if (cgra_data_arr_out.size() != $root.top.cgra.glb2prr_q[prr_id].size) begin
            $error("@%0t: %m FAIL: glb stream to PRR data size is different.\nExpected data size: %d, PRR data size: %d", $time, cgra_data_arr_out.size(), $root.top.cgra.glb2prr_q[prr_id].size);
        end else begin
            foreach($root.top.cgra.glb2prr_q[prr_id][i]) begin
                cgra_data_arr_out[i] = $root.top.cgra.glb2prr_q[prr_id][i];
            end
        end
    endfunction

    function automatic void write_prr(input int prr_id, ref [CGRA_DATA_WIDTH-1:0] cgra_data_arr[]);
        foreach(cgra_data_arr[i]) begin
            $root.top.cgra.prr2glb_q[prr_id][i] = cgra_data_arr[i];
        end
    endfunction

    task automatic f2g_start(input [NUM_GLB_TILES-1:0] tile_id_mask);
        $display("f2g streaming start. tiles: 0x%4h", tile_id_mask);

        // Enable glb2prr
        for (int i=0; i<NUM_PRR; i++) begin
            if (tile_id_mask[i] == 1) begin
                void'($root.top.cgra.prr2glb_on(i));
            end
        end
        @(posedge clk);

    endtask

    task automatic f2g_run(input int tile_id, int max_num_data);
        fork : interrupt_timeout
        begin
            wait(strm_f2g_interrupt_pulse[tile_id]);
            $display("f2g streaming done.");
        end
        begin
            repeat (max_num_data + 30) @(posedge clk);
            $display("@%0t: %m ERROR: cgra stream f2g interrupt timeout ", $time);
        end
        join_any
        disable fork;
        @(posedge clk);
    endtask

    task automatic pcfg_start(input [NUM_GLB_TILES-1:0] tile_id_mask);
        $display("pcfg streaming start. tiles: 0x%4h", tile_id_mask);
        repeat(5) @(posedge clk);
        #(`CLK_PERIOD*0.3)
        pcfg_start_pulse <= tile_id_mask;
        @(posedge clk);
        #(`CLK_PERIOD*0.3)
        pcfg_start_pulse <= 0;
    endtask

    task automatic pcfg_run(input int tile_id, int max_num_data);
        fork : interrupt_timeout
        begin
            wait(pcfg_g2f_interrupt_pulse[tile_id]);
        end
        begin
            repeat (max_num_data + 50) @(posedge clk);
            $display("@%0t: %m ERROR: glb stream pcfg interrupt timeout ", $time);
        end
        join_any
        disable fork;
        @(posedge clk);
        $display("pcfg streaming done.");
    endtask

    function automatic bit [NUM_GLB_TILES-1:0] update_tile_mask(int tile_id, [NUM_GLB_TILES-1:0] tile_id_mask);
        bit [NUM_GLB_TILES-1:0] new_tile_id_mask;
        new_tile_id_mask = tile_id_mask | (1 << tile_id);
        return new_tile_id_mask;
    endfunction

    function void assert_(bit cond, string msg);
        assert (cond)
        else begin
            $display("%s", msg);
            $stacktrace;
            $finish(1);
        end
    endfunction

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
                if ($test$plusargs("DEBUG")) begin
                    $display("Data array same. index: %0d, data_arr_0: 0x%0h, data_arr_1: 0x%0h", i, data_arr_0[i], data_arr_1[i]);
                end
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
                if ($test$plusargs("DEBUG")) begin
                    $display("Data array same. index: %0d, data_arr_0: %0d, data_arr_1: %0d", i, data_arr_0[i], data_arr_1[i]);
                end
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

    function automatic int read_cgra_cfg(ref [CGRA_CFG_ADDR_WIDTH+CGRA_CFG_DATA_WIDTH-1:0] bs_arr []);
        bit [CGRA_CFG_ADDR_WIDTH-1:0] bs_addr;
        bit [CGRA_CFG_DATA_WIDTH-1:0] bs_data;
        bit [CGRA_CFG_DATA_WIDTH-1:0] rd_data;
        int err;
        assert_($root.top.cgra.cfg_wr_en == 0, $sformatf("Configuration wr_en should go 0 after configuration"));
        for (int i=0; i < bs_arr.size(); i++) begin
            bs_addr = bs_arr[i][CGRA_CFG_DATA_WIDTH +: CGRA_CFG_ADDR_WIDTH];
            bs_data = bs_arr[i][0 +: CGRA_CFG_DATA_WIDTH];
            rd_data = $root.top.cgra.cfg_read(bs_addr);
            if (rd_data != bs_data) begin
                $display("bitstream addr :0x%8h is different. Gold: 0x%8h, Read: 0x%8h", bs_addr, bs_data, rd_data);
                err++;
            end
        end
        if (err > 0) begin
            return 1;
        end
        $display("Bitstream are same");
        return 0;
    endfunction
    
    function void timestamp(string test_name);
        int fd;
        string filename;
        filename = {timestamp_folder, "/", test_name, ".timestamp"};
        fd = $fopen(filename, "a");
        $fdisplay(fd, "%0t", $time);
		$fclose(fd);
    endfunction
    
endprogram
