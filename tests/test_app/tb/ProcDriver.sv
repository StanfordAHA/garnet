// class ProcDriver;

`define DBG_PROCDRIVER 0
// `define DBG_PROCDRIVER 1  // for debugging

// function ProcDriver::new(vProcIfcDriver vif, semaphore proc_lock);
// NOT NEEDED b/c not a class no more

semaphore proc_lock; 
initial begin
   proc_lock = new(1);
end

////////////////////////////////////////////////////////////////////////
// task ProcDriver::write_bs(int start_addr, bitstream_t bs_q);
bit [GLB_ADDR_WIDTH-1:0] ProcDriver_write_bs_start_addr;
bit [GLB_ADDR_WIDTH-1:0] ProcDriver_write_bs_cur_addr;
bitstream_t              ProcDriver_write_bs_bs_q;

bit [GLB_ADDR_WIDTH-1:0]  ProcDriver_write_waddr;
bit [BANK_DATA_WIDTH-1:0] ProcDriver_write_wdata;


task ProcDriver_write_bs();
   ProcDriver_write_bs_cur_addr = ProcDriver_write_bs_start_addr;
   proc_lock.get(1);
   foreach (ProcDriver_write_bs_bs_q[i]) begin

      // write(cur_addr, bs_q[i]);
      ProcDriver_write_waddr = ProcDriver_write_bs_cur_addr;
      ProcDriver_write_wdata = ProcDriver_write_bs_bs_q[i];
      ProcDriver_write();

      ProcDriver_write_bs_cur_addr += 8;
   end
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
endtask // ProcDriver_write_bs
    

////////////////////////////////////////////////////////////////////////
// task ProcDriver::write_data(int start_addr, data_array_t data_q);
int PD_wd_start_addr;
data_array_t PD_wd_data_q;
bit [GLB_ADDR_WIDTH-1:0] PD_wd_cur_addr;
bit [BANK_DATA_WIDTH-1:0] PD_wd_data;
int PD_wd_size;

task ProcDriver_write_data();
    $display("ProcDriver_write_data() BEGIN"); $fflush();  // 1720ns
    PD_wd_cur_addr = PD_wd_start_addr;
    proc_lock.get(1);
    assert (BANK_DATA_WIDTH == 64);
    PD_wd_size = PD_wd_data_q.size();  // 0x1000 = 2^12 = 4K??

    for (int i = 0; i < PD_wd_size; i += 4) begin
        if ((i + 1) == PD_wd_size) begin
            PD_wd_data = PD_wd_data_q[i];
        end else if ((i + 2) == PD_wd_size) begin
            PD_wd_data = {PD_wd_data_q[i+1], PD_wd_data_q[i]};
        end else if ((i + 3) == PD_wd_size) begin
            PD_wd_data = {PD_wd_data_q[i+2], PD_wd_data_q[i+1], PD_wd_data_q[i]};
        end else begin
            PD_wd_data = {PD_wd_data_q[i+3], PD_wd_data_q[i+2], PD_wd_data_q[i+1], PD_wd_data_q[i]};
        end
        // write(PD_wd_cur_addr, PD_wd_data);
            ProcDriver_write_waddr = PD_wd_cur_addr;
            ProcDriver_write_wdata = PD_wd_data;
            ProcDriver_write();
        PD_wd_cur_addr += 8;  // Counts hex 8,10,18,20...(8x2^10 == 0x1000
    end
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
    $display("ProcDriver_write_data() END");
endtask // ProcDriver_write_data


////////////////////////////////////////////////////////////////////////
// task ProcDriver::write(int addr, bit [BANK_DATA_WIDTH-1:0] data);
// int                            ProcDriver_write_waddr;
// bit [BANK_DATA_WIDTH-1:0]      ProcDriver_write_wdata;

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


////////////////////////////////////////////////////////////////////////
// task ProcDriver::read_data(int start_addr, ref data_array_t data_q);
// start_addr and ProcDriver_read_data_num_data_q must be loaded by caller, see.
int PD_rdata_start_addr;
int PD_rdata_num_words;
int PD_rdata_num_trans;
data_array_t PD_rdata_data_q;
task ProcDriver_read_data();
    $display("Welcome to ProcDriver_read_data()"); $fflush();  // 3002ns
    PD_rdata_num_words = PD_rdata_data_q.size();        // Should be 4K / 0x1000?
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
              $display("\n\nFOO plan is to read beginning at address %08x\n", PD_rdata_start_addr);
            @(posedge p_ifc.clk);
            for (int i = 0; i < PD_rdata_num_trans; i++) begin
                p_ifc.rd_en = 1'b1;
                // address increases by 8 every write
                p_ifc.rd_addr = (PD_rdata_start_addr + 8 * i);
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

                PD_rdata_data_q[i*4] = p_ifc.rd_data & 'hFFFF;
                if (`DBG_PROCDRIVER)
                  $display("[%0t] -- 0 PD_rdata_data_q[%04d] <= %0x", $time, i*4, PD_rdata_data_q[i*4]);

                if ((i * 4 + 1) < PD_rdata_num_words) begin
                    PD_rdata_data_q[i*4+1] = (p_ifc.rd_data & (('hFFFF) << 16)) >> 16;
                    if (`DBG_PROCDRIVER)
                      $display("[%0t] -- 1 PD_rdata_data_q[%04d] <= %0x", $time, i*4+1, PD_rdata_data_q[i*4+1]);
                end

                if ((i * 4 + 2) < PD_rdata_num_words) begin
                    PD_rdata_data_q[i*4+2] = (p_ifc.rd_data & (('hFFFF) << 32)) >> 32;
                    if (`DBG_PROCDRIVER)
                      $display("[%0t] -- 2 PD_rdata_data_q[%04d] <= %0x", $time, i*4+2, PD_rdata_data_q[i*4+2]);
                end

                if ((i * 4 + 3) < PD_rdata_num_words) begin
                    PD_rdata_data_q[i*4+3] = (p_ifc.rd_data & (('hFFFF) << 48)) >> 48;
                    if (`DBG_PROCDRIVER)
                      $display("[%0t] -- 3 PD_rdata_data_q[%04d] <= %0x", $time, i*4+3, PD_rdata_data_q[i*4+3]);
                end

                if (`DBG_PROCDRIVER) $display("");

                // FIXME somebody needs to figure out why vcs and verilator are different here!!!
                one_cy_delay_if_vcs();
            end
            $display("Offload %d data chunks END", PD_rdata_num_trans);  // 4027ns
            $display("First output word is maybe...0x%04x",  PD_rdata_data_q[0]);
        end
    join
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
endtask
