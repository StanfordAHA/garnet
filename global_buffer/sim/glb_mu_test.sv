/*=============================================================================
** Module: glb_mu_test.sv
** Description:
**              program for glb_mu_test
** Author: Michael Oduoza
** Change history:  03/13/2025 - Implement the first version
**===========================================================================*/
program glb_mu_test #(
    parameter int MAX_NUM_APPS = 1000
) (
    input logic clk,
    reset,
    proc_ifc p_ifc,
    glb_mu_ifc glb_mu_ifc
);
    int err = 0;
    const int MAX_NUM_ERRORS = 20;
    const int GLB_TILE_BASE = 4;
    const int BURST_SIZE = 32;
    const int ADD_INPUT_BUBBLES = 0;
    const int RANDOM_SHIFT = 2;
    const int INPUT_DATA_SIZE = 512;
    const int NUM_SEGMENTS = 4;
    const int BANK_DEPTH = 2 ** (BANK_ADDR_WIDTH - BANK_BYTE_OFFSET);
    const real OVERLAP_TEST_SPLIT_FACTOR = 0.5625;
    int x = 0;
    int OVERLAP_TEST_SIZE_1 = (INPUT_DATA_SIZE/NUM_SEGMENTS) * OVERLAP_TEST_SPLIT_FACTOR;
    int OVERLAP_TEST_SIZE_2 = (INPUT_DATA_SIZE/NUM_SEGMENTS) - OVERLAP_TEST_SIZE_1;

    semaphore proc_lock; 
    initial proc_lock = new(1);
    semaphore mu_lock; 
    initial mu_lock = new(1);

    initial begin
        // Declare signals
        logic [CGRA_DATA_WIDTH-1:0] data_arr16 [];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg0[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg1[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg2[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg3[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_out [];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_out_byte_by_byte [];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_out_overlap [];
        logic [GLB_ADDR_WIDTH-1:0] start_addr;
        logic [TILE_SEL_ADDR_WIDTH-1:0] tile_sel;
        logic [TILE_SEL_ADDR_WIDTH - $clog2(MU_WORD_NUM_TILES) - 1:0] mu_rd_group_sel;

        logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg0[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg1[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg2[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg3[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg4[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg5[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg6[];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg7[];

        logic [MU_TL_SOURCE_WIDTH-1:0] source_out [];
        logic [MU_TL_NUM_BURST_BITS-1:0] size_out [];
        logic [MU_TL_SOURCE_WIDTH-1:0] golden_source_out [];
        logic [MU_TL_NUM_BURST_BITS-1:0] golden_size_out [];

        // Load data
        data_arr16 = new[INPUT_DATA_SIZE];
        data_arr16_out = new[INPUT_DATA_SIZE]; 
        data_arr16_seg0 = new[INPUT_DATA_SIZE/NUM_SEGMENTS];
        data_arr16_seg1 = new[INPUT_DATA_SIZE/NUM_SEGMENTS];
        data_arr16_seg2 = new[INPUT_DATA_SIZE/NUM_SEGMENTS];
        data_arr16_seg3 = new[INPUT_DATA_SIZE/NUM_SEGMENTS];
        load_data("testvectors/512_v1.dat", data_arr16, data_arr16_seg0, data_arr16_seg1, data_arr16_seg2, data_arr16_seg3);

        // Basic read-after-write test 
        run_basic_raw_test(NUM_GLB_TILES, MU_WORD_NUM_TILES, BANK_DEPTH, BURST_SIZE, 
                       start_addr, data_arr16, data_arr16_out, data_arr16_seg0, 
                       data_arr16_seg1, data_arr16_seg2, data_arr16_seg3);
       
        // Run byte-by-byte readout test 
        data_arr16_out_byte_by_byte = new[INPUT_DATA_SIZE]; 
        run_byte_by_byte_raw_test(NUM_GLB_TILES, MU_WORD_NUM_TILES, BANK_DEPTH, start_addr, 
                              data_arr16, data_arr16_out_byte_by_byte, data_arr16_seg0, 
                              data_arr16_seg1, data_arr16_seg2, data_arr16_seg3);
        
        // Load data custom for pt2 (overlap test)
        $display("\n---RUNNING OVERLAP TEST---");
        $display("OVERLAP TEST SIZE 1: %0d", OVERLAP_TEST_SIZE_1);
        $display("OVERLAP TEST SIZE 2: %0d", OVERLAP_TEST_SIZE_2);
        data_arr16_out_overlap = new[INPUT_DATA_SIZE]; 
        data_arr16_pt2_seg0 = new[OVERLAP_TEST_SIZE_1];
        data_arr16_pt2_seg1 = new[OVERLAP_TEST_SIZE_1];
        data_arr16_pt2_seg2 = new[OVERLAP_TEST_SIZE_1];
        data_arr16_pt2_seg3 = new[OVERLAP_TEST_SIZE_1];

        data_arr16_pt2_seg4 = new[OVERLAP_TEST_SIZE_2];
        data_arr16_pt2_seg5 = new[OVERLAP_TEST_SIZE_2];
        data_arr16_pt2_seg6 = new[OVERLAP_TEST_SIZE_2];
        data_arr16_pt2_seg7 = new[OVERLAP_TEST_SIZE_2];
        load_data_custom("testvectors/512_v1.dat", data_arr16, data_arr16_pt2_seg0, data_arr16_pt2_seg1, data_arr16_pt2_seg2, data_arr16_pt2_seg3,
                           data_arr16_pt2_seg4, data_arr16_pt2_seg5, data_arr16_pt2_seg6, data_arr16_pt2_seg7);

        // Run overlap test
        run_overlap_test(NUM_GLB_TILES, BANK_DEPTH, BURST_SIZE, OVERLAP_TEST_SIZE_1, start_addr, 
            data_arr16, data_arr16_pt2_seg0, data_arr16_pt2_seg1, data_arr16_pt2_seg2, data_arr16_pt2_seg3, 
            data_arr16_pt2_seg4, data_arr16_pt2_seg5, data_arr16_pt2_seg6, data_arr16_pt2_seg7, 
            data_arr16_out_overlap);


        // Run tilelink collateral test (testing proper tilelink resp out behavior)    
        source_out = new[9];
        size_out = new[9];
        golden_size_out = new[9];
        golden_source_out = new[9];
        $display("\n---RUNNING TILELINK COLLATERAL TEST---");
        MU_tilelink_collateral_test(golden_source_out, golden_size_out, source_out, size_out);
        verify_tl_size_out(golden_size_out, size_out);
        verify_tl_source_out(golden_source_out, source_out);

        repeat (50) @(posedge clk);

        $display("Time: %0t", $time);
        $display("Simulation exited normally\n");
        $finish;
    end

    task run_basic_raw_test(
        input int num_glb_tiles,
        input int mu_word_num_tiles,
        input int bank_depth,
        input int burst_size,
        input logic [GLB_ADDR_WIDTH-1:0] start_addr,
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_out[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg0[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg1[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg2[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg3[]
    );
        for (int glb_tile_base = 0; glb_tile_base < num_glb_tiles; glb_tile_base += mu_word_num_tiles) begin 
            for (int offset = 0; offset < bank_depth; offset += 32) begin         
                $display("\n---RUNNING BASIC RAW TEST WITH BASE %0d---", glb_tile_base);    

                // Initialize
                initialize(); 
                
                // Write data to 4 consecutive BANKS, starting from base tile
                write_data_to_banks(glb_tile_base, offset, start_addr, data_arr16_seg0, data_arr16_seg1, data_arr16_seg2, data_arr16_seg3);

                repeat (10) @(posedge p_ifc.clk);

                // Read data using MU-GLB read-path
                MU_read_data_from_banks(glb_tile_base, offset, burst_size, data_arr16_out);
            
                // Compare data
                compare_data(data_arr16, data_arr16_out);
            end
        end
    endtask


    task run_byte_by_byte_raw_test(
        input int num_glb_tiles,
        input int mu_word_num_tiles,
        input int bank_depth,
        input logic [GLB_ADDR_WIDTH-1:0] start_addr,
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_out_byte_by_byte[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg0[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg1[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg2[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg3[]
    );
        for (int glb_tile_base = 0; glb_tile_base < num_glb_tiles; glb_tile_base += mu_word_num_tiles) begin 
            for (int offset = 0; offset < bank_depth; offset += 32) begin         
                $display("\n---RUNNING BYTE-BY-BYTE RAW TEST WITH BASE %0d---", glb_tile_base);    

                // Initialize
                initialize(); 
                
                // Write data to 4 consecutive BANKS, starting from base tile
                write_data_to_banks(glb_tile_base, offset, start_addr, data_arr16_seg0, data_arr16_seg1, data_arr16_seg2, data_arr16_seg3);

                repeat (10) @(posedge p_ifc.clk);

                // Read data using MU-GLB read-path (byte-by-byte)
                MU_read_data_from_banks_byte_by_byte(glb_tile_base, offset, data_arr16_out_byte_by_byte);
            
                // Compare data
                compare_data(data_arr16, data_arr16_out_byte_by_byte);
            end
        end
    endtask

    task run_overlap_test(
        input int num_glb_tiles,
        input int bank_depth,
        input int burst_size,
        input int overlap_test_size_1,
        input logic [GLB_ADDR_WIDTH-1:0] start_addr,
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg0[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg1[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg2[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg3[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg4[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg5[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg6[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_pt2_seg7[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_out_overlap[]
    );
        for (int glb_tile_base = 0; glb_tile_base < num_glb_tiles - 2; glb_tile_base += 2) begin
            // Initialize
            initialize(); 

            $display("\n---RUNNING OVERLAP TEST ACROSS TILES %0d and %0d---", glb_tile_base, glb_tile_base + 2); 

            // Write all of the first group to the tail end of base tile 
            write_data_to_banks(glb_tile_base, bank_depth - (overlap_test_size_1 / 4), start_addr, data_arr16_pt2_seg0, data_arr16_pt2_seg1, data_arr16_pt2_seg2, data_arr16_pt2_seg3);

            // Write 2nd group at beginning of neighboring tiles
            write_data_to_banks(glb_tile_base + 2, 0, start_addr, data_arr16_pt2_seg4, data_arr16_pt2_seg5, data_arr16_pt2_seg6, data_arr16_pt2_seg7);

            repeat (10) @(posedge p_ifc.clk);

            // Read data using MU-GLB read-path
            MU_read_data_from_banks(glb_tile_base, bank_depth - (overlap_test_size_1 / 4), burst_size, data_arr16_out_overlap);

            // Compare data
            compare_data(data_arr16, data_arr16_out_overlap);
        end
    endtask

    task MU_tilelink_collateral_test (ref logic [MU_TL_SOURCE_WIDTH-1:0] golden_source_out[], ref logic [MU_TL_NUM_BURST_BITS-1:0] golden_size_out[], ref logic [MU_TL_SOURCE_WIDTH-1:0] source_out[], ref logic [MU_TL_NUM_BURST_BITS-1:0] size_out[]);
        
        initialize();

        golden_source_out[0] = 0;
        golden_source_out[1] = 0;
        golden_source_out[2] = 0;
        golden_source_out[3] = 0;
        golden_source_out[4] = 2;
        golden_source_out[5] = 1;
        golden_source_out[6] = 4;
        golden_source_out[7] = 4;
        golden_source_out[8] = 1;

        golden_size_out[0] = 7;
        golden_size_out[1] = 7;
        golden_size_out[2] = 7;
        golden_size_out[3] = 7;
        golden_size_out[4] = 5;
        golden_size_out[5] = 0;
        golden_size_out[6] = 6;
        golden_size_out[7] = 6;
        golden_size_out[8] = 0;
    
        mu_lock.get(1);
        fork
            // Process 1 initiates read by feeding addresses one per cycle when ready is high
            // Process 2 unloads the data by waiting for data_valid signal and then reading data one per cycle
            begin
                @(posedge glb_mu_ifc.clk);
                glb_mu_ifc.mu_rd_data_ready = 1'b1;
                glb_mu_ifc.mu_tl_rq_in_vld = 1;

                // 128B request on source 0: 4 beats
                glb_mu_ifc.mu_tl_source_in = 0;
                glb_mu_ifc.mu_tl_size_in = 7;

                wait (glb_mu_ifc.mu_tl_rq_in_rdy);
                @(posedge glb_mu_ifc.clk);

                // 32B request on source 2: 1 beat
                glb_mu_ifc.mu_tl_source_in = 2;
                glb_mu_ifc.mu_tl_size_in = 5;


                wait (glb_mu_ifc.mu_tl_rq_in_rdy);
                @(posedge glb_mu_ifc.clk);

                // 1B request on source 1 (inputScale): 1 beat
                glb_mu_ifc.mu_tl_source_in = 1;
                glb_mu_ifc.mu_tl_size_in = 0;

                wait (glb_mu_ifc.mu_tl_rq_in_rdy);
                @(posedge glb_mu_ifc.clk);

                // 64B request on source 4: 2 beats
                glb_mu_ifc.mu_tl_source_in = 4;
                glb_mu_ifc.mu_tl_size_in = 6;


                wait (glb_mu_ifc.mu_tl_rq_in_rdy);
                @(posedge glb_mu_ifc.clk);

                // 1B request on source 1 (inputScale): 1 beat
                glb_mu_ifc.mu_tl_source_in = 1;
                glb_mu_ifc.mu_tl_size_in = 0;

                wait (glb_mu_ifc.mu_tl_rq_in_rdy);
                @(posedge glb_mu_ifc.clk);

                glb_mu_ifc.mu_tl_rq_in_vld = 0;
            end
            begin
                // HERE: wait for the appropriate amount of data 
                for (int i = 0; i < 9; i++) begin
                    wait (glb_mu_ifc.mu_rd_data_valid);      

                    size_out[i] = glb_mu_ifc.mu_tl_size_out;
                    source_out[i] = glb_mu_ifc.mu_tl_source_out;                
                    
                    @(posedge glb_mu_ifc.clk);
                
                end
            end
        join
        repeat (10) @(posedge glb_mu_ifc.clk);
        mu_lock.put(1);
    endtask


    task initialize();
        p_ifc.wr_en   = 0;
        p_ifc.wr_strb = 0;
        p_ifc.wr_addr = 0;
        p_ifc.wr_data = 0;
        p_ifc.rd_addr = 0;
        p_ifc.rd_en = 0;

        glb_mu_ifc.mu_tl_addr_in = 0;
        glb_mu_ifc.mu_tl_rq_in_vld = 0;
        glb_mu_ifc.mu_tl_size_in = 0;
        glb_mu_ifc.mu_tl_source_in = 0;

        glb_mu_ifc.mu_rd_data_ready = 0;

        repeat (10) @(posedge clk);
        // wait for reset clear
        wait (reset == 0);
        repeat (10) @(posedge clk);
    endtask

    task automatic load_data(
        input string file_name,
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg0[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg1[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg2[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg3[]
    );
        $readmemh(file_name, data_arr16);
        for (int i = 0; i < INPUT_DATA_SIZE/NUM_SEGMENTS; i++) begin
            int x = int'(i / NUM_SEGMENTS) * 16 + (i % NUM_SEGMENTS);
            data_arr16_seg0[i] = data_arr16[x];
            data_arr16_seg1[i] = data_arr16[x + NUM_SEGMENTS * 1];
            data_arr16_seg2[i] = data_arr16[x + NUM_SEGMENTS * 2];
            data_arr16_seg3[i] = data_arr16[x + NUM_SEGMENTS * 3];
        end
    endtask

    int x_max;
    task automatic load_data_custom(
        input string file_name,
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg0[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg1[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg2[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg3[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg4[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg5[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg6[],
        ref logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg7[]
    );
        $readmemh(file_name, data_arr16);
        x_max = 0;
        for (int i = 0; i < OVERLAP_TEST_SIZE_1; i++) begin
            int x = int'(i / NUM_SEGMENTS) * 16 + (i % NUM_SEGMENTS);
            data_arr16_seg0[i] = data_arr16[x];
            data_arr16_seg1[i] = data_arr16[x + NUM_SEGMENTS * 1];
            data_arr16_seg2[i] = data_arr16[x + NUM_SEGMENTS * 2];
            data_arr16_seg3[i] = data_arr16[x + NUM_SEGMENTS * 3];
            x_max = x + (NUM_SEGMENTS * 3) + 1; // +1 to go to the next segment
        end

        for (int i = 0; i < OVERLAP_TEST_SIZE_2; i++) begin
            int x = int'(i / NUM_SEGMENTS) * 16 + (i % NUM_SEGMENTS) + x_max;
            data_arr16_seg4[i] = data_arr16[x];
            data_arr16_seg5[i] = data_arr16[x + NUM_SEGMENTS * 1];
            data_arr16_seg6[i] = data_arr16[x + NUM_SEGMENTS * 2];
            data_arr16_seg7[i] = data_arr16[x + NUM_SEGMENTS * 3];
        end
    endtask


    task write_data_to_banks(
        input logic [TILE_SEL_ADDR_WIDTH-1:0] tile_base,
        input int offset,
        input logic [GLB_ADDR_WIDTH-1:0] start_addr,
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg0[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg1[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg2[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_seg3[]
    );
        start_addr = (tile_base << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) + (offset * (2 **(BANK_BYTE_OFFSET)));
        $display("Writing data starting at address %0h", start_addr);
        ProcDriver_write_data(start_addr, data_arr16_seg0);

        start_addr = (((tile_base) << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) | 
                      (1 << BANK_ADDR_WIDTH)) + (offset * (2 **(BANK_BYTE_OFFSET)));
        ProcDriver_write_data(start_addr, data_arr16_seg1);

        start_addr = ((tile_base + 1) << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) + (offset * (2 **(BANK_BYTE_OFFSET)));
        ProcDriver_write_data(start_addr, data_arr16_seg2);

        start_addr =  (((tile_base + 1) << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) | 
                      (1 << BANK_ADDR_WIDTH)) + (offset * (2 **(BANK_BYTE_OFFSET)));
        ProcDriver_write_data(start_addr, data_arr16_seg3);
    endtask


    task MU_read_data_from_banks(
        input logic [TILE_SEL_ADDR_WIDTH-1:0] tile_sel_base,
        input int offset,
        input int burst_size,
        ref logic [CGRA_DATA_WIDTH-1:0] data_out[]
    );
        logic [TILE_SEL_ADDR_WIDTH - $clog2(MU_WORD_NUM_TILES) - 1:0] mu_rd_group_sel;
        logic [MU_ADDR_WIDTH-1:0] mu_rd_start_addr;
        logic [MU_TL_NUM_BURST_BITS-1:0] mu_rd_burst_size;

        // Mask away unnecessary bits from tile ID
        mu_rd_group_sel = tile_sel_base[TILE_SEL_ADDR_WIDTH - 1 : $clog2(MU_WORD_NUM_TILES)];
        mu_rd_start_addr = (mu_rd_group_sel << (MU_ADDR_WIDTH - (TILE_SEL_ADDR_WIDTH - $clog2(MU_WORD_NUM_TILES)))) + (offset * (2 **(BANK_BYTE_OFFSET + BANK_SEL_ADDR_WIDTH + $clog2(MU_WORD_NUM_TILES))));
        mu_rd_burst_size = $clog2(burst_size);
        $display("Reading with burst size %d starting at MU (untranslated) input address %0h.", BURST_SIZE, mu_rd_start_addr);
        MUDriver_read_data(mu_rd_start_addr, mu_rd_burst_size, data_out);
    endtask


    task MU_read_data_from_banks_byte_by_byte(
        input logic [TILE_SEL_ADDR_WIDTH-1:0] tile_sel_base,
        input int offset,
        ref logic [CGRA_DATA_WIDTH-1:0] data_out[]
    );
        logic [TILE_SEL_ADDR_WIDTH - $clog2(MU_WORD_NUM_TILES) - 1:0] mu_rd_group_sel;
        logic [MU_ADDR_WIDTH-1:0] mu_rd_start_addr;
        logic [MU_TL_NUM_BURST_BITS-1:0] mu_rd_burst_size;

        // Mask away unnecessary bits from tile ID
        mu_rd_group_sel = tile_sel_base[TILE_SEL_ADDR_WIDTH - 1 : $clog2(MU_WORD_NUM_TILES)];
        mu_rd_start_addr = (mu_rd_group_sel << (MU_ADDR_WIDTH - (TILE_SEL_ADDR_WIDTH - $clog2(MU_WORD_NUM_TILES)))) + (offset * (2 **(BANK_BYTE_OFFSET + BANK_SEL_ADDR_WIDTH + $clog2(MU_WORD_NUM_TILES))));
        $display("Reading byte-by-byte starting at MU (untranslated) input address %0h.", mu_rd_start_addr);
        MUDriver_read_data_byte_by_byte(mu_rd_start_addr, data_out);
    endtask


       
    task compare_data(
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16[],
        input logic [CGRA_DATA_WIDTH-1:0] data_arr16_out[]
    );
        int err;
        // Compare data
        err = compare_16b_arr(data_arr16, data_arr16_out);
        if (err == 0) begin
            $display("Test passed!");
        end else begin
            $error("Test failed!");
        end
    endtask

    task verify_tl_size_out(
        input logic [MU_TL_NUM_BURST_BITS-1:0] golden_size_out[],
        input logic [MU_TL_NUM_BURST_BITS-1:0] size_out[]
    );
        int err;
        // Compare data
        err = compare_size_arrs(golden_size_out, size_out);
        if (err == 0) begin
            $display("Test passed!");
        end else begin
            $error("Test failed!");
        end
    endtask

    task verify_tl_source_out(
        input logic [MU_TL_SOURCE_WIDTH-1:0] golden_source_out[],
        input logic [MU_TL_SOURCE_WIDTH-1:0] source_out[]
    );
        int err;
        // Compare data
        err = compare_source_arrs(golden_source_out, source_out);
        if (err == 0) begin
            $display("Test passed!");
        end else begin
            $error("Test failed!");
        end
    endtask


    int size;
    bit [BANK_DATA_WIDTH-1:0] bdata;
    bit [GLB_ADDR_WIDTH-1:0] cur_addr;
    task ProcDriver_write_data(input [GLB_ADDR_WIDTH-1:0] start_addr, logic [CGRA_DATA_WIDTH-1:0] data_q[]);
        cur_addr = start_addr;
        proc_lock.get(1);
        size = data_q.size();  
        for (int i = 0; i < size; i += 4) begin
            if ((i + 1) == size) begin
                bdata = data_q[i];
            end else if ((i + 2) == size) begin
                bdata = {data_q[i+1], data_q[i]};
            end else if ((i + 3) == size) begin
                bdata = {data_q[i+2], data_q[i+1], data_q[i]};
            end else begin
                bdata = {data_q[i+3], data_q[i+2], data_q[i+1], data_q[i]};
            end
            ProcDriver_write(cur_addr, bdata);
            cur_addr += 8;  
        end
        repeat (10) @(posedge p_ifc.clk);
        proc_lock.put(1);
    endtask

    task ProcDriver_write(input [GLB_ADDR_WIDTH-1:0] addr, [BANK_DATA_WIDTH-1:0] data);
        p_ifc.wr_en   = 1'b1;
        p_ifc.wr_strb = {(BANK_DATA_WIDTH / 8) {1'b1}};
        p_ifc.wr_addr = addr;
        p_ifc.wr_data = data;
        @(posedge p_ifc.clk);
        p_ifc.wr_en   = 0;
        p_ifc.wr_strb = 0;
        p_ifc.wr_addr = 0;
        p_ifc.wr_data = 0;
    endtask

    int num_words, num_trans;
    task ProcDriver_read_data(input [GLB_ADDR_WIDTH-1:0] start_addr, ref logic [CGRA_DATA_WIDTH-1:0] data_q[]);
        num_words = data_q.size();  
        num_trans = (num_words + 3) / 4;  
        proc_lock.get(1);
        fork
            // Process 1 initiates read by setting rd_en HIGH and feeding addresses one per cycle
            // Process 2 unloads the data by waiting for data_valid signal and then reading data one per cycle
            begin
                $display("Set     %0d consecutive addresses BEGIN", num_trans);
                @(posedge p_ifc.clk);
                for (int i = 0; i < num_trans; i++) begin
                    p_ifc.rd_en = 1'b1;
                    // address increases by 8 every write
                    p_ifc.rd_addr = (start_addr + 8 * i);
                    @(posedge p_ifc.clk);
                end
                p_ifc.rd_en   = 0;
                p_ifc.rd_addr = 0;
            end
            begin
                for (int i = 0; i < num_trans; i++) begin
                    wait (p_ifc.rd_data_valid);      
                    // wait (glb_mu_ifc.mu_rd_data_valid);  

                    data_q[i*4] = p_ifc.rd_data & 'hFFFF;

                    if ((i * 4 + 1) < num_words) begin
                        data_q[i*4+1] = (p_ifc.rd_data & (('hFFFF) << 16)) >> 16;
                    end

                    if ((i * 4 + 2) < num_words) begin
                        data_q[i*4+2] = (p_ifc.rd_data & (('hFFFF) << 32)) >> 32;
                    end

                    if ((i * 4 + 3) < num_words) begin
                        data_q[i*4+3] = (p_ifc.rd_data & (('hFFFF) << 48)) >> 48;
                    end

                    @(posedge p_ifc.clk);
                
                end
    
            end
        join
        repeat (10) @(posedge p_ifc.clk);
        proc_lock.put(1);
    endtask

    int num_mu_words, num_mu_trans, num_mu_addr_trans, mask, RANDOM_DELAY;
    task MUDriver_read_data(input [MU_ADDR_WIDTH-1:0] start_addr, input [MU_TL_NUM_BURST_BITS-1:0] burst_size, ref logic [CGRA_DATA_WIDTH-1:0] data_q[]);
        num_mu_words = data_q.size();  
        num_mu_trans = (num_mu_words + 3) / 16; 
        if (BURST_SIZE <= (MU_WORD_WIDTH / 8)) begin
            num_mu_addr_trans = num_mu_trans ;
        end else begin
            num_mu_addr_trans = num_mu_trans / (BURST_SIZE / (MU_WORD_WIDTH / 8));
        end 
        
        mu_lock.get(1);
        fork
            // Process 1 initiates read by feeding addresses one per cycle when ready is high
            // Process 2 unloads the data by waiting for data_valid signal and then reading data one per cycle
            begin
                $display("Set     %0d consecutive addresses BEGIN", num_mu_trans);
                @(posedge glb_mu_ifc.clk);
                for (int i = 0; i < num_mu_addr_trans; i++) begin
                    glb_mu_ifc.mu_rd_data_ready = 1'b1;
                    // Add random bubbles to input
                    glb_mu_ifc.mu_tl_rq_in_vld = 0;
                    mask = 32'd3 << RANDOM_SHIFT;
                    RANDOM_DELAY = $urandom & mask;
                    RANDOM_DELAY = RANDOM_DELAY >> RANDOM_SHIFT;
                    while (RANDOM_DELAY > 0 & ADD_INPUT_BUBBLES) begin
                        @(posedge glb_mu_ifc.clk);
                        RANDOM_DELAY--;
                    end

                    glb_mu_ifc.mu_tl_rq_in_vld = 1'b1;
                    // address increases by 8 * BURST_SIZE every read
                    if (BURST_SIZE <= (MU_WORD_WIDTH / 8)) begin
                        glb_mu_ifc.mu_tl_addr_in = (start_addr + (MU_WORD_WIDTH / 8) * i);
                    end else begin
                        glb_mu_ifc.mu_tl_addr_in = (start_addr + BURST_SIZE * i);
                    end
                    glb_mu_ifc.mu_tl_size_in = burst_size;
                    // glb_mu_ifc.mu_tl_source_in = (i % 5);
                    wait (glb_mu_ifc.mu_tl_rq_in_rdy);
                    @(posedge glb_mu_ifc.clk);
                end
                glb_mu_ifc.mu_tl_addr_in = 0;
                glb_mu_ifc.mu_tl_rq_in_vld = 0;
            end
            begin
                for (int i = 0; i < num_mu_trans; i++) begin
                    wait (glb_mu_ifc.mu_rd_data_valid);      

                    data_q[i*16] = glb_mu_ifc.mu_rd_data & 'hFFFF;

                    if ((i * 16 + 1) < num_mu_words) begin
                        data_q[i*16+1] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 16)) >> 16;
                    end

                    if ((i * 16 + 2) < num_mu_words) begin
                        data_q[i*16+2] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 32)) >> 32;
                    end

                    if ((i * 16 + 3) < num_mu_words) begin
                        data_q[i*16+3] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 48)) >> 48;
                    end

                    if ((i * 16 + 4) < num_mu_words) begin
                        data_q[i*16+4] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 64)) >> 64;
                    end

                    if ((i * 16 + 5) < num_mu_words) begin
                        data_q[i*16+5] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 80)) >> 80;
                    end

                    if ((i * 16 + 6) < num_mu_words) begin
                        data_q[i*16+6] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 96)) >> 96;
                    end

                    if ((i * 16 + 7) < num_mu_words) begin
                        data_q[i*16+7] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 112)) >> 112;
                    end

                    if ((i * 16 + 8) < num_mu_words) begin
                        data_q[i*16+8] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 128)) >> 128;
                    end

                    if ((i * 16 + 9) < num_mu_words) begin
                        data_q[i*16+9] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 144)) >> 144;
                    end

                    if ((i * 16 + 10) < num_mu_words) begin
                        data_q[i*16+10] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 160)) >> 160;
                    end

                    if ((i * 16 + 11) < num_mu_words) begin
                        data_q[i*16+11] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 176)) >> 176;
                    end

                    if ((i * 16 + 12) < num_mu_words) begin
                        data_q[i*16+12] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 192)) >> 192;
                    end

                    if ((i * 16 + 13) < num_mu_words) begin
                        data_q[i*16+13] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 208)) >> 208;
                    end

                    if ((i * 16 + 14) < num_mu_words) begin
                        data_q[i*16+14] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 224)) >> 224;
                    end

                    if ((i * 16 + 15) < num_mu_words) begin
                        data_q[i*16+15] = (glb_mu_ifc.mu_rd_data & (('hFFFF) << 240)) >> 240;
                    end    
                    
                    @(posedge glb_mu_ifc.clk);
                
                end
    
            end
        join
        repeat (10) @(posedge glb_mu_ifc.clk);
        mu_lock.put(1);
    endtask


    int num_mu_words, num_mu_trans, num_mu_addr_trans, mask, RANDOM_DELAY;
    task MUDriver_read_data_byte_by_byte(input [MU_ADDR_WIDTH-1:0] start_addr, ref logic [CGRA_DATA_WIDTH-1:0] data_q[]);
        num_mu_words = data_q.size();  
        num_mu_trans = (num_mu_words) * 2; 
        num_mu_addr_trans = num_mu_trans ;
       
        mu_lock.get(1);
        fork
            // Process 1 initiates read by feeding addresses one per cycle when ready is high
            // Process 2 unloads the data by waiting for data_valid signal and then reading data one per cycle
            begin
                $display("Set     %0d consecutive addresses BEGIN", num_mu_trans);
                @(posedge glb_mu_ifc.clk);
                for (int i = 0; i < num_mu_addr_trans; i++) begin
                    glb_mu_ifc.mu_rd_data_ready = 1'b1;
                    // Add random bubbles to input
                    glb_mu_ifc.mu_tl_rq_in_vld = 0;
                    mask = 32'd3 << RANDOM_SHIFT;
                    RANDOM_DELAY = $urandom & mask;
                    RANDOM_DELAY = RANDOM_DELAY >> RANDOM_SHIFT;
                    while (RANDOM_DELAY > 0 & ADD_INPUT_BUBBLES) begin
                        @(posedge glb_mu_ifc.clk);
                        RANDOM_DELAY--;
                    end

                    glb_mu_ifc.mu_tl_rq_in_vld = 1'b1;
                    // address increases by 1 (byte-by-byte) every read
                    glb_mu_ifc.mu_tl_addr_in = (start_addr + i);
                   
                    glb_mu_ifc.mu_tl_size_in = 0;
                    glb_mu_ifc.mu_tl_source_in = INPUT_SCALE_REQ_SRC_CODE; 
                    wait (glb_mu_ifc.mu_tl_rq_in_rdy);
                    @(posedge glb_mu_ifc.clk);
                end
                glb_mu_ifc.mu_tl_addr_in = 0;
                glb_mu_ifc.mu_tl_rq_in_vld = 0;
            end
            begin
                for (int i = 0; i < num_mu_trans; i++) begin
                    wait (glb_mu_ifc.mu_rd_data_valid);      

                    if ((i % 2) == 0) begin
                        data_q[int'(i/2)] = {7'b0, glb_mu_ifc.mu_rd_data[7:0]};
                    end else begin
                        data_q[int'(i/2)] |= (glb_mu_ifc.mu_rd_data[7:0]) << 8;
                    end

                    @(posedge glb_mu_ifc.clk);
                
                end
    
            end
        join
        repeat (10) @(posedge glb_mu_ifc.clk);
        mu_lock.put(1);
    endtask


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


    function automatic int compare_source_arrs(ref [MU_TL_SOURCE_WIDTH-1:0] data_arr_0[], ref [MU_TL_SOURCE_WIDTH-1:0] data_arr_1[]);
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


    function automatic int compare_size_arrs(ref [MU_TL_NUM_BURST_BITS-1:0] data_arr_0[], ref [MU_TL_NUM_BURST_BITS-1:0] data_arr_1[]);
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

    



    


//    `include "tb/environment.sv"
endprogram
