module CW_fp_add(a, b, rnd, z, status);

parameter sig_width = 23;
parameter exp_width = 8;
parameter ieee_compliance = 1;
parameter ieee_NaN_compliance = 0;

input [sig_width + exp_width:0] a, b;
input [2:0] rnd;
output [sig_width + exp_width:0] z;
output [7:0] status;

assign status = 0;
assign z = 0;

endmodule
