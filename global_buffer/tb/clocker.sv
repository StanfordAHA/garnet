module clocker (
    output logic clk,
    output logic reset
);

always #5 clk <= ~clk;
initial begin
   clk <= 1'b0;
   reset <= 1'b1;
   repeat(20) @(posedge clk);
   reset <= 1'b0;
end

endmodule
