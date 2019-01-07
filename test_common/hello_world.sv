//-----------------------------------------------------
// see: http://www.asic-world.com/verilog/first1.html
//-----------------------------------------------------
module hello_world;

initial begin
    reg x;
    $display ("Hello World");
    assert(1);
    #10  $finish;
end

endmodule // End of Module hello_world
