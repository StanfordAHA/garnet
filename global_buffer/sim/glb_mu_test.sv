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
    int test_toggle = 0;
    int value;
    int dpr = 0;
    int err = 0;
    const int MAX_NUM_ERRORS = 20;

    semaphore proc_lock; 
    initial proc_lock = new(1);

    initial begin
        logic [CGRA_DATA_WIDTH-1:0] data_arr16 [];
        logic [CGRA_DATA_WIDTH-1:0] data_arr16_out [];
        logic [GLB_ADDR_WIDTH-1:0] start_addr;

        // Load data
        data_arr16 = new[512];
        $readmemh("testvectors/512_v1.dat", data_arr16);

        // Initiialize
        initialize(); 
  
        // Write data
        // Start from glb tile 5
        start_addr = 'hA0000;
        ProcDriver_write_data(start_addr, data_arr16);

        repeat (10) @(posedge p_ifc.clk);

        // Read data
        data_arr16_out = new[512];
        ProcDriver_read_data(start_addr, data_arr16_out);

        // Compare data
        err = compare_16b_arr(data_arr16, data_arr16_out);
        if (err == 0) begin
            $display("Test passed!");
        end else begin
            $error("Test failed!");
        end

        $display("Time: %0t", $time);
        $display("Simulation exited normally\n");
        $finish;
    end


    task initialize();
        p_ifc.wr_en   = 0;
        p_ifc.wr_strb = 0;
        p_ifc.wr_addr = 0;
        p_ifc.wr_data = 0;
        p_ifc.rd_addr = 0;
        p_ifc.rd_en = 0;

        glb_mu_ifc.mu_rd_addr = 0;
        glb_mu_ifc.mu_rd_en = 0;

        repeat (10) @(posedge clk);
        // wait for reset clear
        wait (reset == 0);
        repeat (10) @(posedge clk);
    endtask

    int size;
    bit [BANK_DATA_WIDTH-1:0] bdata;
    bit [GLB_ADDR_WIDTH-1:0] cur_addr;
    task ProcDriver_write_data(input [GLB_ADDR_WIDTH-1:0] start_addr, logic [CGRA_DATA_WIDTH-1:0] data_q[]);
        cur_addr = start_addr;
        proc_lock.get(1);
        size = data_q.size();  // 0x1000 = 2^12 = 4K??
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
        num_trans = (num_words + 3) / 4;  // Should be 1K
        proc_lock.get(1);
        fork
            // Process 1 initiates read by setting rd_en HIGH and feeding addresses one per cycle
            // Process 2 unloads the data by waiting for data_valid signal and then reading data one per cycle
            begin
                $display("Set     %0d consecutive addresses BEGIN", num_trans);
                @(posedge p_ifc.clk);
                for (int i = 0; i < num_trans; i++) begin
                    p_ifc.rd_en = 1'b1;
                    // glb_mu_ifc.mu_rd_en = 1'b1;
                    // address increases by 8 every write
                    p_ifc.rd_addr = (start_addr + 8 * i);
                    // glb_mu_ifc.mu_rd_addr = (start_addr + 8 * i);
                    @(posedge p_ifc.clk);
                end
                p_ifc.rd_en   = 0;
                p_ifc.rd_addr = 0;
                // glb_mu_ifc.mu_rd_en = 0;
                // glb_mu_ifc.mu_rd_addr = 0;
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

    


//    `include "tb/environment.sv"
endprogram
