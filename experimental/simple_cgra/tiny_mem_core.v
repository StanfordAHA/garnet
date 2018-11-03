module tiny_mem_core
  (
   input [15:0]  in_,
   input [0:0]   wr_en,
   output [15:0] out
   );

   always @(*)
     begin
        out = in;
     end

endmodule
