`define CLK_PERIOD 1000ps

import header::*;
module noc_tb;

logic clk;
logic reset;
logic io1_io2f [NUM_PRR];
logic [15:0] io16_io2f [NUM_PRR];
logic io1_f2io [NUM_PRR];
logic [15:0] io16_f2io [NUM_PRR];

// clk generation
initial begin
    #0.5ns
    clk = 0;
    forever
    #(`CLK_PERIOD/2.0) clk = !clk;
end

// reset generation
initial begin
    reset <= 1;
    repeat(10) @(posedge clk);
    reset <= 0;
end

initial begin
    // wait for reset clear
    wait (reset == 0);
    repeat(10) @(posedge clk);
    $display("Initialization done");

    @(posedge clk);
    io16_io2f[0] = 8;
    @(posedge clk);
    io16_io2f[2] = 16;
    @(posedge clk);
    @(posedge clk);
    @(posedge clk);
    $finish;
end

noc noc(
    .clk        (clk),
    .reset      (reset),
    .io1_io2f   (io1_io2f),
    .io16_io2f  (io16_io2f),
    .io1_f2io   (io1_f2io),
    .io16_f2io  (io16_f2io)
);

endmodule
