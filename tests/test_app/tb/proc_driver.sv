class ProcDriver;
    vProcIfcDriver vif;
    semaphore proc_lock;

    extern function new(vProcIfcDriver vif, semaphore proc_lock);
    extern task write_bs(int start_addr, bitstream_t bs_q);
    extern task write_data(int start_addr, data_array_t data_q);
    extern task write(int addr, bit [BANK_DATA_WIDTH-1:0] data);
    extern task read_data(int start_addr, ref data_array_t data_q);
    extern task write_byte(int addr, bit [BANK_DATA_WIDTH-1:0] data, int byte_offset);
    extern task clear_last_rows_and_columns(int start_addr, int C, int X, int Y, int trunc_size);
    extern task reset_cgra();

    logic cgra_reset = 0;
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

    repeat (10) @(vif.cbd);
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

task ProcDriver::read_data(int start_addr, ref data_array_t data_q);
    int num_words = data_q.size();
    int num_trans = (num_words + 3) / 4;
    proc_lock.get(1);
    fork
        begin
            @(vif.cbd);
            for (int i = 0; i < num_trans; i++) begin
                vif.cbd.rd_en   <= 1'b1;
                // address increases by 8 every write
                vif.cbd.rd_addr <= (start_addr + 8 * i);
                @(vif.cbd);
            end
            vif.cbd.rd_en   <= 0;
            vif.cbd.rd_addr <= 0;
        end
        begin
            for (int i = 0; i < num_trans; i++) begin
                wait (vif.cbd.rd_data_valid);

                data_q[i*4] = vif.cbd.rd_data & 'hFFFF;
                if ((i * 4 + 1) < num_words) begin
                    data_q[i*4+1] = (vif.cbd.rd_data & (('hFFFF) << 16)) >> 16;
                end
                if ((i * 4 + 2) < num_words) begin
                    data_q[i*4+2] = (vif.cbd.rd_data & (('hFFFF) << 32)) >> 32;
                end
                if ((i * 4 + 3) < num_words) begin
                    data_q[i*4+3] = (vif.cbd.rd_data & (('hFFFF) << 48)) >> 48;
                end

                @(vif.cbd);
            end
        end
    join

    repeat (10) @(vif.cbd);
    proc_lock.put(1);
endtask

task ProcDriver::write_byte(int addr, bit [BANK_DATA_WIDTH-1:0] data, int byte_offset);
    bit [7:0] wr_strb; // Strobe for byte-level control

    // Calculate the write strobe based on the byte offset
    wr_strb = 8'b0; // Clear all strobe bits
    wr_strb[byte_offset] = 1'b1; // Set strobe for the lower byte of the desired 16-bit word
    wr_strb[byte_offset + 1] = 1'b1; // Set strobe for the upper byte of the desired 16-bit word

    vif.cbd.wr_en   <= 1'b1;
    vif.cbd.wr_strb <= wr_strb;
    vif.cbd.wr_addr <= addr;
    vif.cbd.wr_data <= data;
    @(vif.cbd);
    vif.cbd.wr_en   <= 0;
    vif.cbd.wr_strb <= 0;
    vif.cbd.wr_addr <= 0;
    vif.cbd.wr_data <= 0;
endtask

task ProcDriver::clear_last_rows_and_columns(int start_addr, int C, int X, int Y, int trunc_size);
    bit [GLB_ADDR_WIDTH-1:0] cur_addr;
    bit [BANK_DATA_WIDTH-1:0] zero_data = 0;
    int ch, x, y;
    int byte_offset; // Byte offset for word within 64-bit data width

    proc_lock.get(1);
    assert (BANK_DATA_WIDTH == 64);
    assert (CGRA_BYTE_OFFSET == 1);

    // Loop over each channel
    for (ch = 0; ch < C; ch++) begin

        // Clear the last trunc_size rows for each channel
        for (x = 0; x < X; x++) begin
            for (int tr = Y - trunc_size; tr < Y; tr++) begin
                int word_index = tr * X * C + x * C + ch;
                cur_addr = start_addr + ((word_index / 4) * 4 * 2); // Adjust the block address for 4-word-wide data (64 bits) and multiply by 2 for the byte offset
                byte_offset = (word_index % 4) * 2; // Each word is 16 bits (2 bytes)
                write_byte(cur_addr, zero_data, byte_offset); // Write zero data
            end
        end

        // Clear the last trunc_size columns for each channel
        for (y = 0; y < Y; y++) begin
            for (int tc = X - trunc_size; tc < X; tc++) begin
                int word_index = y * X * C + tc * C + ch;
                cur_addr = start_addr + ((word_index / 4) * 4 * 2);
                byte_offset = (word_index % 4) * 2; // Each word is 16 bits, so multiply by 2 for byte offset
                write_byte(cur_addr, zero_data, byte_offset); // Write zero data
            end
        end
    end

    proc_lock.put(1); // Release lock
endtask

// Task to reset cgra between kernels
task ProcDriver::reset_cgra();
    $display("Resetting CGRA array");
    cgra_reset = 1;
    repeat (10) @(vif.cbd);
    $display("Resetting CGRA array done");
    cgra_reset = 0;
endtask
