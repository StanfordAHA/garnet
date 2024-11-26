// Global signals to replace/enhance class automatics
`define DBG_PROCDRIVER 0  // Set to '1' for debugging

bit [GLB_ADDR_WIDTH-1:0] start_addr;
bit [GLB_ADDR_WIDTH-1:0] cur_addr;
bitstream_t              bs_q;

bit [GLB_ADDR_WIDTH-1:0]  ProcDriver_write_waddr;
bit [BANK_DATA_WIDTH-1:0] ProcDriver_write_wdata;

class ProcDriver;
    vProcIfcDriver vif;
    semaphore proc_lock;

    extern function new(vProcIfcDriver vif, semaphore proc_lock);
    extern task write_bs(int start_addr, bitstream_t bs_q);
    extern task write_data(int start_addr, data_array_t data_q);
    extern task write(int addr, bit [BANK_DATA_WIDTH-1:0] data);
    extern task read_data(int start_addr, ref data_array_t data_q);
endclass

function ProcDriver::new(vProcIfcDriver vif, semaphore proc_lock);
    this.vif = vif;
    this.proc_lock = proc_lock;
endfunction

task ProcDriver::write_bs(int start_addr, bitstream_t bs_q);
    bit [GLB_ADDR_WIDTH-1:0] cur_addr = start_addr;
    proc_lock.get(1);
    foreach (bs_q[i]) begin
        ProcDriver_write_waddr = cur_addr;
        ProcDriver_write_wdata = bs_q[i];
        write(cur_addr, bs_q[i]);
        cur_addr += 8;
    end

    repeat (10) @(vif.cbd);
    proc_lock.put(1);
endtask

data_array_t data_q;
bit [BANK_DATA_WIDTH-1:0] bdata;
int size;

// TODO: Change it to const ref
task ProcDriver::write_data(int start_addr, data_array_t data_q);
    bit [GLB_ADDR_WIDTH-1:0] cur_addr = start_addr;
    bit [BANK_DATA_WIDTH-1:0] data;
    int size;
    proc_lock.get(1);
    assert (BANK_DATA_WIDTH == 64);
    size = data_q.size();
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
        write(cur_addr, data);
        cur_addr += 8;
    end

    repeat (10) @(vif.cbd);
    proc_lock.put(1);
endtask

task ProcDriver::write(int addr, bit [BANK_DATA_WIDTH-1:0] data);
    vif.cbd.wr_en   <= 1'b1;
    vif.cbd.wr_strb <= {(BANK_DATA_WIDTH / 8) {1'b1}};
    vif.cbd.wr_addr <= addr;
    vif.cbd.wr_data <= data;
    @(vif.cbd);
    vif.cbd.wr_en   <= 0;
    vif.cbd.wr_strb <= 0;
    vif.cbd.wr_addr <= 0;
    vif.cbd.wr_data <= 0;
endtask

int num_words, num_trans;
task ProcDriver::read_data(int start_addr, ref data_array_t data_q);
    int num_words = data_q.size();
    int num_trans = (num_words + 3) / 4;
    proc_lock.get(1);
    fork
        // Process 1 initiates read by setting rd_en HIGH and feeding addresses one per cycle
        // Process 2 unloads the data by waiting for data_valid signal and then reading data one per cycle
        begin
            $display("Set     %0d consecutive addresses BEGIN", num_trans);
            if (`DBG_PROCDRIVER) $display("Start reading at address %08x\n", start_addr);
            @(vif.cbd);
            for (int i = 0; i < num_trans; i++) begin
                vif.cbd.rd_en   <= 1'b1;
                // address increases by 8 every write
                vif.cbd.rd_addr <= (start_addr + 8 * i);
                @(vif.cbd);
            end
            vif.cbd.rd_en   <= 0;
            vif.cbd.rd_addr <= 0;
            $display("Set %d consecutive addresses END", num_trans);  // 4027ns
        end
        begin
            $display("Offload %0d data chunks BEGIN", num_trans);  // 3002ns
            for (int i = 0; i < num_trans; i++) begin
                wait (vif.cbd.rd_data_valid);

                data_q[i*4] = vif.cbd.rd_data & 'hFFFF;
                if (`DBG_PROCDRIVER) $display("[%0t] -- 0 data_q[%04d] <= %0x", $time, i*4, data_q[i*4]);
                if ((i * 4 + 1) < num_words) begin
                    data_q[i*4+1] = (vif.cbd.rd_data & (('hFFFF) << 16)) >> 16;
                    if (`DBG_PROCDRIVER) $display("[%0t] -- 1 data_q[%04d] <= %0x", $time, i*4+1, data_q[i*4+1]);
                end
                if ((i * 4 + 2) < num_words) begin
                    data_q[i*4+2] = (vif.cbd.rd_data & (('hFFFF) << 32)) >> 32;
                    if (`DBG_PROCDRIVER) $display("[%0t] -- 2 data_q[%04d] <= %0x", $time, i*4+2, data_q[i*4+2]);
                end
                if ((i * 4 + 3) < num_words) begin
                    data_q[i*4+3] = (vif.cbd.rd_data & (('hFFFF) << 48)) >> 48;
                    if (`DBG_PROCDRIVER) $display("[%0t] -- 3 data_q[%04d] <= %0x", $time, i*4+3, data_q[i*4+3]);
                end

                @(vif.cbd);
            end
            $display("Offload %d data chunks END", num_trans);  // 4027ns
            $display("First output word is maybe...0x%04x",  data_q[0]);
        end
    join

    repeat (10) @(vif.cbd);
    proc_lock.put(1);
endtask
