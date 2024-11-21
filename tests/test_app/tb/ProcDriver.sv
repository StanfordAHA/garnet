`define DBG_PROCDRIVER 0  // Set to '1' for debugging

semaphore proc_lock; 
initial proc_lock = new(1);

bit [GLB_ADDR_WIDTH-1:0] start_addr;
bit [GLB_ADDR_WIDTH-1:0] cur_addr;
bitstream_t              bs_q;

bit [GLB_ADDR_WIDTH-1:0]  ProcDriver_write_waddr;
bit [BANK_DATA_WIDTH-1:0] ProcDriver_write_wdata;

task ProcDriver_write_bs();
    cur_addr = start_addr;
    proc_lock.get(1);
    foreach (bs_q[i]) begin
        ProcDriver_write_waddr = cur_addr;
        ProcDriver_write_wdata = bs_q[i];
        ProcDriver_write();
        cur_addr += 8;
    end
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
endtask

data_array_t data_q;
bit [GLB_ADDR_WIDTH-1:0] cur_addr;
int size;

// TODO: Change it to const ref
task ProcDriver_write_data();
    cur_addr = start_addr;
    proc_lock.get(1);
    assert (BANK_DATA_WIDTH == 64);
    size = data_q.size();  // 0x1000 = 2^12 = 4K??
    for (int i = 0; i < size; i += 4) begin
        if ((i + 1) == size) begin
            data = data_q[i];
        end else if ((i + 2) == size) begin
            data = {data_q[i+1], data_q[i]};
        end else if ((i + 3) == size) begin
            data = {data_q[i+2], data_q[i+1], data_q[i]};
        end else begin
            data = {data_q[i+3], data_q[i+2], data_q[i+1], data_q[i]};
        end
        ProcDriver_write_waddr = cur_addr;
        ProcDriver_write_wdata = data;
        ProcDriver_write();
        cur_addr += 8;  // Counts hex 8,10,18,20...(8x2^10 == 0x1000
    end
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
endtask


/* temp registration block
task ProcDriver::write(int addr, bit [BANK_DATA_WIDTH-1:0] data);
*/
task ProcDriver_write();
    p_ifc.wr_en   = 1'b1;
    p_ifc.wr_strb = {(BANK_DATA_WIDTH / 8) {1'b1}};
    p_ifc.wr_addr = ProcDriver_write_waddr;
    p_ifc.wr_data = ProcDriver_write_wdata;
    @(posedge p_ifc.clk);
    p_ifc.wr_en   = 0;
    p_ifc.wr_strb = 0;
    p_ifc.wr_addr = 0;
    p_ifc.wr_data = 0;
endtask

//bookmark
////////////////////////////////////////////////////////////////////////
// task ProcDriver::read_data(int start_addr, ref data_array_t data_q);
// start_addr and ProcDriver_read_data_num_data_q must be loaded by caller, see.
int PD_rdata_num_words;
int PD_rdata_num_trans;
task ProcDriver_read_data();
    $display("Welcome to ProcDriver_read_data()"); $fflush();  // 3002ns
    PD_rdata_num_words = data_q.size();        // Should be 4K / 0x1000?
    PD_rdata_num_trans = (PD_rdata_num_words + 3) / 4;  // Should be 1K
    proc_lock.get(1);
    fork
        // Process 1 initiates read by setting rd_en HIGH and feeding addresses one per cycle
        // Process 2 unloads the data by waiting for data_valid signal and then reading data one per cycle
        begin
            // 3002ns
            // Counts from 10000 to...? 12000? by 8's
            // 0x10000 + 8 x 0x400 = 0x10000 + 0x2000 = 0x12000?
            $display("Set     %0d consecutive addresses BEGIN", PD_rdata_num_trans);  // 3002ns
            if (`DBG_PROCDRIVER) 
              $display("\n\nFOO plan is to read beginning at address %08x\n", start_addr);
            @(posedge p_ifc.clk);
            for (int i = 0; i < PD_rdata_num_trans; i++) begin
                p_ifc.rd_en = 1'b1;
                // address increases by 8 every write
                p_ifc.rd_addr = (start_addr + 8 * i);
                if (`DBG_PROCDRIVER) $display("[%0t] Set addr = %08x", $time, p_ifc.rd_addr);
                @(posedge p_ifc.clk);
            end
            p_ifc.rd_en   = 0;
            p_ifc.rd_addr = 0;
            $display("Set %d consecutive addresses END", PD_rdata_num_trans);  // 4027ns
        end
        // 4096 words means 1024 tansactions
        // So. When garnet.v is stubbed out, this takes 1K cycles to read 1K zeroes...
        begin
            $display("Offload %0d data chunks BEGIN", PD_rdata_num_trans);  // 3002ns
            for (int i = 0; i < PD_rdata_num_trans; i++) begin
                wait (p_ifc.rd_data_valid);  // This queers the deal if stub not hip...

                // VCS data ready same cycle as valid sig arrives
                // Vvverilator data not ready until one cycle AFTER valid signal
                // FIXME this is a bug, somebody needs to figure out why timing is different!!!
                one_cy_delay_if_verilator();

                if (`DBG_PROCDRIVER)
                  $display("\n[%0t] FOO got data word %0x", $time, p_ifc.rd_data);

                data_q[i*4] = p_ifc.rd_data & 'hFFFF;
                if (`DBG_PROCDRIVER)
                  $display("[%0t] -- 0 data_q[%04d] <= %0x", $time, i*4, data_q[i*4]);

                if ((i * 4 + 1) < PD_rdata_num_words) begin
                    data_q[i*4+1] = (p_ifc.rd_data & (('hFFFF) << 16)) >> 16;
                    if (`DBG_PROCDRIVER)
                      $display("[%0t] -- 1 data_q[%04d] <= %0x", $time, i*4+1, data_q[i*4+1]);
                end

                if ((i * 4 + 2) < PD_rdata_num_words) begin
                    data_q[i*4+2] = (p_ifc.rd_data & (('hFFFF) << 32)) >> 32;
                    if (`DBG_PROCDRIVER)
                      $display("[%0t] -- 2 data_q[%04d] <= %0x", $time, i*4+2, data_q[i*4+2]);
                end

                if ((i * 4 + 3) < PD_rdata_num_words) begin
                    data_q[i*4+3] = (p_ifc.rd_data & (('hFFFF) << 48)) >> 48;
                    if (`DBG_PROCDRIVER)
                      $display("[%0t] -- 3 data_q[%04d] <= %0x", $time, i*4+3, data_q[i*4+3]);
                end

                if (`DBG_PROCDRIVER) $display("");

                // FIXME somebody needs to figure out why vcs and verilator are different here!!!
                one_cy_delay_if_vcs();
            end
            $display("Offload %d data chunks END", PD_rdata_num_trans);  // 4027ns
            $display("First output word is maybe...0x%04x",  data_q[0]);
        end
    join
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
endtask
