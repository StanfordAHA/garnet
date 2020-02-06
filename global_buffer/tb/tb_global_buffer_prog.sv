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
    
    for(int i=0; i < 70; i=i+1) begin
        axi_write(i, 1);
    end

    for(int i=0; i < 50; i=i+1) begin
        axi_write_rand();
    end

    repeat(500) @(posedge clk);
end
endtask // run_test

//============================================================================//
// help task functions
//============================================================================//
task axi_write_rand();
begin
    repeat (10) @(posedge clk);
    $srandom(10);
    axi_trans.addr = $urandom_range(0, 100);
    axi_trans.wr_data = $urandom(1);
    axi_driver.axi_write(axi_trans.addr, axi_trans.wr_data);
    axi_trans = axi_driver.GetResult();
    repeat (100) @(posedge clk); 
end
endtask

task axi_write(int addr, int data);
begin
    repeat (10) @(posedge clk);
    axi_trans.addr = addr;
    axi_trans.wr_data = data;
    axi_driver.axi_write(axi_trans.addr, axi_trans.wr_data);
    axi_trans = axi_driver.GetResult();
    repeat (100) @(posedge clk); 
end
endtask

task axi_read(int addr);
begin
    repeat (10) @(posedge clk);
    axi_trans.addr = addr;
    axi_driver.axi_read(axi_trans.addr);
    axi_trans = axi_driver.GetResult();
    repeat (100) @(posedge clk); 
end
endtask

task init_test();
begin
    // instantiate axi driver
    axi_driver = new(clk, if_axil);
    axi_driver.Reset();
    
    repeat (2) @(posedge clk); 
end
endtask

task check_register(int register, int value);
    begin
        assert(register == value)
        else $display("reg: %d, val: %d", register, value);
    end
endtask

//============================================================================//
// test begin
//============================================================================//
initial begin
    $display("%t:\t*************************START*****************************",$time);
    @(negedge reset);
    repeat (10) @(posedge clk);
    init_test;
    run_test;
    repeat (10) @(posedge clk);
    $display("%t:\t*************************FINISH****************************",$time);
    $finish(2);
end
    
endprogram
