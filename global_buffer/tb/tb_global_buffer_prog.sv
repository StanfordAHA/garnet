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
// local parameters
//============================================================================//

//============================================================================//
// main run tests
//============================================================================//
task run_test; begin
    logic [AXI_ADDR_WIDTH-1:0] addr;
    logic [AXI_DATA_WIDTH-1:0] data;

    // configuration test
    // test_configuration();
    test_stream_f2g();

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
        cfg_write(1, i, 2, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_write(1, i, 3, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_write(1, i, 4, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_write(1, i, 5, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_write(1, i, 6, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_write(1, i, 7, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_write(1, i, 8, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_write(1, i, 9, {(GLB_ADDR_WIDTH+1){1'b1}});
    end
    for (int i=0; i<NUM_TILES; i=i+1) begin
        cfg_read(1, i, 0, 2'b11);
        cfg_read(1, i, 1, 2'b11);
        cfg_read(1, i, 2, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_read(1, i, 3, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_read(1, i, 4, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_read(1, i, 5, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_read(1, i, 6, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_read(1, i, 7, {(GLB_ADDR_WIDTH+1){1'b1}});
        cfg_read(1, i, 8, {MAX_NUM_WORDS_WIDTH{1'b1}});
        cfg_read(1, i, 9, {(GLB_ADDR_WIDTH+1){1'b1}});
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
// f2g stream test
//============================================================================//
task test_stream_f2g();
begin
    int tile_id;
    int num_words;
    int start_addr;

    repeat (100) @(posedge clk);

    // enable interrupt
    cfg_write(0, 0, 0, {(2*NUM_TILES){1'b1}});

    // // tile_id 0, num_words 100, start_addr 100
    // tile_id = 0;
    // num_words = 100;
    // start_addr = ((tile_id << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) + 100);
    // stream_config(tile_id, 0, 2'b11);
    // stream_config(tile_id, 1, 2'b01);
    // stream_config(tile_id, 2, num_words);
    // stream_config(tile_id, 3, (start_addr << 1) + 1'b1);
    // run_f2g(tile_id, num_words);
    // // toggle ISR
    // cfg_read_2(0, 0, 1);
    // cfg_write(0, 0, 1, axi_trans.rd_data);

    // // tile_id 0, num_words 99, start_addr 94
    // tile_id = 0;
    // num_words = 99;
    // start_addr = ((tile_id << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) + 94);
    // stream_config(tile_id, 0, 2'b11);
    // stream_config(tile_id, 1, 2'b01);
    // stream_config(tile_id, 2, num_words);
    // stream_config(tile_id, 3, (start_addr << 1) + 1'b1);
    // run_f2g(tile_id, num_words);
    // // toggle ISR
    // cfg_read_2(0, 0, 1);
    // cfg_write(0, 0, 1, axi_trans.rd_data);

    // // tile_id 1, num_words 99, start_addr 94
    // tile_id = 1;
    // num_words = 99;
    // start_addr = ((tile_id << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) + 94);
    // stream_config(tile_id, 0, 2'b11);
    // stream_config(tile_id, 1, 2'b01);
    // stream_config(tile_id, 2, num_words);
    // stream_config(tile_id, 3, (start_addr << 1) + 1'b1);
    // run_f2g(tile_id, num_words);
    // // toggle ISR
    // cfg_read_2(0, 0, 1);
    // cfg_write(0, 0, 1, axi_trans.rd_data);

    // // tile 2-3 connected, num_words 99, start_addr 94
    // // dma2 on, dma3 off
    // tile_id = 2;
    // num_words = 99;
    // start_addr = (((tile_id+1) << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) + 94);
    // stream_config(tile_id, 0, 2'b01);
    // stream_config(tile_id, 1, 2'b01);
    // stream_config(tile_id, 2, num_words);
    // stream_config(tile_id, 3, (start_addr << 1) + 1'b1);
    // stream_config(tile_id+1, 0, 2'b10);
    // run_f2g(tile_id, num_words);
    // // toggle ISR
    // cfg_read_2(0, 0, 1);
    // cfg_write(0, 0, 1, axi_trans.rd_data);

    // // tile 2-3 connected, stream 2-3 both
    // // dma2 off, dma3 on
    // tile_id = 2;
    // stream_config(tile_id, 0, 2'b01);
    // stream_config(tile_id, 1, 2'b00);

    // tile_id = 3;
    // num_words = 200;
    // start_addr = ((tile_id << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) - 84);
    // stream_config(tile_id, 0, 2'b10);
    // stream_config(tile_id, 1, 2'b01);
    // stream_config(tile_id, 2, num_words);
    // stream_config(tile_id, 3, (start_addr << 1) + 1'b1);
    // run_f2g(tile_id, num_words);

    // // toggle ISR
    // cfg_read_2(0, 0, 1);
    // cfg_write(0, 0, 1, axi_trans.rd_data);

    // // tile 4-6 connected, stream 4
    // // dma4 on
    // tile_id = 4;
    // num_words = 200;
    // start_addr = ((tile_id << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) + 84);
    // stream_config(tile_id, 0, 2'b01);
    // stream_config(tile_id, 1, 2'b01);
    // stream_config(tile_id, 2, num_words);
    // stream_config(tile_id, 3, (start_addr << 1) + 1'b1);

    // tile_id = 5;
    // stream_config(tile_id, 0, 2'b00);

    // tile_id = 6;
    // stream_config(tile_id, 0, 2'b10);

    // tile_id = 4;
    // run_f2g(tile_id, num_words);
    // // toggle ISR
    // cfg_read_2(0, 0, 1);
    // cfg_write(0, 0, 1, axi_trans.rd_data);

    // tile 4-6 connected, stream 5-6
    // dma4 on
    tile_id = 4;
    num_words = 200;
    start_addr = (((tile_id+2) << (BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH)) - 84);
    stream_config(tile_id, 0, 2'b01);
    stream_config(tile_id, 1, 2'b01);
    stream_config(tile_id, 2, num_words);
    stream_config(tile_id, 3, (start_addr << 1) + 1'b1);

    tile_id = 5;
    stream_config(tile_id, 0, 2'b00);

    tile_id = 6;
    stream_config(tile_id, 0, 2'b10);

    tile_id = 4;
    run_f2g(tile_id, num_words);
    // toggle ISR
    cfg_read_2(0, 0, 1);
    cfg_write(0, 0, 1, axi_trans.rd_data);

    repeat (100) @(posedge clk); 
end
endtask

task stream_config(bit[$clog2(NUM_TILES)-1:0] tile_id, bit[4:0] reg_id, int data);
begin
    int addr = {1'b1, tile_id, reg_id, 2'b00};
    axi_write(addr, data);
end
endtask

task run_f2g(bit[$clog2(NUM_TILES)-1:0] tile_id, int num_words);
    stream_data_f2g[tile_id] = '0;
    stream_data_valid_f2g[tile_id]  = 0;
    repeat (10) @(posedge clk);
    $srandom(10);
    repeat (num_words) begin
        stream_data_f2g[tile_id] = $urandom();
        stream_data_valid_f2g[tile_id]  = 1;
        @(posedge clk);
    end
    stream_data_f2g[tile_id] = '0;
    stream_data_valid_f2g[tile_id]  = 0;
    repeat (10) @(posedge clk);
begin

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

task cfg_read_2(bit is_tile, bit[$clog2(NUM_TILES)-1:0] tile_id, bit[4:0] reg_id);
begin
    int addr = {is_tile, tile_id, reg_id, 2'b00};
    axi_read(addr);
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
