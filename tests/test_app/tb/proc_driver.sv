`define DBG_PROCDRIVER 0  // Set to '1' for debugging

semaphore proc_lock; 
initial proc_lock = new(1);

semaphore mu_ifc_lock; 
initial mu_ifc_lock = new(1);
import "DPI-C" function int get_MU_input_bubble_mode();


bit [GLB_ADDR_WIDTH-1:0] start_addr;
bit [GLB_ADDR_WIDTH-1:0] cur_addr;
bitstream_t              bs_q;

bit [GLB_ADDR_WIDTH-1:0]  ProcDriver_write_waddr;
bit [BANK_DATA_WIDTH-1:0] ProcDriver_write_wdata;

bit [MU_DATAWIDTH-1:0] mu2cgra_wdata [OC_0-1:0];

// For adding random bubbles to matrix unit input
integer RANDOM_DELAY;
integer ADD_MU_INPUT_BUBBLES;
integer mask;
integer RANDOM_SHIFT;

// For adding random bubbles to matrix unit input
initial begin
    RANDOM_SHIFT = 2;
    ADD_MU_INPUT_BUBBLES = get_MU_input_bubble_mode();
    mask = 32'd3 << RANDOM_SHIFT;
end


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


data_array_t mu_data_q[OC_0];
data_array_t data_q;
bit [BANK_DATA_WIDTH-1:0] bdata;
int size;

// TODO: Change it to const ref
task ProcDriver_write_data();
    cur_addr = start_addr;
    proc_lock.get(1);
    assert (BANK_DATA_WIDTH == 64);
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
        ProcDriver_write_waddr = cur_addr;
        ProcDriver_write_wdata = bdata;
        ProcDriver_write();
        cur_addr += 8;  // Counts hex 8,10,18,20...(8x2^10 == 0x1000
    end
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
endtask


int i;
task MU_driver_write_data();
    cur_addr = start_addr;
    mu_ifc_lock.get(1);
    size = mu_data_q[0].size(); 
    i = 0;
    while (i < size) begin
        for (int oc_0 = 0; oc_0 < OC_0; oc_0++) begin
            mu2cgra_wdata[oc_0] = mu_data_q[oc_0][i];
        end
        MU_driver_write();
        if (mu_ifc.cgra2mu_ready) begin
            i += 1;
        end
    end
    mu_ifc.mu2cgra_valid = 0;
    repeat (10) @(posedge mu_ifc.clk);
    mu_ifc_lock.put(1);
endtask


task MU_driver_write();
    mu_ifc.mu2cgra = mu2cgra_wdata;

    mu_ifc.mu2cgra_valid = 0;
    RANDOM_DELAY = $urandom & mask;
    RANDOM_DELAY = RANDOM_DELAY >> RANDOM_SHIFT;
    while (RANDOM_DELAY > 0 & ADD_MU_INPUT_BUBBLES) begin
        @(posedge mu_ifc.clk);
        RANDOM_DELAY--;
    end

    mu_ifc.mu2cgra_valid = 1;
    @(posedge mu_ifc.clk);
endtask


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

int num_words, num_trans;
task ProcDriver_read_data();
    num_words = data_q.size();        // Should be 4K / 0x1000?
    num_trans = (num_words + 3) / 4;  // Should be 1K

    $display("Num words: %d\n", num_words);
    $display("Num transactions: %d\n", num_trans);
    proc_lock.get(1);
    fork
        // Process 1 initiates read by setting rd_en HIGH and feeding addresses one per cycle
        // Process 2 unloads the data by waiting for data_valid signal and then reading data one per cycle
        begin
            $display("Set     %0d consecutive addresses BEGIN", num_trans);
            if (`DBG_PROCDRIVER) $display("Start reading at address %08x\n", start_addr);
            @(posedge p_ifc.clk);
            for (int i = 0; i < num_trans; i++) begin
                p_ifc.rd_en = 1'b1;
                // address increases by 8 every write
                p_ifc.rd_addr = (start_addr + 8 * i);
                if (`DBG_PROCDRIVER) $display("[%0t] Set addr = %08x", $time, p_ifc.rd_addr);
                @(posedge p_ifc.clk);
            end
            p_ifc.rd_en   = 0;
            p_ifc.rd_addr = 0;
            $display("Set %d consecutive addresses END", num_trans);  // 4027ns
        end
        begin
            $display("Offload %0d data chunks BEGIN", num_trans);  // 3002ns
            for (int i = 0; i < num_trans; i++) begin
                wait (p_ifc.rd_data_valid);

                // VCS data ready same cycle as valid sig arrives
                // Vvverilator data not ready until one cycle AFTER valid signal
                // FIXME this is a bug, somebody needs to figure out why timing is different!!!
                one_cy_delay_if_verilator();

                if (`DBG_PROCDRIVER) $display("\n[%0t] FOO got data word %0x", $time, p_ifc.rd_data);

                data_q[i*4] = p_ifc.rd_data & 'hFFFF;
                if (`DBG_PROCDRIVER) $display("[%0t] -- 0 data_q[%04d] <= %0x", $time, i*4, data_q[i*4]);

                if ((i * 4 + 1) < num_words) begin
                    data_q[i*4+1] = (p_ifc.rd_data & (('hFFFF) << 16)) >> 16;
                    if (`DBG_PROCDRIVER) $display("[%0t] -- 1 data_q[%04d] <= %0x", $time, i*4+1, data_q[i*4+1]);
                end

                if ((i * 4 + 2) < num_words) begin
                    data_q[i*4+2] = (p_ifc.rd_data & (('hFFFF) << 32)) >> 32;
                    if (`DBG_PROCDRIVER) $display("[%0t] -- 2 data_q[%04d] <= %0x", $time, i*4+2, data_q[i*4+2]);
                end

                if ((i * 4 + 3) < num_words) begin
                    data_q[i*4+3] = (p_ifc.rd_data & (('hFFFF) << 48)) >> 48;
                    if (`DBG_PROCDRIVER)
                      $display("[%0t] -- 3 data_q[%04d] <= %0x", $time, i*4+3, data_q[i*4+3]);
                end

                if (`DBG_PROCDRIVER) $display("");

                // FIXME somebody needs to figure out why vcs and verilator are different here!!!
                one_cy_delay_if_vcs();
            end
            $display("Offload %d data chunks END", num_trans);  // 4027ns
            $display("First output word is maybe...0x%04x",  data_q[0]);
        end
    join
    repeat (10) @(posedge p_ifc.clk);
    proc_lock.put(1);
endtask
