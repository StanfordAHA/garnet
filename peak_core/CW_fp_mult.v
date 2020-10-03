module CW_fp_mult(a, b, rnd, status, z);

parameter sig_width = 23;
parameter exp_width = 8;
parameter ieee_compliance = 1;

input [sig_width+exp_width:0] a,b;
input [2:0] rnd;
output [7:0] status;
output [sig_width+exp_width:0] z;

assign status = 0;
assign z = 0;

endmodule
