/*=============================================================================
** Module: tb_global_buffer_prog.sv
** Description:
**              program for global buffer testbench
** Author: Taeyoung Kong
** Change history:  02/03/2020 - Implement first version of global buffer program
**===========================================================================*/
import global_buffer_pkg::*;

program automatic tb_global_buffer_prog (
    input bit                           clk, 
    input bit                           reset, 

    interface                           if_axil,

    output logic [CGRA_DATA_WIDTH-1:0]  stream_data_f2g [NUM_TILES],
    output logic                        stream_data_valid_f2g [NUM_TILES]
);

    axi_driver axi_driver;
    axi_trans_t axi_trans;

//============================================================================//
// main run tests
//============================================================================//
task run_test; begin
    logic [AXI_ADDR_WIDTH-1:0] addr;
    logic [AXI_DATA_WIDTH-1:0] data;

    // configuration test
    test_configuration();

    repeat(500) @(posedge clk);
end
endtask // run_test

//============================================================================//
//  configuration test
//============================================================================//
task test_configuration();
begin
    repeat (100) @(posedge clk);
    test_interrupt_configuration();
    test_tile_configuration();
    repeat (100) @(posedge clk); 
end
endtask

task test_interrupt_configuration();
begin
    repeat (100) @(posedge clk);
    cfg_write(0, 0, 0, {(2*NUM_TILES){1'b1}});
    cfg_write(0, 0, 1, {(2*NUM_TILES){1'b1}});
    cfg_read(0, 0, 0, {(2*NUM_TILES){1'b1}});
    cfg_read(0, 0, 1, {(2*NUM_TILES){1'b1}});
    cfg_write(0, 0, 0, 0);
    cfg_write(0, 0, 1, {(2*NUM_TILES){1'b1}}); // ISR registers are toggled
    cfg_read(0, 0, 0, 0);
    cfg_read(0, 0, 1, 0);
    repeat (100) @(posedge clk); 
end
endtask

task test_tile_configuration();
begin
    repeat (100) @(posedge clk);
    for (int i=0; i<NUM_TILES; i=i+1) begin
        cfg_write(1, i, 0, 2'b11);
        cfg_write(1, i, 1, 2'b11);
        cfg_write(1, i, 2, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_write(1, i, 3, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_write(1, i, 4, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_write(1, i, 5, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_write(1, i, 6, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_write(1, i, 7, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_write(1, i, 8, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_write(1, i, 9, {MAX_NUM_WORDS_WIDTH{1'b1}});
    end
    for (int i=0; i<NUM_TILES; i=i+1) begin
        cfg_read(1, i, 0, 2'b11);
        cfg_read(1, i, 1, 2'b11);
        cfg_read(1, i, 2, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_read(1, i, 3, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_read(1, i, 4, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_read(1, i, 5, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_read(1, i, 6, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_read(1, i, 7, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_read(1, i, 8, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_read(1, i, 9, {MAX_NUM_WORDS_WIDTH{1'b1}});
    end
    for (int i=0; i<NUM_TILES; i=i+1) begin
        cfg_write(1, i, 0, 0);
        cfg_write(1, i, 1, 0);
        cfg_write(1, i, 2, 0);
        cfg_write(1, i, 3, 0);
        cfg_write(1, i, 4, 0);
        cfg_write(1, i, 5, 0);
        cfg_write(1, i, 6, 0);
        cfg_write(1, i, 7, 0);
        cfg_write(1, i, 8, 0);
        cfg_write(1, i, 9, 0);
    end
    for (int i=0; i<NUM_TILES; i=i+1) begin
        cfg_read(1, i, 0, 0);
        cfg_read(1, i, 1, 0);
        cfg_read(1, i, 2, 0);
        cfg_read(1, i, 3, 0);
        cfg_read(1, i, 4, 0);
        cfg_read(1, i, 5, 0);
        cfg_read(1, i, 6, 0);
        cfg_read(1, i, 7, 0);
        cfg_read(1, i, 8, 0);
        cfg_read(1, i, 9, 0);
    end
    repeat (100) @(posedge clk); 
end
endtask

//============================================================================//
// help task functions
//============================================================================//
task cfg_write(bit is_tile, bit[$clog2(NUM_TILES)-1:0] tile_id, bit[4:0] reg_id, int data);
begin
    int addr = {is_tile, tile_id, reg_id, 2'b00};
    axi_write(addr, data);
end
endtask

task cfg_read(bit is_tile, bit[$clog2(NUM_TILES)-1:0] tile_id, bit[4:0] reg_id, int expected);
begin
    int addr = {is_tile, tile_id, reg_id, 2'b00};
    axi_read(addr);
    check_axi(axi_trans.rd_data, expected);
end
endtask

task axi_write_rand();
begin
    repeat (10) @(posedge clk);
    $srandom(10);
    axi_trans.addr = $urandom_range(0, 100);
    axi_trans.wr_data = $urandom(1);
    axi_driver.axi_write(axi_trans.addr, axi_trans.wr_data);
    axi_trans = axi_driver.GetResult();
    repeat (10) @(posedge clk); 
end
endtask

task axi_write(int addr, int data);
begin
    repeat (10) @(posedge clk);
    axi_trans.addr = addr;
    axi_trans.wr_data = data;
    axi_driver.axi_write(axi_trans.addr, axi_trans.wr_data);
    axi_trans = axi_driver.GetResult();
    repeat (10) @(posedge clk); 
end
endtask

task axi_read(int addr);
begin
    repeat (10) @(posedge clk);
    axi_trans.addr = addr;
    axi_driver.axi_read(axi_trans.addr);
    axi_trans = axi_driver.GetResult();
    repeat (10) @(posedge clk); 
end
endtask

task init_test();
begin
    // instantiate axi driver
    axi_driver = new(if_axil);
    axi_driver.Reset();
    
    repeat (2) @(posedge clk); 
end
endtask

task check_axi(int axi_rd_data, int value);
    begin
        assert(axi_rd_data == value)
        else $display("axi_rd_data: %d, val: %d", axi_rd_data, value);
    end
endtask

//============================================================================//
// test begin
//============================================================================//
initial begin
    $display("%t:\t*************************START*****************************",$time);
    
    // wait until reset is low
    @(negedge reset);
    repeat (10) @(posedge clk);

    // initialize test
    $display("%t:\t*************************INIT*****************************",$time);
    init_test;

    // run main test
    $display("%t:\t*************************RUN*****************************",$time);
    run_test;

    repeat (10) @(posedge clk);
    $display("%t:\t*************************FINISH****************************",$time);
    $finish(2);
end
    
endprogram
