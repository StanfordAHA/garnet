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
    output logic [NUM_GLB_TILES-1:0] glb_clk_en_master,
    output logic [NUM_GLB_TILES-1:0] glb_clk_en_bank_master,
    output logic [NUM_GLB_TILES-1:0] pcfg_broadcast_stall,
    output logic [NUM_GROUPS-1:0][$clog2(NUM_GLB_TILES)-1:0] flush_crossbar_sel,

    // proc
    output logic                         proc_wr_en,
    output logic [BANK_DATA_WIDTH/8-1:0] proc_wr_strb,
    output logic [   GLB_ADDR_WIDTH-1:0] proc_wr_addr,
    output logic [  BANK_DATA_WIDTH-1:0] proc_wr_data,
    output logic                         proc_rd_en,
    output logic [   GLB_ADDR_WIDTH-1:0] proc_rd_addr,
    input  logic [  BANK_DATA_WIDTH-1:0] proc_rd_data,
    input  logic                         proc_rd_data_valid,

    // configuration of glb from glc
    output logic                      if_cfg_wr_en,
    output logic                      if_cfg_wr_clk_en,
    output logic [AXI_ADDR_WIDTH-1:0] if_cfg_wr_addr,
    output logic [AXI_DATA_WIDTH-1:0] if_cfg_wr_data,
    output logic                      if_cfg_rd_en,
    output logic                      if_cfg_rd_clk_en,
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
    output logic [NUM_GLB_TILES-1:0] strm_g2f_start_pulse,
    output logic [NUM_GLB_TILES-1:0] strm_f2g_start_pulse,
    output logic [NUM_GLB_TILES-1:0] pcfg_start_pulse,
    input  logic [NUM_GLB_TILES-1:0] strm_g2f_interrupt_pulse,
    input  logic [NUM_GLB_TILES-1:0] strm_f2g_interrupt_pulse,
    input  logic [NUM_GLB_TILES-1:0] pcfg_g2f_interrupt_pulse,

    // cgra configuration to cgra
    input logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0] cgra_cfg_g2f_cfg_wr_en,
    input logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0] cgra_cfg_g2f_cfg_rd_en,
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_ADDR_WIDTH-1:0] cgra_cfg_g2f_cfg_addr,
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_g2f_cfg_data
);
    timeunit 100ps; timeprecision 1ps;

    const int MAX_NUM_ERRORS = 20;
    int test_toggle = 0;
    int tile_id = 0;

    bit [NUM_GLB_TILES-1:0] tile_id_mask = 0;

    task automatic init_test();
        // Initialize global buffer configuration registers
        $root.top.assert_reset();

        for (int i = 0; i < NUM_GLB_TILES; i++) begin
            void'($root.top.cgra.glb2prr_off(i));
            void'($root.top.cgra.prr2glb_off(i));
        end
        void'($root.top.cgra.flush_on());
        @(posedge clk);
        void'($root.top.cgra.flush_off());
        @(posedge clk);
    endtask

    task automatic run_test(Test test);
        int err = 0;
        int i_addr = 0;
        int i_extent[LOOP_LEVEL];
        int latency;
        int data_cnt = 0;
        bit done = 0;
        int num_chained_prev = 0;
        int num_chained_next = 0;

        Kernel kernels[] = test.kernels;

        if (test.data_network_mask != 0) begin
            foreach (kernels[i]) begin
                num_chained_prev = 0;
                num_chained_next = 0;
                for (int j = kernels[i].tile_id; j <= NUM_GLB_TILES; j++) begin
                    if (test.data_network_mask[j] == 1) begin
                        num_chained_next++;
                    end else begin
                        break;
                    end
                end
                for (int j = kernels[i].tile_id - 1; j >= 0; j--) begin
                    if (test.data_network_mask[j] == 1) begin
                        num_chained_prev++;
                    end else begin
                        break;
                    end
                end
                for (
                    int j = kernels[i].tile_id - num_chained_prev;
                    j < kernels[i].tile_id + num_chained_next;
                    j++
                ) begin
                    if (kernels[i].type_ == PCFG) begin
                        pcfg_network_connect(j, 1);
                    end else begin
                        data_network_connect(j, 1);
                    end
                end
                if (kernels[i].type_ == PCFG) begin
                    pcfg_network_latency(kernels[i].tile_id,
                                         (num_chained_prev + num_chained_next) * 2 + 3);
                end else begin
                    data_network_latency(kernels[i].tile_id,
                                         (num_chained_prev + num_chained_next) * 2 + 3);
                end
            end
        end
        glb_pcfg_broadcast_stall(test.pcfg_broadcast_stall_mask);
        foreach (kernels[i]) begin
            if (kernels[i].type_ == PCFG) begin
                glb_pcfg_broadcast_mux(test.pcfg_broadcast_mux_value);
                break;
            end
        end

        foreach (kernels[i]) begin
            if (kernels[i].type_ == WR) begin
                // WR/RD only has one loop level
                kernels[i].data_arr = new[kernels[i].extent[0]];
                kernels[i].data_arr_out = new[kernels[i].extent[0]];
                $readmemh(kernels[i].filename, kernels[i].data_arr);
                // Since data is in 16bit word, we have to convert it to 64bit data array
                kernels[i].data64_arr = convert_16b_to_64b(kernels[i].data_arr);
                kernels[i].data64_arr_out = new[kernels[i].data64_arr.size()];
            end else if (kernels[i].type_ == RD) begin
                kernels[i].data_arr = new[kernels[i].extent[0]];
                kernels[i].data_arr_out = new[kernels[i].extent[0]];
                $readmemh(kernels[i].filename, kernels[i].data_arr);
                // Since data is in 16bit word, we have to convert it to 64bit data array
                kernels[i].data64_arr = convert_16b_to_64b(kernels[i].data_arr);
                kernels[i].data64_arr_out = new[kernels[i].data64_arr.size()];
                // Note: In order to test RD, we have to load data to SRAM first.
                // Since our hardware generator does not support ifdef or inline verilog, we have to run task 
                // to write data to memory
                proc_write_burst(kernels[i].start_addr, kernels[i].data64_arr);
            end else if (kernels[i].type_ == PCFG) begin
                kernels[i].data_arr = new[kernels[i].extent[0]];
                kernels[i].data_arr_out = new[kernels[i].extent[0]];
                $readmemh(kernels[i].filename, kernels[i].data_arr);
                // Since data is in 16bit word, we have to convert it to 64bit data array
                kernels[i].data64_arr = convert_16b_to_64b(kernels[i].data_arr);
                kernels[i].data64_arr_out = new[kernels[i].data64_arr.size()];
                // Note: In order to test PCFG, we have to load data to SRAM first.
                // Since our hardware generator does not support ifdef or inline verilog, we have to run task 
                // to write data to memory
                proc_write_burst(kernels[i].start_addr, kernels[i].data64_arr);
                pcfg_dma_configure(kernels[i].tile_id, 1, kernels[i].start_addr,
                                   kernels[i].extent[0] / 4);
            end else if (kernels[i].type_ == G2F) begin
                data_cnt = 1;
                for (int j = 0; j < kernels[i].dim; j++) begin
                    data_cnt += (kernels[i].extent[j] - 1) * kernels[i].data_stride[j];
                end
                kernels[i].mem = new[data_cnt];
                $readmemh(kernels[i].filename, kernels[i].mem);

                data_cnt = 1;
                for (int j = 0; j < kernels[i].dim; j++) begin
                    data_cnt *= kernels[i].extent[j];
                end
                kernels[i].data_arr = new[data_cnt];
                kernels[i].data_arr_out = new[data_cnt];
                i_addr = kernels[i].start_addr;
                i_extent = '{LOOP_LEVEL{0}};
                done = 0;
                data_cnt = 0;
                // Note: Again, we cannot call function to write data to memory, we have to run task 
                // to write data to memory. Use partial wrtie function to do that.
                #2
                    while (1) begin
                        i_addr = kernels[i].start_addr;
                        for (int j = 0; j < kernels[i].dim; j++) begin
                            i_addr += kernels[i].data_stride[j] * i_extent[j] * 2; // Convert 16bit-word address to byte address
                        end
                        // Update internal counter
                        for (int j = 0; j < kernels[i].dim; j++) begin
                            i_extent[j] += 1;
                            if (i_extent[j] == kernels[i].extent[j]) begin
                                i_extent[j] = 0;
                                if (j == kernels[i].dim - 1) done = 1;
                            end else begin
                                break;
                            end
                        end
                        proc_write_partial(i_addr,
                                           kernels[i].mem[(i_addr-kernels[i].start_addr)/2]);
                        kernels[i].data_arr[
                        data_cnt++
                        ] = kernels[i].mem[(i_addr-kernels[i].start_addr)/2];
                        if (done == 1) break;
                    end
                // Configure LD DMA
                g2f_dma_configure(kernels[i].tile_id, 1, kernels[i].start_addr,
                                  kernels[i].cycle_start_addr, kernels[i].dim,
                                  kernels[i].new_extent, kernels[i].new_cycle_stride,
                                  kernels[i].new_data_stride);
            end else if (kernels[i].type_ == F2G) begin
                data_cnt = 1;
                for (int j = 0; j < kernels[i].dim; j++) begin
                    data_cnt *= kernels[i].extent[j];
                end
                kernels[i].data_arr = new[data_cnt];
                kernels[i].data_arr_out = new[data_cnt];
                $readmemh(kernels[i].filename, kernels[i].data_arr);
                kernels[i].data64_arr = convert_16b_to_64b(kernels[i].data_arr);
                kernels[i].data64_arr_out = new[kernels[i].data64_arr.size()];

                // Store the data to PRR queue.
                write_prr(kernels[i].tile_id, kernels[i].data_arr);
                // Configure PRR controller to follow cycle stride/extent pattern.
                void'($root.top.cgra.prr2glb_configure(
                    kernels[i].tile_id, kernels[i].dim, kernels[i].extent, kernels[i].cycle_stride
                ));
                // Configure ST DMA
                f2g_dma_configure(kernels[i].tile_id, 1, kernels[i].start_addr,
                                  kernels[i].cycle_start_addr, kernels[i].dim,
                                  kernels[i].new_extent, kernels[i].new_cycle_stride,
                                  kernels[i].new_data_stride);
            end else if (kernels[i].type_ == SRAM) begin
                kernels[i].data_arr = new[kernels[i].extent[0]];
                kernels[i].data_arr_out = new[kernels[i].extent[0]];
                $readmemh(kernels[i].filename, kernels[i].data_arr);
                // Since data is in 16bit word, we have to convert it to 64bit data array
                kernels[i].data64_arr = convert_16b_to_64b(kernels[i].data_arr);
                kernels[i].data64_arr_out = new[kernels[i].data64_arr.size()];
            end
        end

        repeat (50) @(posedge clk);

        $display("\n---- Test Run ----");
        // start
        test_toggle = 1;
        fork
            if (test.g2f_tile_mask != 0) g2f_start(test.g2f_tile_mask);
            if (test.f2g_tile_mask != 0) f2g_start(test.f2g_tile_mask);
            if (test.pcfg_tile_mask != 0) pcfg_start(test.pcfg_tile_mask);
            begin
                foreach (kernels[i]) begin
                    automatic int j = i;
                    fork
                        if (kernels[j].type_ == WR) begin
                            proc_write_burst(kernels[j].start_addr, convert_16b_to_64b(
                                             kernels[j].data_arr));
                        end else if (kernels[j].type_ == RD) begin
                            proc_read_burst(kernels[j].start_addr, kernels[j].data64_arr_out);
                        end else if (kernels[j].type_ == G2F) begin
                            g2f_run(kernels[j].tile_id, kernels[j].total_cycle);
                        end else if (kernels[j].type_ == F2G) begin
                            f2g_run(kernels[j].tile_id, kernels[j].total_cycle);
                        end else if (kernels[j].type_ == PCFG) begin
                            pcfg_run(kernels[j].tile_id, kernels[j].check_tile_id, kernels[j].total_cycle,
                                     kernels[j].data64_arr_out);
                        end else if (kernels[j].type_ == SRAM) begin
                            sram_write_burst(kernels[j].bank_id, kernels[j].data64_arr);
                            sram_read_burst(kernels[j].bank_id, kernels[j].data64_arr_out);
                        end
                    join_none
                end
                wait fork;
            end
        join_none
        wait fork;
        // end
        test_toggle = 0;

        repeat (50) @(posedge clk);

        // compare
        $display("\n---- Test Result ----");
        foreach (kernels[i]) begin
            if (kernels[i].type_ == WR) begin
                proc_read_burst(kernels[i].start_addr, kernels[i].data64_arr_out);
                $display("WR Comparison");
                err += compare_64b_arr(kernels[i].data64_arr, kernels[i].data64_arr_out);
            end else if (kernels[i].type_ == RD) begin
                $display("RD Comparison");
                err += compare_64b_arr(kernels[i].data64_arr, kernels[i].data64_arr_out);
            end else if (kernels[i].type_ == G2F) begin
                // FIXME: Only works with 'use_valid' set in LD_DMA CTRL
                read_prr(kernels[i].tile_id, kernels[i].data_arr_out);
                $display("G2F Comparison");
                err += compare_16b_arr(kernels[i].data_arr, kernels[i].data_arr_out);
            end else if (kernels[i].type_ == F2G) begin
                proc_read_burst(kernels[i].start_addr, kernels[i].data64_arr_out);
                $display("F2G Comparison");
                err += compare_64b_arr(kernels[i].data64_arr, kernels[i].data64_arr_out);
            end else if (kernels[i].type_ == PCFG) begin
                $display("PCFG Comparison");
                err += compare_64b_arr(kernels[i].data64_arr, kernels[i].data64_arr_out);
            end else if (kernels[i].type_ == SRAM) begin
                $display("SRAM Comparison");
                err += compare_64b_arr(kernels[i].data64_arr, kernels[i].data64_arr_out);
            end
            repeat (30) @(posedge clk);
        end

        if (err == 0) begin
            $display("Test passed!");
        end else begin
            $error("Test failed!");
        end

    endtask

    initial begin
        Test test;
        string test_filename;
        string test_name;
        int max_num_test;
        initialize();
        if (!($value$plusargs("MAX_NUM_TEST=%d", max_num_test))) max_num_test = 10;
        for (int i = 1; i <= max_num_test; i++) begin
            $sformat(test_name, "test%02d", i);
            if (($test$plusargs(test_name))) begin
                $display("\n************** Test Start *****************");
                $sformat(test_filename, "./testvectors/%s.txt", test_name);
                test = new(test_filename);
                init_test();
                run_test(test);
                $display("************** Test End *****************\n");
            end
        end
    end

    task initialize();
        // control
        glb_clk_en_master <= 0;
        glb_clk_en_bank_master <= 0;
        pcfg_broadcast_stall <= 0;
        pcfg_start_pulse <= 0;
        strm_g2f_start_pulse <= 0;
        strm_f2g_start_pulse <= 0;
        flush_crossbar_sel <= 0;

        // proc
        proc_wr_en <= 0;
        proc_wr_strb <= 0;
        proc_wr_addr <= 0;
        proc_wr_data <= 0;
        proc_rd_en <= 0;
        proc_rd_addr <= 0;

        // cfg ifc
        if_cfg_wr_en <= 0;
        if_cfg_wr_clk_en <= 0;
        if_cfg_wr_addr <= 0;
        if_cfg_wr_data <= 0;
        if_cfg_rd_en <= 0;
        if_cfg_rd_clk_en <= 0;
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
        repeat (10) @(posedge clk);
    endtask

    task glb_flush_crossbar_ctrl(logic [NUM_GROUPS-1:0][$clog2(NUM_GLB_TILES)-1:0] mask);
        #2 $display("Glb flush signal crossbar configuration %8h", mask);
        flush_crossbar_sel <= mask;
        repeat (4) @(posedge clk);

    endtask

    task glb_clk_en_master_ctrl(logic [NUM_GLB_TILES-1:0] mask);
        #2 $display("Glb tiles master clk enable with mask %16b", mask);
        glb_clk_en_master <= mask;
        repeat (4) @(posedge clk);

    endtask

    task glb_clk_en_bank_master_ctrl(logic [NUM_GLB_TILES-1:0] mask);
        #2 $display("Glb tiles master bank clk enable with mask %16b", mask);
        glb_clk_en_bank_master <= mask;
        repeat (4) @(posedge clk);

    endtask

    task glb_pcfg_broadcast_stall(logic [NUM_GLB_TILES-1:0] mask);
        #2 $display("Glb tiles PCFG broadcast logics are stalled with mask %16b", mask);
        pcfg_broadcast_stall <= mask;
        repeat (4) @(posedge clk);

    endtask

    task glb_pcfg_broadcast_mux(
        logic [`GLB_PCFG_BROADCAST_MUX_R_MSB:0] mux_value[NUM_GLB_TILES-1:0]);
        $display("Set pcfg broadcast muxes");
        for (int i = 0; i < NUM_GLB_TILES; i++) begin
            $display("Tile ID: %0d, South Mux: %2b, West Mux: %2b, East Mux: %2b", i,
                     mux_value[i][`GLB_PCFG_BROADCAST_MUX_SOUTH_F_MSB : `GLB_PCFG_BROADCAST_MUX_SOUTH_F_LSB],
                     mux_value[i][`GLB_PCFG_BROADCAST_MUX_WEST_F_MSB : `GLB_PCFG_BROADCAST_MUX_WEST_F_LSB],
                     mux_value[i][`GLB_PCFG_BROADCAST_MUX_EAST_F_MSB : `GLB_PCFG_BROADCAST_MUX_EAST_F_LSB]);
            glb_cfg_write(
                (i << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_BROADCAST_MUX_R,
                mux_value[i]);
            glb_cfg_read(
                (i << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_BROADCAST_MUX_R,
                mux_value[i]);
        end
        repeat (4) @(posedge clk);

    endtask

    task automatic sram_write_burst(int bank_id, ref data64 data);
        int start_addr = (1 << BANK_ADDR_WIDTH) * bank_id;
        int write_data;
        for (int i = 0; i < data.size(); i++) begin
            for (int j = 0; j < 2; j++) begin
                write_data = data[i][32*j+:32];
                sram_write(start_addr + (i << BANK_BYTE_OFFSET) + (j << (BANK_BYTE_OFFSET - 1)),
                           write_data);
            end
        end
    endtask

    task automatic sram_write(input bit [GLB_ADDR_WIDTH-1:0] addr, int data);
        #2 if_sram_cfg_wr_en <= 1;
        if_sram_cfg_wr_addr <= addr;
        if_sram_cfg_wr_data <= data;
        repeat (4) @(posedge clk);
        #2 if_sram_cfg_wr_en <= 0;
        if_sram_cfg_wr_addr <= 0;
        if_sram_cfg_wr_data <= 0;
        repeat (2) @(posedge clk);
    endtask

    task automatic sram_read_burst(int bank_id, ref data64 data);
        int start_addr = (1 << BANK_ADDR_WIDTH) * bank_id;
        int read_data;
        for (int i = 0; i < data.size(); i++) begin
            for (int j = 0; j < 2; j++) begin
                sram_read(start_addr + (i << BANK_BYTE_OFFSET) + (j << (BANK_BYTE_OFFSET - 1)),
                          read_data);
                data[i][32*j+:32] = read_data;
            end
        end
    endtask

    task automatic sram_read(input bit [GLB_ADDR_WIDTH-1:0] addr, ref int data);
        int read_delay = 40;
        fork
            begin
                @(posedge clk);
                #2 if_sram_cfg_rd_en <= 1;
                if_sram_cfg_rd_addr <= addr;
                repeat (4) @(posedge clk);
                #2 if_sram_cfg_rd_en <= 0;
                if_sram_cfg_rd_addr <= 0;
            end
            begin
                for (int i = 0; i < read_delay; i++) begin
                    if (if_sram_cfg_rd_data_valid == 1) begin
                        data = if_sram_cfg_rd_data;
                        break;
                    end
                    @(posedge clk);
                end
            end
        join
        repeat (20) @(posedge clk);
    endtask

    task automatic data_network_connect(input int tile_id, bit is_connected);
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_DATA_NETWORK_CTRL_R,
            (is_connected << `GLB_DATA_NETWORK_CTRL_CONNECTED_F_LSB));
    endtask

    task automatic data_network_latency(input int tile_id, [LATENCY_WIDTH-1:0] latency);
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_DATA_NETWORK_LATENCY_R,
            (latency << `GLB_DATA_NETWORK_LATENCY_VALUE_F_LSB));
    endtask

    task automatic pcfg_network_connect(input int tile_id, bit is_connected);
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_NETWORK_CTRL_R,
            (is_connected << `GLB_PCFG_NETWORK_CTRL_CONNECTED_F_LSB));
    endtask

    task automatic pcfg_network_latency(input int tile_id, [LATENCY_WIDTH-1:0] latency);
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_NETWORK_LATENCY_R,
            (latency << `GLB_PCFG_NETWORK_LATENCY_VALUE_F_LSB));
    endtask

    task automatic pcfg_dma_configure(input int tile_id, bit on, [AXI_DATA_WIDTH-1:0] start_addr,
                                      [AXI_DATA_WIDTH-1:0] num_word);
        glb_cfg_write((tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_DMA_CTRL_R,
                      (on << `GLB_PCFG_DMA_CTRL_MODE_F_LSB));
        glb_cfg_read((tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_DMA_CTRL_R,
                     (on << `GLB_PCFG_DMA_CTRL_MODE_F_LSB));
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_DMA_HEADER_START_ADDR_R,
            (start_addr << `GLB_PCFG_DMA_HEADER_START_ADDR_START_ADDR_F_LSB));
        glb_cfg_read(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_DMA_HEADER_START_ADDR_R,
            (start_addr << `GLB_PCFG_DMA_HEADER_START_ADDR_START_ADDR_F_LSB));
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_DMA_HEADER_NUM_CFG_R,
            (num_word << `GLB_PCFG_DMA_HEADER_NUM_CFG_NUM_CFG_F_LSB));
        glb_cfg_read(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_PCFG_DMA_HEADER_NUM_CFG_R,
            (num_word << `GLB_PCFG_DMA_HEADER_NUM_CFG_NUM_CFG_F_LSB));
    endtask

    task automatic g2f_dma_configure(input int tile_id, bit on, [AXI_DATA_WIDTH-1:0] start_addr,
                                     [AXI_DATA_WIDTH-1:0] cycle_start_addr, int dim,
                                     int extent[LOOP_LEVEL], int cycle_stride[LOOP_LEVEL],
                                     int data_stride[LOOP_LEVEL]);
        glb_cfg_write((tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_CTRL_R,
                      ((2'b01 << `GLB_LD_DMA_CTRL_DATA_MUX_F_LSB)
                    | (on << `GLB_LD_DMA_CTRL_MODE_F_LSB)
                    | (1 << `GLB_LD_DMA_CTRL_USE_VALID_F_LSB)));
        glb_cfg_read((tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_CTRL_R,
                     ((2'b01 << `GLB_LD_DMA_CTRL_DATA_MUX_F_LSB)
                    | (on << `GLB_LD_DMA_CTRL_MODE_F_LSB)
                    | (1 << `GLB_LD_DMA_CTRL_USE_VALID_F_LSB)));
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_START_ADDR_R,
            (start_addr << `GLB_LD_DMA_HEADER_0_START_ADDR_START_ADDR_F_LSB));
        glb_cfg_read(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_START_ADDR_R,
            (start_addr << `GLB_LD_DMA_HEADER_0_START_ADDR_START_ADDR_F_LSB));
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_CYCLE_START_ADDR_R,
            (cycle_start_addr << `GLB_LD_DMA_HEADER_0_CYCLE_START_ADDR_CYCLE_START_ADDR_F_LSB));
        glb_cfg_read(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_CYCLE_START_ADDR_R,
            (cycle_start_addr << `GLB_LD_DMA_HEADER_0_CYCLE_START_ADDR_CYCLE_START_ADDR_F_LSB));
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_DIM_R,
            (dim << `GLB_LD_DMA_HEADER_0_DIM_DIM_F_LSB));
        glb_cfg_read(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_DIM_R,
            (dim << `GLB_LD_DMA_HEADER_0_DIM_DIM_F_LSB));
        // NOTE: Each stride/range address difference is 'hc
        for (int i = 0; i < dim; i++) begin
            glb_cfg_write(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_RANGE_0_R + i * 'hc,
                (extent[i] << `GLB_LD_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
            glb_cfg_read(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_RANGE_0_R + i * 'hc,
                (extent[i] << `GLB_LD_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
            glb_cfg_write(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_STRIDE_0_R + i * 'hc,
                (data_stride[i] << `GLB_LD_DMA_HEADER_0_STRIDE_0_STRIDE_F_LSB));
            glb_cfg_read(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_STRIDE_0_R + i * 'hc,
                (data_stride[i] << `GLB_LD_DMA_HEADER_0_STRIDE_0_STRIDE_F_LSB));
            glb_cfg_write(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_CYCLE_STRIDE_0_R + i * 'hc,
                (cycle_stride[i] << `GLB_LD_DMA_HEADER_0_CYCLE_STRIDE_0_CYCLE_STRIDE_F_LSB));
            glb_cfg_read(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_LD_DMA_HEADER_0_CYCLE_STRIDE_0_R + i * 'hc,
                (cycle_stride[i] << `GLB_LD_DMA_HEADER_0_CYCLE_STRIDE_0_CYCLE_STRIDE_F_LSB));
        end
    endtask

    task automatic f2g_dma_configure(input int tile_id, bit on, [AXI_DATA_WIDTH-1:0] start_addr,
                                     [AXI_DATA_WIDTH-1:0] cycle_start_addr, int dim,
                                     int extent[LOOP_LEVEL], int cycle_stride[LOOP_LEVEL],
                                     int data_stride[LOOP_LEVEL]);
        glb_cfg_write((tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_CTRL_R,
                      ((2'b10 << `GLB_ST_DMA_CTRL_DATA_MUX_F_LSB)
                    | (on << `GLB_ST_DMA_CTRL_MODE_F_LSB)
                    | (1 << `GLB_ST_DMA_CTRL_USE_VALID_F_LSB)));
        glb_cfg_read((tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_CTRL_R,
                     ((2'b10 << `GLB_ST_DMA_CTRL_DATA_MUX_F_LSB)
                    | (on << `GLB_ST_DMA_CTRL_MODE_F_LSB)
                    | (1 << `GLB_ST_DMA_CTRL_USE_VALID_F_LSB)));
        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_START_ADDR_R,
            (start_addr << `GLB_ST_DMA_HEADER_0_START_ADDR_START_ADDR_F_LSB));
        glb_cfg_read(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_START_ADDR_R,
            (start_addr << `GLB_ST_DMA_HEADER_0_START_ADDR_START_ADDR_F_LSB));

        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_CYCLE_START_ADDR_R,
            (cycle_start_addr << `GLB_ST_DMA_HEADER_0_CYCLE_START_ADDR_CYCLE_START_ADDR_F_LSB));
        glb_cfg_read(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_CYCLE_START_ADDR_R,
            (cycle_start_addr << `GLB_ST_DMA_HEADER_0_CYCLE_START_ADDR_CYCLE_START_ADDR_F_LSB));

        glb_cfg_write(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_DIM_R,
            (dim << `GLB_ST_DMA_HEADER_0_DIM_DIM_F_LSB));
        glb_cfg_read(
            (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_DIM_R,
            (dim << `GLB_ST_DMA_HEADER_0_DIM_DIM_F_LSB));
        // NOTE: Each stride/range address difference is 'hc
        for (int i = 0; i < dim; i++) begin
            glb_cfg_write(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_RANGE_0_R + i * 'hc,
                (extent[i] << `GLB_ST_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
            glb_cfg_read(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_RANGE_0_R + i * 'hc,
                (extent[i] << `GLB_ST_DMA_HEADER_0_RANGE_0_RANGE_F_LSB));
            glb_cfg_write(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_STRIDE_0_R + i * 'hc,
                (data_stride[i] << `GLB_ST_DMA_HEADER_0_STRIDE_0_STRIDE_F_LSB));
            glb_cfg_read(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_STRIDE_0_R + i * 'hc,
                (data_stride[i] << `GLB_ST_DMA_HEADER_0_STRIDE_0_STRIDE_F_LSB));
            glb_cfg_write(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_CYCLE_STRIDE_0_R + i * 'hc,
                (cycle_stride[i] << `GLB_ST_DMA_HEADER_0_CYCLE_STRIDE_0_CYCLE_STRIDE_F_LSB));
            glb_cfg_read(
                (tile_id << (AXI_ADDR_WIDTH - TILE_SEL_ADDR_WIDTH)) + `GLB_ST_DMA_HEADER_0_CYCLE_STRIDE_0_R + i * 'hc,
                (cycle_stride[i] << `GLB_ST_DMA_HEADER_0_CYCLE_STRIDE_0_CYCLE_STRIDE_F_LSB));
        end
    endtask

    task glb_cfg_write(input [AXI_ADDR_WIDTH-1:0] addr, input [AXI_DATA_WIDTH-1:0] data);
        repeat (5) @(posedge clk);
        #2 if_cfg_wr_clk_en <= 1;
        @(posedge clk);
        #2 if_cfg_wr_en <= 1;
        if_cfg_wr_addr <= addr;
        if_cfg_wr_data <= data;
        @(posedge clk);
        #2 if_cfg_wr_en <= 0;
        if_cfg_wr_addr <= 0;
        if_cfg_wr_data <= 0;
        repeat (NUM_GLB_TILES + 10) @(posedge clk);
        #2 if_cfg_wr_clk_en <= 0;
        repeat (2) @(posedge clk);
    endtask

    task glb_cfg_read(input [AXI_ADDR_WIDTH-1:0] addr, input [AXI_DATA_WIDTH-1:0] data);
        repeat (5) @(posedge clk);
        #2 if_cfg_rd_clk_en <= 1;
        @(posedge clk);
        #2 if_cfg_rd_en <= 1;
        if_cfg_rd_addr <= addr;
        @(posedge clk);
        #2 if_cfg_rd_en <= 0;
        if_cfg_rd_addr <= 0;
        fork : glb_cfg_read_timeout
            begin
                while (1) begin
                    if (if_cfg_rd_data_valid) begin
                        assert (data == if_cfg_rd_data);
                        break;
                    end
                    @(posedge clk);
                end
            end
            begin
                repeat (20 + 2 * NUM_GLB_TILES) @(posedge clk);
                $display("@%0t: %m ERROR: glb cfg read timeout ", $time);
            end
        join_any
        disable fork;
        @(posedge clk);
        #2 if_cfg_rd_clk_en <= 0;
        repeat (2) @(posedge clk);
    endtask

    task automatic proc_write_burst(input [GLB_ADDR_WIDTH-1:0] addr, data64 data);
        int size = data.size();
        repeat (5) @(posedge clk);
        $display("Start glb-mem burst write. addr: 0x%0h, size %0d", addr, size);
        #2
            foreach (data[i]) begin
                proc_write(addr + 8 * i, data[i]);
            end
        #2 proc_wr_en <= 0;
        proc_wr_strb <= 0;
        $display("Finish glb-mem burst write");
        repeat (5) @(posedge clk);
    endtask

    task automatic proc_write(input [GLB_ADDR_WIDTH-1:0] addr, [BANK_DATA_WIDTH-1:0] data);
        proc_wr_en   <= 1;
        proc_wr_strb <= {(BANK_DATA_WIDTH / 8) {1'b1}};
        proc_wr_addr <= addr;
        proc_wr_data <= data;
        @(posedge clk);
        #2 proc_wr_en <= 0;
        proc_wr_strb <= 0;
    endtask

    task automatic proc_write_partial(input [GLB_ADDR_WIDTH-1:0] addr,
                                      [CGRA_DATA_WIDTH-1:0] data);
        bit [BANK_DATA_WIDTH / 8 - 1:0] strb;
        bit [BANK_DATA_WIDTH - 1:0] wr_data;

        // FIXME: Lazy to generalize this task.
        if (BANK_DATA_WIDTH != CGRA_DATA_WIDTH * 4)
            $error("This task assumes that BANK_DATA_WIDTH is 64bit and CGRA_DATA_WIDTH is 16bit.");

        case (addr[2:1])
            2'b00: begin
                strb = {{6{1'b0}}, {2{1'b1}}};
                wr_data = {48'b0, data};
            end
            2'b01: begin
                strb = {{4{1'b0}}, {2{1'b1}}, {2{1'b0}}};
                wr_data = {32'b0, data, 16'b0};
            end
            2'b10: begin
                strb = {{2{1'b0}}, {2{1'b1}}, {4{1'b0}}};
                wr_data = {16'b0, data, 32'b0};
            end
            2'b11: begin
                strb = {{2{1'b1}}, {6{1'b0}}};
                wr_data = {data, 48'b0};
            end
        endcase
        proc_wr_en   <= 1;
        proc_wr_strb <= strb;
        proc_wr_addr <= addr;
        proc_wr_data <= wr_data;
        @(posedge clk);
        #2 proc_wr_en <= 0;
        proc_wr_strb <= 0;
    endtask

    task automatic proc_read_burst(input [GLB_ADDR_WIDTH-1:0] addr, ref data64 data);
        logic [CGRA_DATA_WIDTH-1:0] data_q[$];
        data16 data_out;
        int size = data.size();

        repeat (5) @(posedge clk);
        $display("Start glb-mem burst read. addr: 0x%0h, size %0d", addr, size);
        // If address is not aligned, we need to read one more address
        if (addr[2:1] != 2'b00) begin
            size += 1;
        end
        fork : proc_read
            begin
                for (int i = 0; i < size; i++) begin
                    #2 proc_rd_en <= 1;
                    proc_rd_addr <= addr + 8 * i;
                    @(posedge clk);
                end
                #2 proc_rd_en <= 0;
            end
            begin
                fork : proc_read_timeout
                    begin
                        int cnt = 0;
                        while (1) begin
                            @(posedge clk);
                            if (proc_rd_data_valid) begin
                                // For the first and the last data, we only push valid data to queue 
                                if (cnt == 0) begin
                                    if (addr[2:1] == 2'b00) begin
                                        for (int i = 0; i < 4; i++) begin
                                            data_q.push_back(
                                                proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                        end
                                    end else if (addr[2:1] == 2'b01) begin
                                        for (int i = 1; i < 4; i++) begin
                                            data_q.push_back(
                                                proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                        end
                                    end else if (addr[2:1] == 2'b10) begin
                                        for (int i = 2; i < 4; i++) begin
                                            data_q.push_back(
                                                proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                        end
                                    end else begin
                                        for (int i = 3; i < 4; i++) begin
                                            data_q.push_back(
                                                proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                        end
                                    end
                                end else if (cnt == (size - 1)) begin
                                    if (addr[2:1] == 2'b00) begin
                                        for (int i = 0; i < 4; i++) begin
                                            data_q.push_back(
                                                proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                        end
                                    end else if (addr[2:1] == 2'b01) begin
                                        for (int i = 0; i < 1; i++) begin
                                            data_q.push_back(
                                                proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                        end
                                    end else if (addr[2:1] == 2'b10) begin
                                        for (int i = 0; i < 2; i++) begin
                                            data_q.push_back(
                                                proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                        end
                                    end else begin
                                        for (int i = 0; i < 3; i++) begin
                                            data_q.push_back(
                                                proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                        end
                                    end
                                end else begin
                                    for (int i = 0; i < 4; i++) begin
                                        data_q.push_back(
                                            proc_rd_data[CGRA_DATA_WIDTH*i+:CGRA_DATA_WIDTH]);
                                    end
                                end
                                cnt = cnt + 1;
                                if (cnt == size) break;
                            end
                        end
                    end
                    begin
                        repeat (2 * size + 100) @(posedge clk);
                        $display("@%0t: %m ERROR: glb-mem burst read timeout ", $time);
                    end
                join_any
                disable fork;
            end
        join
        data_out = data_q;
        data = convert_16b_to_64b(data_out);
        repeat (5) @(posedge clk);
        $display("Finish glb-mem burst read");
    endtask

    task automatic g2f_start(input [NUM_GLB_TILES-1:0] tile_id_mask);
        $display("g2f streaming start. tiles: 0x%4h", tile_id_mask);

        // Enable glb2prr
        for (int i = 0; i < NUM_PRR; i++) begin
            if (tile_id_mask[i] == 1) begin
                void'($root.top.cgra.glb2prr_on(i));
            end
        end

        #2 strm_g2f_start_pulse <= tile_id_mask;
        @(posedge clk);
        #2 strm_g2f_start_pulse <= 0;
    endtask

    task automatic g2f_run(input int tile_id, int total_cycle);
        $display("g2f run total cycles: %0d", total_cycle);
        fork : interrupt_timeout
            begin
                wait (strm_g2f_interrupt_pulse[tile_id]);
                $display("g2f streaming done.");
            end
            begin
                repeat (total_cycle + 30) @(posedge clk);
                $display("@%0t: %m ERROR: glb stream g2f interrupt timeout ", $time);
            end
        join_any
        disable fork;
        @(posedge clk);
    endtask

    task automatic f2g_start(input [NUM_GLB_TILES-1:0] tile_id_mask);
        $display("f2g streaming start. tiles: 0x%4h", tile_id_mask);

        #2 strm_f2g_start_pulse <= tile_id_mask;
        @(posedge clk);
        #2 strm_f2g_start_pulse <= 0;

        repeat (GLS_PIPELINE_DEPTH + 3) @(posedge clk);
        // Enable glb2prr
        for (int i = 0; i < NUM_PRR; i++) begin
            if (tile_id_mask[i] == 1) begin
                void'($root.top.cgra.prr2glb_on(i));
            end
        end

    endtask

    task automatic f2g_run(input int tile_id, int total_cycle);
        $display("f2g run total cycles: %0d", total_cycle);
        fork : interrupt_timeout
            begin
                wait (strm_f2g_interrupt_pulse[tile_id]);
                $display("f2g streaming done.");
            end
            begin
                repeat (total_cycle + 30) @(posedge clk);
                $display("@%0t: %m ERROR: cgra stream f2g interrupt timeout ", $time);
            end
        join_any
        disable fork;
        @(posedge clk);
    endtask

    task automatic pcfg_start(input [NUM_GLB_TILES-1:0] tile_id_mask);
        $display("pcfg streaming start. tiles: 0x%4h", tile_id_mask);
        repeat (5) @(posedge clk);
        #2 pcfg_start_pulse <= tile_id_mask;
        @(posedge clk);
        #2 pcfg_start_pulse <= 0;
    endtask

    task automatic pcfg_run(input int tile_id, int check_tile_id, int total_cycle,
                            ref [CGRA_CFG_ADDR_WIDTH + CGRA_CFG_DATA_WIDTH - 1:0] cgra_cfg_out[]);
        int cnt = 0;
        fork : interrupt_timeout
            begin
                wait (pcfg_g2f_interrupt_pulse[tile_id]);
            end
            begin
                repeat (total_cycle + 50) @(posedge clk);
                $display("@%0t: %m ERROR: glb stream pcfg interrupt timeout ", $time);
            end
            begin
                forever begin
                    // Check the second column
                    if (cgra_cfg_g2f_cfg_wr_en[check_tile_id][CGRA_PER_GLB-1] == 1) begin
                        cgra_cfg_out[
                        cnt++
                        ] = {
                            cgra_cfg_g2f_cfg_addr[check_tile_id][CGRA_PER_GLB-1],
                            cgra_cfg_g2f_cfg_data[check_tile_id][CGRA_PER_GLB-1]
                        };
                    end
                    @(posedge clk);
                end
            end
        join_any
        disable fork;
        @(posedge clk);
        $display("pcfg streaming done.");
    endtask

    function automatic void read_prr(input int prr_id,
                                     ref [CGRA_DATA_WIDTH-1:0] cgra_data_arr_out[]);
        if (cgra_data_arr_out.size() != $root.top.cgra.glb2prr_q[prr_id].size) begin
            $error(
                "@%0t: %m FAIL: glb stream to PRR data size is different.\nExpected data size: %d, PRR data size: %d",
                $time, cgra_data_arr_out.size(), $root.top.cgra.glb2prr_q[prr_id].size);
        end else begin
            foreach ($root.top.cgra.glb2prr_q[prr_id][i]) begin
                cgra_data_arr_out[i] = $root.top.cgra.glb2prr_q[prr_id][i];
            end
        end
    endfunction

    function automatic void write_prr(input int prr_id,
                                      ref [CGRA_DATA_WIDTH-1:0] cgra_data_arr[]);
        foreach (cgra_data_arr[i]) begin
            $root.top.cgra.prr2glb_q[prr_id][i] = cgra_data_arr[i];
        end
    endfunction

    function automatic bit [NUM_GLB_TILES-1:0] update_tile_mask(
        int tile_id, [NUM_GLB_TILES-1:0] tile_id_mask);
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

    function automatic int compare_64b_arr(ref [63:0] data_arr_0[], ref [63:0] data_arr_1[]);
        int size_0 = data_arr_0.size();
        int size_1 = data_arr_1.size();
        int err;
        if (size_0 != size_1) begin
            $display("Data array size is different. data_arr_0: %0d, data_arr_1: %0d", size_0,
                     size_1);
            err++;
        end
        foreach (data_arr_0[i]) begin
            if (data_arr_0[i] !== data_arr_1[i]) begin
                err++;
                if (err > MAX_NUM_ERRORS) begin
                    $display("The number of errors reached %0d. Do not print anymore",
                             MAX_NUM_ERRORS);
                    break;
                end
                $display("Data different. index: %0d, data_arr_0: 0x%0h, data_arr_1: 0x%0h", i,
                         data_arr_0[i], data_arr_1[i]);
            end
        end
        if (err > 0) begin
            $error("Two data array are Different");
            return 1;
        end
        $display("Two data array are same");
        return 0;
    endfunction

    function automatic int compare_16b_arr(ref [15:0] data_arr_0[], ref [15:0] data_arr_1[]);
        int size_0 = data_arr_0.size();
        int size_1 = data_arr_1.size();
        int err;
        if (size_0 != size_1) begin
            $display("Data array size is different. data_arr_0: %0d, data_arr_1: %0d", size_0,
                     size_1);
            err++;
        end
        foreach (data_arr_0[i]) begin
            if (data_arr_0[i] !== data_arr_1[i]) begin
                err++;
                if (err > MAX_NUM_ERRORS) begin
                    $display("The number of errors reached %0d. Do not print anymore",
                             MAX_NUM_ERRORS);
                    break;
                end
                $display("Data different. index: %0d, data_arr_0: 0x%0h, data_arr_1: 0x%0h", i,
                         data_arr_0[i], data_arr_1[i]);
            end
        end
        if (err > 0) begin
            $error("Two data array are Different");
            return 1;
        end
        $display("Two data array are same");
        return 0;
    endfunction

    function int compare_cfg(logic [BANK_DATA_WIDTH-1:0] cfg_0,
                             logic [AXI_DATA_WIDTH-1:0] cfg_1);
        if (cfg_0 !== cfg_1) begin
            $display("cfg data is different. cfg_0: 0x%0h, cfg_1: 0x%0h", cfg_0, cfg_1);
            return 1;
        end
        return 0;
    endfunction

    function automatic data64 convert_16b_to_64b(ref [15:0] data_in[]);
        data64 data_out;
        int num_data_in = data_in.size();
        int num_data_out = (num_data_in + 3) / 4;
        data_out = new[num_data_out];
        for (int i = 0; i < num_data_in; i = i + 4) begin
            if (i == (num_data_in - 1)) begin
                if (num_data_in % 4 == 1) begin
                    data_out[i/4] = {{48{1'b1}}, data_in[i]};
                end else if (num_data_in % 4 == 2) begin
                    data_out[i/4] = {{32{1'b1}}, data_in[i+1], data_in[i]};
                end else if (num_data_in % 4 == 3) begin
                    data_out[i/4] = {{16{1'b1}}, data_in[i+2], data_in[i+1], data_in[i]};
                end else begin
                    data_out[i/4] = {data_in[i+3], data_in[i+2], data_in[i+1], data_in[i]};
                end
            end
            data_out[i/4] = {data_in[i+3], data_in[i+2], data_in[i+1], data_in[i]};
        end
        return data_out;
    endfunction

    function automatic data16 convert_64b_to_16b(ref [63:0] data_in[]);
        data16 data_out;
        int num_data_in = data_in.size();
        int num_data_out = num_data_in * 4;
        data_out = new[num_data_out];
        for (int i = 0; i < num_data_in; i++) begin
            data_out[i*4+0] = data_in[i][0+:16];
            data_out[i*4+1] = data_in[i][16+:16];
            data_out[i*4+2] = data_in[i][32+:16];
            data_out[i*4+3] = data_in[i][48+:16];
        end
        return data_out;
    endfunction

    function automatic int read_cgra_cfg(
        ref [CGRA_CFG_ADDR_WIDTH+CGRA_CFG_DATA_WIDTH-1:0] bs_arr[]);
        bit [CGRA_CFG_ADDR_WIDTH-1:0] bs_addr;
        bit [CGRA_CFG_DATA_WIDTH-1:0] bs_data;
        bit [CGRA_CFG_DATA_WIDTH-1:0] rd_data;
        int err;
        assert_($root.top.cgra.cfg_wr_en == 0, $sformatf(
                "Configuration wr_en should go 0 after configuration"));
        for (int i = 0; i < bs_arr.size(); i++) begin
            bs_addr = bs_arr[i][CGRA_CFG_DATA_WIDTH+:CGRA_CFG_ADDR_WIDTH];
            bs_data = bs_arr[i][0+:CGRA_CFG_DATA_WIDTH];
            rd_data = $root.top.cgra.cfg_read(bs_addr);
            if (rd_data != bs_data) begin
                $display("bitstream addr :0x%8h is different. Gold: 0x%8h, Read: 0x%8h", bs_addr,
                         bs_data, rd_data);
                err++;
            end
        end
        if (err > 0) begin
            return 1;
        end
        $display("Bitstream are same");
        return 0;
    endfunction

endprogram
