/*
CW_fp_mult
  #(.sig_width(frac_bits+3), .exp_width(exp_bits), .ieee_compliance(ieee_compliance)) 
mul1 (
  .a({a,3'h0}),
  .b({b,3'h0}),
  .rnd(rnd),
  .z({int_out,results_x}),
  .status(status));

assign z = {sign, exp, frac[frac_bits-1:0]};
*/
module CW_fp_mult(a,b,rnd,status,z);
   parameter sig_width             = 23;
   parameter exp_width             = 8;
   parameter ieee_compliance       = 1;

   input [sig_width+exp_width:0] a,b;
   input [2:0]                   rnd;
   output [7:0]                  status;
   output [sig_width+exp_width:0] z;

   real sra,srb,srz;

`define SIG_WIDTH 10
`define EXP_WIDTH  8

   // MUL: I see sig_width 10 and exp_width 8
   initial begin
      if (sig_width != `SIG_WIDTH) begin
         $display("");
         $fatal(13, {$sformatf(" -- sig_width=%0d, should be %0d\n", sig_width, `SIG_WIDTH)});
      end else if (exp_width != `EXP_WIDTH) begin
         $display("");
         $fatal(13, {$sformatf(" -- exp_width=%0d, should be %0d\n", exp_width, `EXP_WIDTH)});
      end
   end

   // mfloat is? s1  e8 m10 ? sign=a[18] exp=a[17:10] mant=a[9:0]
   // real is?   s1 e11 m52 ?
   function real mfloat_to_real;
      input [sig_width+exp_width:0] mfloat;

      bit                 sign;
      bit [exp_width-1:0] expo; // [7:0]
      integer             mant;

      bit [10:0]   expo_new;  // 64-bit real has 11-bit exponent

      begin
         sign = mfloat[sig_width+exp_width];             // [18:18]
         expo = mfloat[sig_width+exp_width-1:sig_width]; // [17:10]
         mant = mfloat[sig_width-1:0];                   // [ 9:0 ]
//         sign = mfloat[18];
//         expo = mfloat[17:10];
//         mant = mfloat[9:0];
         
         // Handle special cases (zero, denorm, inf, nan)
         if (expo == 0) begin  // zero or denorm 1023-127=?  896??
            if (mant == 0) begin  // zero
               mfloat_to_real = 0.0;
            end else begin // denorm
               // mfloat_to_real = $bitstoreal({sign, 11'b0, mant[6:0], 45'b0});
               mfloat_to_real = $bitstoreal({sign, 11'b0, mant[9:0], 42'b0});
               mfloat_to_real = mfloat_to_real * (2.0 ** -126);  // Mysteries of the organism
            end
         end else if (expo == 255) begin  // inf or nan
            if (mant == 0) begin  // inf
               mfloat_to_real = $bitstoreal({sign, 11'h7ff, 52'b0});
            end else begin  // nan
               mfloat_to_real = $bitstoreal({sign, 11'h7ff, {42'b1, mant[9:0]}});
            end
         end else begin
            expo_new = expo - 127 + 1023;  // Adj bias from 127 (mfloat16) to 1023 (dp)
            mfloat_to_real = $bitstoreal({sign, expo_new[10:0], mant[9:0], 42'b0});
         end
      end
   endfunction // mfloat_to_real

   function [18:0] real_to_mfloat;
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
            if (mant == 0) real_to_mfloat = 16'b0;  // Zero
            else           real_to_mfloat = {sign, 8'b0, mant[51:45]}; // denorm

         end else if (expo == 1023) begin  // inf or nan
            if (mant == 0) real_to_mfloat = {sign, 8'hff, 7'b0};  // inf
            else           real_to_mfloat = {sign, 8'hff, mant[51:45]};  // nan

         end else begin
            expo_new  = expo - 1023 + 127;
            real_to_mfloat = {sign, expo_new[7:0], mant[51:42]};
         end
      end
   endfunction // real_to_mfloat

   assign sra = mfloat_to_real(a);
   assign srb = mfloat_to_real(b);
   assign srz = sra * srb;
   assign z = real_to_mfloat(srz);

   // TODO ifdef DEBUG
   always @* begin
      $display("");
      /*
      $display("MUL: I see sign(a)=%0d, exp(a)=0x%0x/%0d, mant(a)=%0d",
               a[18],
               a[17:10], a[17:10],
               a[9:0]);
       */
      $display("MUL: I see sig_width %0d and exp_width %0d", sig_width, exp_width);
      $display("MUL: I see BITS %04x * %04x = %04x", a, b, z);
      $display("MUL: I see REAL %e + %e = %e", sra, srb, srz);
      $display("MUL: I see z=%04x mfloat_to_real(z)=%e", z, mfloat_to_real(z));
      $display("");
   end
   assign status = 0;


/*
   always @* begin
      $display("MUL: I see sig_width %d and exp_width %d", sig_width, exp_width);
      $display("MUL: %0f x %0f = %0f", a, b, z);
      // $display("MUL: I see real a=%f b=%f", a, b);
   end
*/
//   assign z = 7;
   assign status = 0;

endmodule // CW_fp_mult

          
