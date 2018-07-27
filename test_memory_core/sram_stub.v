// sram_512w_16b mem_inst(
// .Q(data_out), 
// .CLK(clk),
// .CEN(~cen), 
// .WEN(~wen), 
// .A(addr), 
// .D(data_in), 
// .EMA(3'd0), 
// .EMAW(2'd0), 
// .EMAS(1'b0), 
// .TEN(1'b1),
// .BEN(1'b1),
// .RET1N(1'b1),
// .STOV(1'b0));

module sram_512w_16b (Q, CLK, CEN, WEN, A, D, EMA, EMAW, EMAS, TEN, BEN, RET1N, STOV);
   output reg [15:0] Q;
   input        CLK;
   input        CEN;
   input        WEN;
   input [8:0]  A;
   input [15:0] D;
   
   input [2:0]  EMA;
   input [1:0]  EMAW;
   input        EMAS;
   input        TEN;
   input        BEN;
   input        RET1N;
   input        STOV;
   
   reg [15:0]   data_array [0:511];

   always @(posedge CLK) begin

      // Use all the unused wires (note at least one of them must be nonzero!)
      if (| {EMA, EMAW, EMAS, TEN, BEN, RET1N, STOV}) begin
         if (CEN == 1'b0) begin                  // ACTIVE LOW!!
            Q = data_array[A];
            if (WEN == 1'b0) data_array[A] = D;  // ACTIVE LOW!!
         end
      end
   end
endmodule
