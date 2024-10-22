semaphore proc_lock;
initial begin
   proc_lock = new(1);
end

////////////////////////////////////////////////////////////////////////
// task ProcDriver::write_bs(int start_addr, bitstream_t bs_q);
bit [GLB_ADDR_WIDTH-1:0] ProcDriver_write_bs_start_addr;
bit [GLB_ADDR_WIDTH-1:0] ProcDriver_write_bs_cur_addr;
bitstream_t              ProcDriver_write_bs_bs_q;

task ProcDriver_write_bs();
   ProcDriver_write_bs_cur_addr = ProcDriver_write_bs_start_addr;
   proc_lock.get(1);
   foreach (ProcDriver_write_bs_bs_q[i]) begin

      // write(cur_addr, bs_q[i]);
      ProcDriver_write_addr = ProcDriver_write_bs_cur_addr;
      ProcDriver_write_data = ProcDriver_write_bs_bs_q[i];
      ProcDriver_write();

      ProcDriver_write_bs_cur_addr += 8;
   end
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
endtask

////////////////////////////////////////////////////////////////////////
// task ProcDriver::write(int addr, bit [BANK_DATA_WIDTH-1:0] data);
int                            ProcDriver_write_addr;
bit [BANK_DATA_WIDTH-1:0]      ProcDriver_write_data;

task ProcDriver_write();
    p_ifc.wr_en   = 1'b1;
    p_ifc.wr_strb = {(BANK_DATA_WIDTH / 8) {1'b1}};
    p_ifc.wr_addr = ProcDriver_write_addr;
    p_ifc.wr_data = ProcDriver_write_data;
    @(posedge p_ifc.clk);
    p_ifc.wr_en   = 0;
    p_ifc.wr_strb = 0;
    p_ifc.wr_addr = 0;
    p_ifc.wr_data = 0;
endtask
