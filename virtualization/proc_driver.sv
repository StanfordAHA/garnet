class ProcDriver;
    vProcIfcDriver vif;

    extern function new(vProcIfcDriver vif);
    extern task write_bs(int start_addr, bitstream_t bs_q);
    extern task write_data(int start_addr, data_array_t data_q);
    extern task write(int addr, bit[BANK_DATA_WIDTH-1:0] data);
endclass

function ProcDriver::new(vProcIfcDriver vif);
    this.vif = vif;
endfunction

task ProcDriver::write_bs(int start_addr, bitstream_t bs_q);
    bit [GLB_ADDR_WIDTH-1:0] cur_addr = start_addr;
    foreach(bs_q[i]) begin
        write(cur_addr, bs_q[i]);
        cur_addr += 8;
    end
endtask

task ProcDriver::write_data(int start_addr, data_array_t data_q);
    bit [GLB_ADDR_WIDTH-1:0] cur_addr = start_addr;
    bit [BANK_DATA_WIDTH-1:0] data;
    int size;
    assert (BANK_DATA_WIDTH == 64);
    size = data_q.size();
    for(int i=0; i<size; i+=4) begin
        if ((i+1) == size) begin
            data = data_q[i];
        end
        else if ((i+2) == size) begin
            data = {data_q[i+1], data_q[i]};
        end
        else if ((i+3) == size) begin
            data = {data_q[i+2], data_q[i+1], data_q[i]};
        end
        else begin
            data = {data_q[i+3], data_q[i+2], data_q[i+1], data_q[i]};
        end
        write(cur_addr, data);
        cur_addr += 8;
    end
endtask

task ProcDriver::write(int addr, bit[BANK_DATA_WIDTH-1:0] data);
    vif.cbd.wr_en   <= 1'b1;
    vif.cbd.wr_strb <= {(BANK_DATA_WIDTH/8){1'b1}};
    vif.cbd.wr_addr <= addr;
    vif.cbd.wr_data <= data;
    @(vif.cbd);
    vif.cbd.wr_en   <= 0;
    vif.cbd.wr_strb <= 0;
    vif.cbd.wr_addr <= 0;
    vif.cbd.wr_data <= 0;
endtask

//task ProcDriver::read(input ProcTransaction trans);
//    int j;
//    j = trans.length;
//
//    fork
//        begin
//            @(vif.cbd);
//            for (int i=0; i<j; i++) begin
//                vif.cbd.rd_en   <= trans.rd_en;
//                // address increases by 8 every write
//                vif.cbd.rd_addr <= (trans.rd_addr + (2**BANK_BYTE_OFFSET)*i);
//                @(vif.cbd);
//            end
//            vif.cbd.rd_en   <= 0;
//            vif.cbd.rd_addr <= 0;
//        end
//        begin
//            for (int i=0; i<j; i++) begin
//                wait (vif.cbd.rd_data_valid);
//                trans.rd_data[i] = vif.cbd.rd_data;
//                trans.rd_data_valid[i] = vif.cbd.rd_data_valid;
//                @(vif.cbd);
//            end
//        end
//    join
//endtask
