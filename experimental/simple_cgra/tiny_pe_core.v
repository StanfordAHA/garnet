module tiny_pe_core
  (
   input [15:0]  data0,
   input [15:0]  data1,
   input [4:0]   op,
   output [15:0] res
   );

   always @(*)
     begin
        if (op == 0) begin
           res = data0 + data1;           
        end else if (op == 1) begin
           res = data0 - data1;
        end
     end

endmodule
