// `define DBG_CW_FP_ADD 1   // Uncomment this line for debugging

module CW_fp_add (a,b,rnd,z,status);
   parameter sig_width             = 23;
   parameter exp_width             = 8;
   parameter ieee_compliance       = 1;
   parameter ieee_NaN_compliance   = 0;

   input  [exp_width+sig_width:0] a,b;
   input  [2:0]                   rnd;

   output [exp_width+sig_width:0] z;
   output [7:0]                   status;
   
   real sra,srb,srz;

   // ADD: I see exp_width 8 and sig_width 7
   initial begin
      if (sig_width != 7) begin
         $display("");
         $fatal(13, {$sformatf(" -- sig_width=%0d, should be 7\n", sig_width)});
      end else if (exp_width != 8) begin
         $display("");
         $fatal(13, {$sformatf(" -- exp_width=%0d, should be 8\n", exp_width)});
      end
   end

   // ADD: I see exp_width 8 and sig_width 7
   // bfloat is? s1  e8  m7 ?   sign=a[15] exp=a[14:7] mant=a[6:0]
   // real is?   s1 e11 m52 ?
   function real bfloat_to_real;
      input [sig_width+exp_width:0] bfloat;

      bit                 sign;
      bit [exp_width-1:0] expo;
      integer             mant;

      bit [10:0]   expo_new;  // 64-bit real has 11-bit exponent

      begin
         sign = bfloat[sig_width+exp_width];             // [ 15 ]
         expo = bfloat[sig_width+exp_width-1:sig_width]; // [14:7]
         mant = bfloat[sig_width-1:0];                   // [ 6:0]
         
         // Handle special cases (zero, denorm, inf, nan)
         if (expo == 0) begin  // zero or denorm 1023-127=?  896??
            if (mant == 0) begin  // zero
               bfloat_to_real = 0.0;
            end else begin // denorm
               bfloat_to_real = $bitstoreal({sign, 11'b0, mant[6:0], 45'b0});
               bfloat_to_real = bfloat_to_real * (2.0 ** -126);  // Mysteries of the organism
            end
         end else if (expo == 255) begin  // inf or nan
            if (mant == 0) begin  // inf
               bfloat_to_real = $bitstoreal({sign, 11'h7ff, 52'b0});
            end else begin  // nan
               bfloat_to_real = $bitstoreal({sign, 11'h7ff, {45'b1, mant[6:0]}});
            end
         end else begin
            expo_new = expo - 127 + 1023;  // Adj bias from 127 (bfloat16) to 1023 (dp)
            bfloat_to_real = $bitstoreal({sign, expo_new[10:0], mant[6:0], 45'b0});
         end
      end
   endfunction // bfloat_to_real

   function [sig_width+exp_width:0] real_to_bfloat;
      input real srz;
      bit [63:0] srzbits;

      bit        sign;
      bit [10:0] expo;
      bit [51:0] mant;

      bit [ 7:0] expo_new;
     
      begin
         srzbits = $realtobits(srz);
         sign = srzbits[63];
         expo = srzbits[62:52];
         mant = srzbits[51:0];
         
         // Handle special cases (zero, denorm, inf, nan)
         if (expo == 0) begin  // zero or denorm
            if (mant == 0) real_to_bfloat = 16'b0;  // Zero
            else           real_to_bfloat = {sign, 8'b0, mant[51:45]}; // denorm

         end else if (expo == 1023) begin  // inf or nan
            if (mant == 0) real_to_bfloat = {sign, 8'hff, 7'b0};  // inf
            else           real_to_bfloat = {sign, 8'hff, mant[51:45]};  // nan

         end else begin
            expo_new  = expo - 1023 + 127;
            real_to_bfloat = {sign, expo_new[7:0], mant[51:45]};
         end
      end
   endfunction // real_to_bfloat

   assign sra = bfloat_to_real(a);
   assign srb = bfloat_to_real(b);
   assign srz = sra + srb;
   assign z = real_to_bfloat(srz);

`ifdef DBG_CW_FP_ADD
   always @* begin
      $display("");
      $display("ADD: I see BITS %04x + %04x = %04x", a, b, z);
      $display("ADD: I see REAL %e + %e = %e", sra, srb, srz);
      $display("ADD: I see z=%04x bfloat_to_real(z)=%e", z, bfloat_to_real(z));
      $display("");
   end
`endif
   assign status = 0;

endmodule // CW_fp_add
