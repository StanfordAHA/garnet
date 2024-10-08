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
        write(cur_addr, bs_q[i]);
        cur_addr += 8;
    end

    repeat (10) @(posedge vif.clk);
    proc_lock.put(1);
endtask

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
        write(cur_addr, data);
        cur_addr += 8;
    end

    repeat (10) @(posedge vif.clk);
    proc_lock.put(1);
endtask

task ProcDriver::write(int addr, bit [BANK_DATA_WIDTH-1:0] data);
    vif.wr_en   <= 1'b1;
    vif.wr_strb <= {(BANK_DATA_WIDTH / 8) {1'b1}};
    vif.wr_addr <= addr;
    vif.wr_data <= data;
    @(posedge vif.clk);
    vif.wr_en   <= 0;
    vif.wr_strb <= 0;
    vif.wr_addr <= 0;
    vif.wr_data <= 0;
endtask

task ProcDriver::read_data(int start_addr, ref data_array_t data_q);
    int num_words = data_q.size();
    int num_trans = (num_words + 3) / 4;
    proc_lock.get(1);
    fork
        begin
            @(posedge vif.clk);
            for (int i = 0; i < num_trans; i++) begin
                vif.rd_en   <= 1'b1;
                // address increases by 8 every write
                vif.rd_addr <= (start_addr + 8 * i);
                @(posedge vif.clk);
            end
            vif.rd_en   <= 0;
            vif.rd_addr <= 0;
        end
        begin
            for (int i = 0; i < num_trans; i++) begin
                wait (vif.rd_data_valid);

                data_q[i*4] = vif.rd_data & 'hFFFF;
                if ((i * 4 + 1) < num_words) begin
                    data_q[i*4+1] = (vif.rd_data & (('hFFFF) << 16)) >> 16;
                end
                if ((i * 4 + 2) < num_words) begin
                    data_q[i*4+2] = (vif.rd_data & (('hFFFF) << 32)) >> 32;
                end
                if ((i * 4 + 3) < num_words) begin
                    data_q[i*4+3] = (vif.rd_data & (('hFFFF) << 48)) >> 48;
                end

                @(posedge vif.clk);
            end
        end
    join

    repeat (10) @(posedge vif.clk);
    proc_lock.put(1);
endtask
