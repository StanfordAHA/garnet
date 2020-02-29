`timescale 1ns/1ns
module Interconnect_tb;
    reg [0:0] glb2io_1_X00_Y00;
    wire [0:0] io2glb_1_X00_Y00;
    reg [15:0] glb2io_16_X00_Y00;
    wire [15:0] io2glb_16_X00_Y00;
    reg [0:0] glb2io_1_X01_Y00;
    wire [0:0] io2glb_1_X01_Y00;
    reg [15:0] glb2io_16_X01_Y00;
    wire [15:0] io2glb_16_X01_Y00;
    reg [31:0] config_config_addr;
    reg [31:0] config_config_data;
    reg [0:0] config_read;
    reg [0:0] config_write;
    reg clk;
    reg reset;
    reg [0:0] stall;
    wire [31:0] read_config_data;

    Interconnect #(
        
    ) dut (
        .glb2io_1_X00_Y00(glb2io_1_X00_Y00),
        .io2glb_1_X00_Y00(io2glb_1_X00_Y00),
        .glb2io_16_X00_Y00(glb2io_16_X00_Y00),
        .io2glb_16_X00_Y00(io2glb_16_X00_Y00),
        .glb2io_1_X01_Y00(glb2io_1_X01_Y00),
        .io2glb_1_X01_Y00(io2glb_1_X01_Y00),
        .glb2io_16_X01_Y00(glb2io_16_X01_Y00),
        .io2glb_16_X01_Y00(io2glb_16_X01_Y00),
        .config_config_addr(config_config_addr),
        .config_config_data(config_config_data),
        .config_read(config_read),
        .config_write(config_write),
        .clk(clk),
        .reset(reset),
        .stall(stall),
        .read_config_data(read_config_data)
    );

    initial begin
        clk <= 1'd0;
        $write("Starting reset\n");
        reset <= 1'd1;
        #5 clk ^= 1;
        #5 clk ^= 1;
        #1;
        reset <= 1'd0;
        $write("Finished reset\n");
        clk <= 1'd0;
        reset <= 1'd0;
        config_config_addr <= 32'd257;
        config_config_data <= 32'd8388619;
        config_read <= 1'd0;
        config_write <= 1'd1;
        #5 clk ^= 1;
        #5 clk ^= 1;
        config_write <= 1'd0;
        clk <= 1'd0;
        reset <= 1'd0;
        config_config_addr <= 32'd257;
        config_read <= 1'd1;
        config_write <= 1'd0;
        #5 clk ^= 1;
        #5 clk ^= 1;
        #1;
        $write("Doing config (257, 8388619)\n");
        if (!(read_config_data === 32'd8388619)) begin
            $error("Failed on action=23 checking port read_config_data with traceback /aha/garnet/tests/test_timing/test_basic.py:68.  Expected %x, got %x.", 32'd8388619, read_config_data);
        end
        clk <= 1'd0;
        reset <= 1'd0;
        config_config_addr <= 32'd16777473;
        config_config_data <= 32'd1207960064;
        config_read <= 1'd0;
        config_write <= 1'd1;
        #5 clk ^= 1;
        #5 clk ^= 1;
        config_write <= 1'd0;
        clk <= 1'd0;
        reset <= 1'd0;
        config_config_addr <= 32'd16777473;
        config_read <= 1'd1;
        config_write <= 1'd0;
        #5 clk ^= 1;
        #5 clk ^= 1;
        #1;
        $write("Doing config (16777473, 1207960064)\n");
        if (!(read_config_data === 32'd1207960064)) begin
            $error("Failed on action=40 checking port read_config_data with traceback /aha/garnet/tests/test_timing/test_basic.py:68.  Expected %x, got %x.", 32'd1207960064, read_config_data);
        end
        clk <= 1'd0;
        reset <= 1'd0;
        config_config_addr <= 32'd33554689;
        config_config_data <= 32'd2;
        config_read <= 1'd0;
        config_write <= 1'd1;
        #5 clk ^= 1;
        #5 clk ^= 1;
        config_write <= 1'd0;
        clk <= 1'd0;
        reset <= 1'd0;
        config_config_addr <= 32'd33554689;
        config_read <= 1'd1;
        config_write <= 1'd0;
        #5 clk ^= 1;
        #5 clk ^= 1;
        #1;
        $write("Doing config (33554689, 2)\n");
        if (!(read_config_data === 32'd2)) begin
            $error("Failed on action=57 checking port read_config_data with traceback /aha/garnet/tests/test_timing/test_basic.py:68.  Expected %x, got %x.", 32'd2, read_config_data);
        end
        clk <= 1'd0;
        reset <= 1'd0;
        config_read <= 1'd0;
        config_write <= 1'd0;
        #5 clk ^= 1;
        #5 clk ^= 1;
        #20 $finish;
    end

endmodule
