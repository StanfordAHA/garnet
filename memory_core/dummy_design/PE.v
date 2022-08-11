module PEGEN_mul_hack #(
    parameter exp_bits = 1,
    parameter frac_bits = 1,
    parameter ieee_compliance = 1
) (
    input [exp_bits+frac_bits:0] a,
    input [exp_bits+frac_bits:0] b,
    input [2:0] rnd,
    output [exp_bits+frac_bits:0] z,
    output [7:0] status
);

wire [exp_bits+frac_bits:0] int_out;
wire [2:0] results_x;
reg sign;
reg [exp_bits-1:0] exp;
reg [frac_bits:0] frac;

CW_fp_mult #(.sig_width(frac_bits+3), .exp_width(exp_bits), .ieee_compliance(ieee_compliance)) mul1 (.a({a,3'h0}),.b({b,3'h0}),.rnd(rnd),.z({int_out,results_x}),.status(status));

always @(*) begin
  sign = int_out[exp_bits+frac_bits];
  exp  = int_out[exp_bits+frac_bits-1:frac_bits];
  frac = {1'b0,int_out[frac_bits-1:0]};
  if ((results_x[2]&(results_x[1] | results_x[0])) | (int_out[0] & results_x[2])) begin
    frac = frac + 1'd1;
    if (~&exp) begin
      exp = exp + {{(exp_bits-1){1'b0}},frac[frac_bits]};
    end
  end
end
assign z = {sign, exp, frac[frac_bits-1:0]};

endmodule

module PEGEN_add #(
    parameter exp_bits = 1,
    parameter frac_bits = 1,
    parameter ieee_compliance = 1
) (
    input [exp_bits+frac_bits:0] a,
    input [exp_bits+frac_bits:0] b,
    input [2:0] rnd,
    output [exp_bits+frac_bits:0] z,
    output [7:0] status
);
CW_fp_add #(.sig_width(frac_bits), .exp_width(exp_bits), .ieee_compliance(ieee_compliance)) add_inst (.a(a),.b(b),.rnd(rnd),.z(z),.status(status));
endmodule

module PEGEN_coreir_xor #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = in0 ^ in1;
endmodule

module PEGEN_coreir_ule #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output out
);
  assign out = in0 <= in1;
endmodule

module PEGEN_coreir_ugt #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output out
);
  assign out = in0 > in1;
endmodule

module PEGEN_coreir_uge #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output out
);
  assign out = in0 >= in1;
endmodule

module PEGEN_coreir_sub #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = in0 - in1;
endmodule

module PEGEN_coreir_slt #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output out
);
  assign out = $signed(in0) < $signed(in1);
endmodule

module PEGEN_coreir_sle #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output out
);
  assign out = $signed(in0) <= $signed(in1);
endmodule

module PEGEN_coreir_shl #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = in0 << in1;
endmodule

module PEGEN_coreir_sge #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output out
);
  assign out = $signed(in0) >= $signed(in1);
endmodule

module PEGEN_coreir_reg_arst #(
    parameter width = 1,
    parameter arst_posedge = 1,
    parameter clk_posedge = 1,
    parameter init = 1
) (
    input clk,
    input arst,
    input [width-1:0] in,
    output [width-1:0] out
);
  reg [width-1:0] outReg;
  wire real_rst;
  assign real_rst = arst_posedge ? arst : ~arst;
  wire real_clk;
  assign real_clk = clk_posedge ? clk : ~clk;
  always @(posedge real_clk, posedge real_rst) begin
    if (real_rst) outReg <= init;
    else outReg <= in;
  end
  assign out = outReg;
endmodule

module PEGEN_coreir_or #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = in0 | in1;
endmodule

module PEGEN_coreir_not #(
    parameter width = 1
) (
    input [width-1:0] in,
    output [width-1:0] out
);
  assign out = ~in;
endmodule

module PEGEN_coreir_neg #(
    parameter width = 1
) (
    input [width-1:0] in,
    output [width-1:0] out
);
  assign out = -in;
endmodule

module PEGEN_coreir_mux #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    input sel,
    output [width-1:0] out
);
  assign out = sel ? in1 : in0;
endmodule

module PEGEN_coreir_mul #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = in0 * in1;
endmodule

module PEGEN_coreir_lshr #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = in0 >> in1;
endmodule

module PEGEN_coreir_eq #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output out
);
  assign out = in0 == in1;
endmodule

module PEGEN_coreir_const #(
    parameter width = 1,
    parameter value = 1
) (
    output [width-1:0] out
);
  assign out = value;
endmodule

module PEGEN_float_mul__exp_bits8__frac_bits7 (
    input [15:0] in0,
    input [15:0] in1,
    output [15:0] out
);
wire [2:0] _$_U1_out;
wire [15:0] mi_z;
wire [7:0] mi_status;
PEGEN_coreir_const #(
    .value(3'h1),
    .width(3)
) _$_U1 (
    .out(_$_U1_out)
);
PEGEN_mul_hack #(
    .exp_bits(8),
    .frac_bits(7),
    .ieee_compliance(1'b1)
) mi (
    .a(in0),
    .b(in1),
    .rnd(_$_U1_out),
    .z(mi_z),
    .status(mi_status)
);
assign out = mi_z;
endmodule

module PEGEN_float_add__exp_bits8__frac_bits7 (
    input [15:0] in0,
    input [15:0] in1,
    output [15:0] out
);
wire [2:0] _$_U0_out;
wire [15:0] mi_z;
wire [7:0] mi_status;
PEGEN_coreir_const #(
    .value(3'h0),
    .width(3)
) _$_U0 (
    .out(_$_U0_out)
);
PEGEN_add #(
    .exp_bits(8),
    .frac_bits(7),
    .ieee_compliance(1'b1)
) mi (
    .a(in0),
    .b(in1),
    .rnd(_$_U0_out),
    .z(mi_z),
    .status(mi_status)
);
assign out = mi_z;
endmodule

module PEGEN_coreir_ashr #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = $signed(in0) >>> in1;
endmodule

module PEGEN_coreir_and #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = in0 & in1;
endmodule

module PEGEN_coreir_add #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output [width-1:0] out
);
  assign out = in0 + in1;
endmodule

module PEGEN_corebit_xor (
    input in0,
    input in1,
    output out
);
  assign out = in0 ^ in1;
endmodule

module PEGEN_corebit_or (
    input in0,
    input in1,
    output out
);
  assign out = in0 | in1;
endmodule

module PEGEN_corebit_not (
    input in,
    output out
);
  assign out = ~in;
endmodule

module PEGEN_corebit_const #(
    parameter value = 1
) (
    output out
);
  assign out = value;
endmodule

module PEGEN_corebit_and (
    input in0,
    input in1,
    output out
);
  assign out = in0 & in1;
endmodule

module PEGEN_commonlib_muxn__N2__width9 (
    input [8:0] in_data [1:0],
    input [0:0] in_sel,
    output [8:0] out
);
wire [8:0] _join_out;
PEGEN_coreir_mux #(
    .width(9)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_commonlib_muxn__N2__width8 (
    input [7:0] in_data [1:0],
    input [0:0] in_sel,
    output [7:0] out
);
wire [7:0] _join_out;
PEGEN_coreir_mux #(
    .width(8)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_commonlib_muxn__N2__width5 (
    input [4:0] in_data [1:0],
    input [0:0] in_sel,
    output [4:0] out
);
wire [4:0] _join_out;
PEGEN_coreir_mux #(
    .width(5)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_commonlib_muxn__N2__width32 (
    input [31:0] in_data [1:0],
    input [0:0] in_sel,
    output [31:0] out
);
wire [31:0] _join_out;
PEGEN_coreir_mux #(
    .width(32)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_commonlib_muxn__N2__width3 (
    input [2:0] in_data [1:0],
    input [0:0] in_sel,
    output [2:0] out
);
wire [2:0] _join_out;
PEGEN_coreir_mux #(
    .width(3)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_commonlib_muxn__N2__width23 (
    input [22:0] in_data [1:0],
    input [0:0] in_sel,
    output [22:0] out
);
wire [22:0] _join_out;
PEGEN_coreir_mux #(
    .width(23)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_commonlib_muxn__N2__width2 (
    input [1:0] in_data [1:0],
    input [0:0] in_sel,
    output [1:0] out
);
wire [1:0] _join_out;
PEGEN_coreir_mux #(
    .width(2)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_commonlib_muxn__N2__width16 (
    input [15:0] in_data [1:0],
    input [0:0] in_sel,
    output [15:0] out
);
wire [15:0] _join_out;
PEGEN_coreir_mux #(
    .width(16)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_commonlib_muxn__N2__width1 (
    input [0:0] in_data [1:0],
    input [0:0] in_sel,
    output [0:0] out
);
wire [0:0] _join_out;
PEGEN_coreir_mux #(
    .width(1)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module PEGEN_Op_unq1 (
    input [15:0] in0,
    input [15:0] in1,
    output [15:0] O,
    input CLK,
    input ASYNCRESET
);
wire [15:0] magma_BFloat_16_mul_inst0_out;
PEGEN_float_mul__exp_bits8__frac_bits7 magma_BFloat_16_mul_inst0 (
    .in0(in0),
    .in1(in1),
    .out(magma_BFloat_16_mul_inst0_out)
);
assign O = magma_BFloat_16_mul_inst0_out;
endmodule

module PEGEN_Op (
    input [15:0] in0,
    input [15:0] in1,
    output [15:0] O,
    input CLK,
    input ASYNCRESET
);
wire [15:0] magma_BFloat_16_add_inst0_out;
PEGEN_float_add__exp_bits8__frac_bits7 magma_BFloat_16_add_inst0 (
    .in0(in0),
    .in1(in1),
    .out(magma_BFloat_16_add_inst0_out)
);
assign O = magma_BFloat_16_add_inst0_out;
endmodule

module PEGEN_Mux2xUInt32 (
    input [31:0] I0,
    input [31:0] I1,
    input S,
    output [31:0] O
);
wire [31:0] coreir_commonlib_mux2x32_inst0_out;
wire [31:0] coreir_commonlib_mux2x32_inst0_in_data [1:0];
assign coreir_commonlib_mux2x32_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x32_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width32 coreir_commonlib_mux2x32_inst0 (
    .in_data(coreir_commonlib_mux2x32_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x32_inst0_out)
);
assign O = coreir_commonlib_mux2x32_inst0_out;
endmodule

module PEGEN_Mux2xUInt16 (
    input [15:0] I0,
    input [15:0] I1,
    input S,
    output [15:0] O
);
wire [15:0] coreir_commonlib_mux2x16_inst0_out;
wire [15:0] coreir_commonlib_mux2x16_inst0_in_data [1:0];
assign coreir_commonlib_mux2x16_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x16_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width16 coreir_commonlib_mux2x16_inst0 (
    .in_data(coreir_commonlib_mux2x16_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x16_inst0_out)
);
assign O = coreir_commonlib_mux2x16_inst0_out;
endmodule

module PEGEN_Mux2xSInt9 (
    input [8:0] I0,
    input [8:0] I1,
    input S,
    output [8:0] O
);
wire [8:0] coreir_commonlib_mux2x9_inst0_out;
wire [8:0] coreir_commonlib_mux2x9_inst0_in_data [1:0];
assign coreir_commonlib_mux2x9_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x9_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width9 coreir_commonlib_mux2x9_inst0 (
    .in_data(coreir_commonlib_mux2x9_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x9_inst0_out)
);
assign O = coreir_commonlib_mux2x9_inst0_out;
endmodule

module PEGEN_Mux2xSInt16 (
    input [15:0] I0,
    input [15:0] I1,
    input S,
    output [15:0] O
);
wire [15:0] coreir_commonlib_mux2x16_inst0_out;
wire [15:0] coreir_commonlib_mux2x16_inst0_in_data [1:0];
assign coreir_commonlib_mux2x16_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x16_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width16 coreir_commonlib_mux2x16_inst0 (
    .in_data(coreir_commonlib_mux2x16_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x16_inst0_out)
);
assign O = coreir_commonlib_mux2x16_inst0_out;
endmodule

module PEGEN_Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3 (
    input [1:0] I0,
    input [1:0] I1,
    input S,
    output [1:0] O
);
wire [1:0] coreir_commonlib_mux2x2_inst0_out;
wire [1:0] coreir_commonlib_mux2x2_inst0_in_data [1:0];
assign coreir_commonlib_mux2x2_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x2_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width2 coreir_commonlib_mux2x2_inst0 (
    .in_data(coreir_commonlib_mux2x2_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x2_inst0_out)
);
assign O = coreir_commonlib_mux2x2_inst0_out;
endmodule

module PEGEN_Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3 (
    input [2:0] I0,
    input [2:0] I1,
    input S,
    output [2:0] O
);
wire [2:0] coreir_commonlib_mux2x3_inst0_out;
wire [2:0] coreir_commonlib_mux2x3_inst0_in_data [1:0];
assign coreir_commonlib_mux2x3_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x3_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width3 coreir_commonlib_mux2x3_inst0 (
    .in_data(coreir_commonlib_mux2x3_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x3_inst0_out)
);
assign O = coreir_commonlib_mux2x3_inst0_out;
endmodule

module PEGEN_Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3 (
    input [4:0] I0,
    input [4:0] I1,
    input S,
    output [4:0] O
);
wire [4:0] coreir_commonlib_mux2x5_inst0_out;
wire [4:0] coreir_commonlib_mux2x5_inst0_in_data [1:0];
assign coreir_commonlib_mux2x5_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x5_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width5 coreir_commonlib_mux2x5_inst0 (
    .in_data(coreir_commonlib_mux2x5_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x5_inst0_out)
);
assign O = coreir_commonlib_mux2x5_inst0_out;
endmodule

module PEGEN_Mux2xBits8 (
    input [7:0] I0,
    input [7:0] I1,
    input S,
    output [7:0] O
);
wire [7:0] coreir_commonlib_mux2x8_inst0_out;
wire [7:0] coreir_commonlib_mux2x8_inst0_in_data [1:0];
assign coreir_commonlib_mux2x8_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x8_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width8 coreir_commonlib_mux2x8_inst0 (
    .in_data(coreir_commonlib_mux2x8_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x8_inst0_out)
);
assign O = coreir_commonlib_mux2x8_inst0_out;
endmodule

module PEGEN_Mux2xBits23 (
    input [22:0] I0,
    input [22:0] I1,
    input S,
    output [22:0] O
);
wire [22:0] coreir_commonlib_mux2x23_inst0_out;
wire [22:0] coreir_commonlib_mux2x23_inst0_in_data [1:0];
assign coreir_commonlib_mux2x23_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x23_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width23 coreir_commonlib_mux2x23_inst0 (
    .in_data(coreir_commonlib_mux2x23_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x23_inst0_out)
);
assign O = coreir_commonlib_mux2x23_inst0_out;
endmodule

module PEGEN_Mux2xBits16 (
    input [15:0] I0,
    input [15:0] I1,
    input S,
    output [15:0] O
);
wire [15:0] coreir_commonlib_mux2x16_inst0_out;
wire [15:0] coreir_commonlib_mux2x16_inst0_in_data [1:0];
assign coreir_commonlib_mux2x16_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x16_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width16 coreir_commonlib_mux2x16_inst0 (
    .in_data(coreir_commonlib_mux2x16_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x16_inst0_out)
);
assign O = coreir_commonlib_mux2x16_inst0_out;
endmodule

module PEGEN_Register (
    input [15:0] value,
    output [15:0] O,
    input en,
    input CLK,
    input ASYNCRESET
);
wire [15:0] enable_mux_O;
wire [15:0] reg_PR16_inst0_out;
PEGEN_Mux2xBits16 enable_mux (
    .I0(reg_PR16_inst0_out),
    .I1(value),
    .S(en),
    .O(enable_mux_O)
);
PEGEN_coreir_reg_arst #(
    .arst_posedge(1'b1),
    .clk_posedge(1'b1),
    .init(16'h0000),
    .width(16)
) reg_PR16_inst0 (
    .clk(CLK),
    .arst(ASYNCRESET),
    .in(enable_mux_O),
    .out(reg_PR16_inst0_out)
);
assign O = reg_PR16_inst0_out;
endmodule

module PEGEN_Mux2xBit (
    input I0,
    input I1,
    input S,
    output O
);
wire [0:0] coreir_commonlib_mux2x1_inst0_out;
wire [0:0] coreir_commonlib_mux2x1_inst0_in_data [1:0];
assign coreir_commonlib_mux2x1_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x1_inst0_in_data[0] = I0;
PEGEN_commonlib_muxn__N2__width1 coreir_commonlib_mux2x1_inst0 (
    .in_data(coreir_commonlib_mux2x1_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x1_inst0_out)
);
assign O = coreir_commonlib_mux2x1_inst0_out[0];
endmodule

module PEGEN_Register_unq1 (
    input value,
    output O,
    input en,
    input CLK,
    input ASYNCRESET
);
wire enable_mux_O;
wire [0:0] reg_PR1_inst0_out;
PEGEN_Mux2xBit enable_mux (
    .I0(reg_PR1_inst0_out[0]),
    .I1(value),
    .S(en),
    .O(enable_mux_O)
);
PEGEN_coreir_reg_arst #(
    .arst_posedge(1'b1),
    .clk_posedge(1'b1),
    .init(1'h0),
    .width(1)
) reg_PR1_inst0 (
    .clk(CLK),
    .arst(ASYNCRESET),
    .in(enable_mux_O),
    .out(reg_PR1_inst0_out)
);
assign O = reg_PR1_inst0_out[0];
endmodule

module PEGEN_RegisterMode_unq1 (
    input [1:0] mode,
    input const_,
    input value,
    input clk_en,
    output O0,
    output O1,
    input CLK,
    input ASYNCRESET
);
wire Mux2xBit_inst0_O;
wire Mux2xBit_inst1_O;
wire Mux2xBit_inst2_O;
wire Mux2xBit_inst3_O;
wire Mux2xBit_inst4_O;
wire Mux2xBit_inst5_O;
wire Register_inst0_O;
wire bit_const_0_None_out;
wire [1:0] const_0_2_out;
wire [1:0] const_2_2_out;
wire [1:0] const_3_2_out;
wire magma_Bits_2_eq_inst0_out;
wire magma_Bits_2_eq_inst1_out;
wire magma_Bits_2_eq_inst2_out;
PEGEN_Mux2xBit Mux2xBit_inst0 (
    .I0(value),
    .I1(value),
    .S(magma_Bits_2_eq_inst0_out),
    .O(Mux2xBit_inst0_O)
);
PEGEN_Mux2xBit Mux2xBit_inst1 (
    .I0(bit_const_0_None_out),
    .I1(clk_en),
    .S(magma_Bits_2_eq_inst0_out),
    .O(Mux2xBit_inst1_O)
);
PEGEN_Mux2xBit Mux2xBit_inst2 (
    .I0(Register_inst0_O),
    .I1(value),
    .S(magma_Bits_2_eq_inst2_out),
    .O(Mux2xBit_inst2_O)
);
PEGEN_Mux2xBit Mux2xBit_inst3 (
    .I0(Register_inst0_O),
    .I1(Register_inst0_O),
    .S(magma_Bits_2_eq_inst2_out),
    .O(Mux2xBit_inst3_O)
);
PEGEN_Mux2xBit Mux2xBit_inst4 (
    .I0(Mux2xBit_inst2_O),
    .I1(const_),
    .S(magma_Bits_2_eq_inst1_out),
    .O(Mux2xBit_inst4_O)
);
PEGEN_Mux2xBit Mux2xBit_inst5 (
    .I0(Mux2xBit_inst3_O),
    .I1(Register_inst0_O),
    .S(magma_Bits_2_eq_inst1_out),
    .O(Mux2xBit_inst5_O)
);
PEGEN_Register_unq1 Register_inst0 (
    .value(Mux2xBit_inst0_O),
    .O(Register_inst0_O),
    .en(Mux2xBit_inst1_O),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_corebit_const #(
    .value(1'b0)
) bit_const_0_None (
    .out(bit_const_0_None_out)
);
PEGEN_coreir_const #(
    .value(2'h0),
    .width(2)
) const_0_2 (
    .out(const_0_2_out)
);
PEGEN_coreir_const #(
    .value(2'h2),
    .width(2)
) const_2_2 (
    .out(const_2_2_out)
);
PEGEN_coreir_const #(
    .value(2'h3),
    .width(2)
) const_3_2 (
    .out(const_3_2_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst0 (
    .in0(mode),
    .in1(const_3_2_out),
    .out(magma_Bits_2_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst1 (
    .in0(mode),
    .in1(const_0_2_out),
    .out(magma_Bits_2_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst2 (
    .in0(mode),
    .in1(const_2_2_out),
    .out(magma_Bits_2_eq_inst2_out)
);
assign O0 = Mux2xBit_inst4_O;
assign O1 = Mux2xBit_inst5_O;
endmodule

module PEGEN_RegisterMode (
    input [1:0] mode,
    input [15:0] const_,
    input [15:0] value,
    input clk_en,
    output [15:0] O0,
    output [15:0] O1,
    input CLK,
    input ASYNCRESET
);
wire Mux2xBit_inst0_O;
wire [15:0] Mux2xBits16_inst0_O;
wire [15:0] Mux2xBits16_inst1_O;
wire [15:0] Mux2xBits16_inst2_O;
wire [15:0] Mux2xBits16_inst3_O;
wire [15:0] Mux2xBits16_inst4_O;
wire [15:0] Register_inst0_O;
wire bit_const_0_None_out;
wire [1:0] const_0_2_out;
wire [1:0] const_2_2_out;
wire [1:0] const_3_2_out;
wire magma_Bits_2_eq_inst0_out;
wire magma_Bits_2_eq_inst1_out;
wire magma_Bits_2_eq_inst2_out;
PEGEN_Mux2xBit Mux2xBit_inst0 (
    .I0(bit_const_0_None_out),
    .I1(clk_en),
    .S(magma_Bits_2_eq_inst0_out),
    .O(Mux2xBit_inst0_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst0 (
    .I0(value),
    .I1(value),
    .S(magma_Bits_2_eq_inst0_out),
    .O(Mux2xBits16_inst0_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst1 (
    .I0(Register_inst0_O),
    .I1(value),
    .S(magma_Bits_2_eq_inst2_out),
    .O(Mux2xBits16_inst1_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst2 (
    .I0(Register_inst0_O),
    .I1(Register_inst0_O),
    .S(magma_Bits_2_eq_inst2_out),
    .O(Mux2xBits16_inst2_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst3 (
    .I0(Mux2xBits16_inst1_O),
    .I1(const_),
    .S(magma_Bits_2_eq_inst1_out),
    .O(Mux2xBits16_inst3_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst4 (
    .I0(Mux2xBits16_inst2_O),
    .I1(Register_inst0_O),
    .S(magma_Bits_2_eq_inst1_out),
    .O(Mux2xBits16_inst4_O)
);
PEGEN_Register Register_inst0 (
    .value(Mux2xBits16_inst0_O),
    .O(Register_inst0_O),
    .en(Mux2xBit_inst0_O),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_corebit_const #(
    .value(1'b0)
) bit_const_0_None (
    .out(bit_const_0_None_out)
);
PEGEN_coreir_const #(
    .value(2'h0),
    .width(2)
) const_0_2 (
    .out(const_0_2_out)
);
PEGEN_coreir_const #(
    .value(2'h2),
    .width(2)
) const_2_2 (
    .out(const_2_2_out)
);
PEGEN_coreir_const #(
    .value(2'h3),
    .width(2)
) const_3_2 (
    .out(const_3_2_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst0 (
    .in0(mode),
    .in1(const_3_2_out),
    .out(magma_Bits_2_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst1 (
    .in0(mode),
    .in1(const_0_2_out),
    .out(magma_Bits_2_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst2 (
    .in0(mode),
    .in1(const_2_2_out),
    .out(magma_Bits_2_eq_inst2_out)
);
assign O0 = Mux2xBits16_inst3_O;
assign O1 = Mux2xBits16_inst4_O;
endmodule

module PEGEN_LUT (
    input [7:0] lut,
    input bit0,
    input bit1,
    input bit2,
    output O,
    input CLK,
    input ASYNCRESET
);
wire bit_const_0_None_out;
wire [7:0] const_1_8_out;
wire [7:0] magma_Bits_8_and_inst0_out;
wire [7:0] magma_Bits_8_lshr_inst0_out;
PEGEN_corebit_const #(
    .value(1'b0)
) bit_const_0_None (
    .out(bit_const_0_None_out)
);
PEGEN_coreir_const #(
    .value(8'h01),
    .width(8)
) const_1_8 (
    .out(const_1_8_out)
);
PEGEN_coreir_and #(
    .width(8)
) magma_Bits_8_and_inst0 (
    .in0(magma_Bits_8_lshr_inst0_out),
    .in1(const_1_8_out),
    .out(magma_Bits_8_and_inst0_out)
);
wire [7:0] magma_Bits_8_lshr_inst0_in1;
assign magma_Bits_8_lshr_inst0_in1 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit2,bit1,bit0};
PEGEN_coreir_lshr #(
    .width(8)
) magma_Bits_8_lshr_inst0 (
    .in0(lut),
    .in1(magma_Bits_8_lshr_inst0_in1),
    .out(magma_Bits_8_lshr_inst0_out)
);
assign O = magma_Bits_8_and_inst0_out[0];
endmodule

module PEGEN_FPU (
    input [1:0] fpu_op,
    input [15:0] a,
    input [15:0] b,
    output [15:0] res,
    output N,
    output Z,
    input CLK,
    input ASYNCRESET
);
wire Mux2xBit_inst0_O;
wire Mux2xBit_inst1_O;
wire [15:0] Mux2xBits16_inst0_O;
wire [15:0] Mux2xBits16_inst1_O;
wire [15:0] Op_inst0_O;
wire [15:0] Op_inst1_O;
wire bit_const_1_None_out;
wire [1:0] const_0_2_out;
wire [6:0] const_0_7_out;
wire [7:0] const_0_8_out;
wire [1:0] const_1_2_out;
wire [7:0] const_255_8_out;
wire [1:0] const_2_2_out;
wire [15:0] const_32768_16_out;
wire magma_Bit_and_inst0_out;
wire magma_Bit_and_inst1_out;
wire magma_Bit_and_inst2_out;
wire magma_Bit_and_inst3_out;
wire magma_Bit_and_inst4_out;
wire magma_Bit_not_inst0_out;
wire magma_Bit_or_inst0_out;
wire magma_Bit_or_inst1_out;
wire magma_Bit_or_inst2_out;
wire magma_Bit_xor_inst0_out;
wire [15:0] magma_Bits_16_xor_inst0_out;
wire magma_Bits_2_eq_inst0_out;
wire magma_Bits_2_eq_inst1_out;
wire magma_Bits_2_eq_inst2_out;
wire magma_Bits_2_eq_inst3_out;
wire magma_Bits_2_eq_inst4_out;
wire magma_Bits_2_eq_inst5_out;
wire magma_Bits_7_eq_inst0_out;
wire magma_Bits_7_eq_inst1_out;
wire magma_Bits_7_eq_inst2_out;
wire magma_Bits_8_eq_inst0_out;
wire magma_Bits_8_eq_inst1_out;
wire magma_Bits_8_eq_inst2_out;
PEGEN_Mux2xBit Mux2xBit_inst0 (
    .I0(magma_Bit_and_inst2_out),
    .I1(bit_const_1_None_out),
    .S(magma_Bit_and_inst4_out),
    .O(Mux2xBit_inst0_O)
);
PEGEN_Mux2xBit Mux2xBit_inst1 (
    .I0(magma_Bit_and_inst2_out),
    .I1(Mux2xBit_inst0_O),
    .S(magma_Bits_2_eq_inst5_out),
    .O(Mux2xBit_inst1_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst0 (
    .I0(b),
    .I1(magma_Bits_16_xor_inst0_out),
    .S(magma_Bit_or_inst0_out),
    .O(Mux2xBits16_inst0_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst1 (
    .I0(Op_inst1_O),
    .I1(Op_inst0_O),
    .S(magma_Bit_or_inst2_out),
    .O(Mux2xBits16_inst1_O)
);
PEGEN_Op Op_inst0 (
    .in0(a),
    .in1(Mux2xBits16_inst0_O),
    .O(Op_inst0_O),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_Op_unq1 Op_inst1 (
    .in0(a),
    .in1(Mux2xBits16_inst0_O),
    .O(Op_inst1_O),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_corebit_const #(
    .value(1'b1)
) bit_const_1_None (
    .out(bit_const_1_None_out)
);
PEGEN_coreir_const #(
    .value(2'h0),
    .width(2)
) const_0_2 (
    .out(const_0_2_out)
);
PEGEN_coreir_const #(
    .value(7'h00),
    .width(7)
) const_0_7 (
    .out(const_0_7_out)
);
PEGEN_coreir_const #(
    .value(8'h00),
    .width(8)
) const_0_8 (
    .out(const_0_8_out)
);
PEGEN_coreir_const #(
    .value(2'h1),
    .width(2)
) const_1_2 (
    .out(const_1_2_out)
);
PEGEN_coreir_const #(
    .value(8'hff),
    .width(8)
) const_255_8 (
    .out(const_255_8_out)
);
PEGEN_coreir_const #(
    .value(2'h2),
    .width(2)
) const_2_2 (
    .out(const_2_2_out)
);
PEGEN_coreir_const #(
    .value(16'h8000),
    .width(16)
) const_32768_16 (
    .out(const_32768_16_out)
);
PEGEN_corebit_and magma_Bit_and_inst0 (
    .in0(magma_Bits_8_eq_inst0_out),
    .in1(magma_Bits_7_eq_inst0_out),
    .out(magma_Bit_and_inst0_out)
);
PEGEN_corebit_and magma_Bit_and_inst1 (
    .in0(magma_Bits_8_eq_inst1_out),
    .in1(magma_Bits_7_eq_inst1_out),
    .out(magma_Bit_and_inst1_out)
);
PEGEN_corebit_and magma_Bit_and_inst2 (
    .in0(magma_Bits_8_eq_inst2_out),
    .in1(magma_Bits_7_eq_inst2_out),
    .out(magma_Bit_and_inst2_out)
);
PEGEN_corebit_and magma_Bit_and_inst3 (
    .in0(magma_Bit_and_inst0_out),
    .in1(magma_Bit_and_inst1_out),
    .out(magma_Bit_and_inst3_out)
);
PEGEN_corebit_and magma_Bit_and_inst4 (
    .in0(magma_Bit_and_inst3_out),
    .in1(magma_Bit_not_inst0_out),
    .out(magma_Bit_and_inst4_out)
);
PEGEN_corebit_not magma_Bit_not_inst0 (
    .in(magma_Bit_xor_inst0_out),
    .out(magma_Bit_not_inst0_out)
);
PEGEN_corebit_or magma_Bit_or_inst0 (
    .in0(magma_Bits_2_eq_inst0_out),
    .in1(magma_Bits_2_eq_inst1_out),
    .out(magma_Bit_or_inst0_out)
);
PEGEN_corebit_or magma_Bit_or_inst1 (
    .in0(magma_Bits_2_eq_inst2_out),
    .in1(magma_Bits_2_eq_inst3_out),
    .out(magma_Bit_or_inst1_out)
);
PEGEN_corebit_or magma_Bit_or_inst2 (
    .in0(magma_Bit_or_inst1_out),
    .in1(magma_Bits_2_eq_inst4_out),
    .out(magma_Bit_or_inst2_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst0 (
    .in0(a[15]),
    .in1(b[15]),
    .out(magma_Bit_xor_inst0_out)
);
PEGEN_coreir_xor #(
    .width(16)
) magma_Bits_16_xor_inst0 (
    .in0(b),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_xor_inst0_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst0 (
    .in0(fpu_op),
    .in1(const_1_2_out),
    .out(magma_Bits_2_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst1 (
    .in0(fpu_op),
    .in1(const_2_2_out),
    .out(magma_Bits_2_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst2 (
    .in0(fpu_op),
    .in1(const_0_2_out),
    .out(magma_Bits_2_eq_inst2_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst3 (
    .in0(fpu_op),
    .in1(const_1_2_out),
    .out(magma_Bits_2_eq_inst3_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst4 (
    .in0(fpu_op),
    .in1(const_2_2_out),
    .out(magma_Bits_2_eq_inst4_out)
);
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst5 (
    .in0(fpu_op),
    .in1(const_2_2_out),
    .out(magma_Bits_2_eq_inst5_out)
);
PEGEN_coreir_eq #(
    .width(7)
) magma_Bits_7_eq_inst0 (
    .in0(a[6:0]),
    .in1(const_0_7_out),
    .out(magma_Bits_7_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(7)
) magma_Bits_7_eq_inst1 (
    .in0(b[6:0]),
    .in1(const_0_7_out),
    .out(magma_Bits_7_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(7)
) magma_Bits_7_eq_inst2 (
    .in0(Mux2xBits16_inst1_O[6:0]),
    .in1(const_0_7_out),
    .out(magma_Bits_7_eq_inst2_out)
);
PEGEN_coreir_eq #(
    .width(8)
) magma_Bits_8_eq_inst0 (
    .in0(a[14:7]),
    .in1(const_255_8_out),
    .out(magma_Bits_8_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(8)
) magma_Bits_8_eq_inst1 (
    .in0(b[14:7]),
    .in1(const_255_8_out),
    .out(magma_Bits_8_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(8)
) magma_Bits_8_eq_inst2 (
    .in0(Mux2xBits16_inst1_O[14:7]),
    .in1(const_0_8_out),
    .out(magma_Bits_8_eq_inst2_out)
);
assign res = Mux2xBits16_inst1_O;
assign N = Mux2xBits16_inst1_O[15];
assign Z = Mux2xBit_inst1_O;
endmodule

module PEGEN_FPCustom (
    input [2:0] op,
    input [0:0] signed_,
    input [15:0] a,
    input [15:0] b,
    output [15:0] res,
    output res_p,
    output V,
    input CLK,
    input ASYNCRESET
);
wire Mux2xBit_inst0_O;
wire Mux2xBit_inst1_O;
wire Mux2xBit_inst10_O;
wire Mux2xBit_inst2_O;
wire Mux2xBit_inst3_O;
wire Mux2xBit_inst4_O;
wire Mux2xBit_inst5_O;
wire Mux2xBit_inst6_O;
wire Mux2xBit_inst7_O;
wire Mux2xBit_inst8_O;
wire Mux2xBit_inst9_O;
wire [15:0] Mux2xBits16_inst0_O;
wire [15:0] Mux2xBits16_inst1_O;
wire [15:0] Mux2xBits16_inst10_O;
wire [15:0] Mux2xBits16_inst11_O;
wire [15:0] Mux2xBits16_inst12_O;
wire [15:0] Mux2xBits16_inst13_O;
wire [15:0] Mux2xBits16_inst14_O;
wire [15:0] Mux2xBits16_inst15_O;
wire [15:0] Mux2xBits16_inst16_O;
wire [15:0] Mux2xBits16_inst17_O;
wire [15:0] Mux2xBits16_inst18_O;
wire [15:0] Mux2xBits16_inst19_O;
wire [15:0] Mux2xBits16_inst2_O;
wire [15:0] Mux2xBits16_inst20_O;
wire [15:0] Mux2xBits16_inst3_O;
wire [15:0] Mux2xBits16_inst4_O;
wire [15:0] Mux2xBits16_inst5_O;
wire [15:0] Mux2xBits16_inst6_O;
wire [15:0] Mux2xBits16_inst7_O;
wire [15:0] Mux2xBits16_inst8_O;
wire [15:0] Mux2xBits16_inst9_O;
wire [22:0] Mux2xBits23_inst0_O;
wire [7:0] Mux2xBits8_inst0_O;
wire [7:0] Mux2xBits8_inst1_O;
wire [7:0] Mux2xBits8_inst2_O;
wire [7:0] Mux2xBits8_inst3_O;
wire [7:0] Mux2xBits8_inst4_O;
wire [7:0] Mux2xBits8_inst5_O;
wire [15:0] Mux2xSInt16_inst0_O;
wire [15:0] Mux2xSInt16_inst1_O;
wire [15:0] Mux2xSInt16_inst10_O;
wire [15:0] Mux2xSInt16_inst11_O;
wire [15:0] Mux2xSInt16_inst12_O;
wire [15:0] Mux2xSInt16_inst13_O;
wire [15:0] Mux2xSInt16_inst14_O;
wire [15:0] Mux2xSInt16_inst15_O;
wire [15:0] Mux2xSInt16_inst16_O;
wire [15:0] Mux2xSInt16_inst17_O;
wire [15:0] Mux2xSInt16_inst18_O;
wire [15:0] Mux2xSInt16_inst19_O;
wire [15:0] Mux2xSInt16_inst2_O;
wire [15:0] Mux2xSInt16_inst20_O;
wire [15:0] Mux2xSInt16_inst21_O;
wire [15:0] Mux2xSInt16_inst22_O;
wire [15:0] Mux2xSInt16_inst23_O;
wire [15:0] Mux2xSInt16_inst24_O;
wire [15:0] Mux2xSInt16_inst25_O;
wire [15:0] Mux2xSInt16_inst26_O;
wire [15:0] Mux2xSInt16_inst27_O;
wire [15:0] Mux2xSInt16_inst28_O;
wire [15:0] Mux2xSInt16_inst29_O;
wire [15:0] Mux2xSInt16_inst3_O;
wire [15:0] Mux2xSInt16_inst30_O;
wire [15:0] Mux2xSInt16_inst4_O;
wire [15:0] Mux2xSInt16_inst5_O;
wire [15:0] Mux2xSInt16_inst6_O;
wire [15:0] Mux2xSInt16_inst7_O;
wire [15:0] Mux2xSInt16_inst8_O;
wire [15:0] Mux2xSInt16_inst9_O;
wire [8:0] Mux2xSInt9_inst0_O;
wire [8:0] Mux2xSInt9_inst1_O;
wire [8:0] Mux2xSInt9_inst10_O;
wire [8:0] Mux2xSInt9_inst11_O;
wire [8:0] Mux2xSInt9_inst12_O;
wire [8:0] Mux2xSInt9_inst2_O;
wire [8:0] Mux2xSInt9_inst3_O;
wire [8:0] Mux2xSInt9_inst4_O;
wire [8:0] Mux2xSInt9_inst5_O;
wire [8:0] Mux2xSInt9_inst6_O;
wire [8:0] Mux2xSInt9_inst7_O;
wire [8:0] Mux2xSInt9_inst8_O;
wire [8:0] Mux2xSInt9_inst9_O;
wire bit_const_0_None_out;
wire bit_const_1_None_out;
wire [15:0] const_0_16_out;
wire [22:0] const_0_23_out;
wire [2:0] const_0_3_out;
wire [8:0] const_0_9_out;
wire [15:0] const_10_16_out;
wire [15:0] const_11_16_out;
wire [15:0] const_127_16_out;
wire [7:0] const_127_8_out;
wire [8:0] const_127_9_out;
wire [15:0] const_128_16_out;
wire [15:0] const_12_16_out;
wire [15:0] const_13_16_out;
wire [7:0] const_142_8_out;
wire [15:0] const_14_16_out;
wire [15:0] const_15_16_out;
wire [0:0] const_1_1_out;
wire [15:0] const_1_16_out;
wire [2:0] const_1_3_out;
wire [8:0] const_255_9_out;
wire [15:0] const_2_16_out;
wire [2:0] const_2_3_out;
wire [15:0] const_32512_16_out;
wire [15:0] const_32640_16_out;
wire [15:0] const_32768_16_out;
wire [15:0] const_3_16_out;
wire [2:0] const_3_3_out;
wire [15:0] const_4_16_out;
wire [2:0] const_4_3_out;
wire [15:0] const_5_16_out;
wire [2:0] const_5_3_out;
wire [15:0] const_65409_16_out;
wire [15:0] const_6_16_out;
wire [2:0] const_6_3_out;
wire [15:0] const_7_16_out;
wire [22:0] const_7_23_out;
wire [15:0] const_8_16_out;
wire [15:0] const_9_16_out;
wire magma_Bit_not_inst0_out;
wire magma_Bit_not_inst1_out;
wire magma_Bit_not_inst10_out;
wire magma_Bit_not_inst11_out;
wire magma_Bit_not_inst12_out;
wire magma_Bit_not_inst13_out;
wire magma_Bit_not_inst14_out;
wire magma_Bit_not_inst15_out;
wire magma_Bit_not_inst16_out;
wire magma_Bit_not_inst17_out;
wire magma_Bit_not_inst18_out;
wire magma_Bit_not_inst19_out;
wire magma_Bit_not_inst2_out;
wire magma_Bit_not_inst20_out;
wire magma_Bit_not_inst21_out;
wire magma_Bit_not_inst22_out;
wire magma_Bit_not_inst23_out;
wire magma_Bit_not_inst24_out;
wire magma_Bit_not_inst3_out;
wire magma_Bit_not_inst4_out;
wire magma_Bit_not_inst5_out;
wire magma_Bit_not_inst6_out;
wire magma_Bit_not_inst7_out;
wire magma_Bit_not_inst8_out;
wire magma_Bit_not_inst9_out;
wire magma_Bit_xor_inst0_out;
wire magma_Bit_xor_inst1_out;
wire magma_Bit_xor_inst10_out;
wire magma_Bit_xor_inst11_out;
wire magma_Bit_xor_inst12_out;
wire magma_Bit_xor_inst13_out;
wire magma_Bit_xor_inst14_out;
wire magma_Bit_xor_inst15_out;
wire magma_Bit_xor_inst16_out;
wire magma_Bit_xor_inst17_out;
wire magma_Bit_xor_inst18_out;
wire magma_Bit_xor_inst19_out;
wire magma_Bit_xor_inst2_out;
wire magma_Bit_xor_inst20_out;
wire magma_Bit_xor_inst21_out;
wire magma_Bit_xor_inst22_out;
wire magma_Bit_xor_inst23_out;
wire magma_Bit_xor_inst24_out;
wire magma_Bit_xor_inst3_out;
wire magma_Bit_xor_inst4_out;
wire magma_Bit_xor_inst5_out;
wire magma_Bit_xor_inst6_out;
wire magma_Bit_xor_inst7_out;
wire magma_Bit_xor_inst8_out;
wire magma_Bit_xor_inst9_out;
wire [15:0] magma_Bits_16_and_inst0_out;
wire [15:0] magma_Bits_16_and_inst1_out;
wire [15:0] magma_Bits_16_and_inst10_out;
wire [15:0] magma_Bits_16_and_inst11_out;
wire [15:0] magma_Bits_16_and_inst12_out;
wire [15:0] magma_Bits_16_and_inst2_out;
wire [15:0] magma_Bits_16_and_inst3_out;
wire [15:0] magma_Bits_16_and_inst4_out;
wire [15:0] magma_Bits_16_and_inst5_out;
wire [15:0] magma_Bits_16_and_inst6_out;
wire [15:0] magma_Bits_16_and_inst7_out;
wire [15:0] magma_Bits_16_and_inst8_out;
wire [15:0] magma_Bits_16_and_inst9_out;
wire magma_Bits_16_eq_inst0_out;
wire magma_Bits_16_eq_inst1_out;
wire [15:0] magma_Bits_16_lshr_inst0_out;
wire [15:0] magma_Bits_16_lshr_inst1_out;
wire [15:0] magma_Bits_16_or_inst0_out;
wire [15:0] magma_Bits_16_or_inst1_out;
wire [15:0] magma_Bits_16_or_inst2_out;
wire [15:0] magma_Bits_16_or_inst3_out;
wire [15:0] magma_Bits_16_or_inst4_out;
wire [15:0] magma_Bits_16_or_inst5_out;
wire [15:0] magma_Bits_16_or_inst6_out;
wire [15:0] magma_Bits_16_or_inst7_out;
wire [15:0] magma_Bits_16_or_inst8_out;
wire [15:0] magma_Bits_16_shl_inst0_out;
wire [15:0] magma_Bits_16_shl_inst1_out;
wire [15:0] magma_Bits_16_shl_inst2_out;
wire [15:0] magma_Bits_16_shl_inst3_out;
wire magma_Bits_1_eq_inst0_out;
wire [22:0] magma_Bits_23_lshr_inst0_out;
wire [22:0] magma_Bits_23_shl_inst0_out;
wire magma_Bits_3_eq_inst0_out;
wire magma_Bits_3_eq_inst1_out;
wire magma_Bits_3_eq_inst2_out;
wire magma_Bits_3_eq_inst3_out;
wire magma_Bits_3_eq_inst4_out;
wire magma_Bits_3_eq_inst5_out;
wire magma_Bits_3_eq_inst6_out;
wire magma_Bits_3_eq_inst7_out;
wire [15:0] magma_SInt_16_add_inst0_out;
wire [15:0] magma_SInt_16_and_inst0_out;
wire [15:0] magma_SInt_16_neg_inst0_out;
wire [15:0] magma_SInt_16_neg_inst1_out;
wire [15:0] magma_SInt_16_neg_inst2_out;
wire magma_SInt_16_sge_inst0_out;
wire [15:0] magma_SInt_16_shl_inst0_out;
wire [15:0] magma_SInt_16_sub_inst0_out;
wire [15:0] magma_SInt_16_sub_inst1_out;
wire [8:0] magma_SInt_9_neg_inst0_out;
wire [8:0] magma_SInt_9_neg_inst1_out;
wire magma_SInt_9_slt_inst0_out;
wire magma_SInt_9_slt_inst1_out;
wire magma_SInt_9_slt_inst2_out;
wire [8:0] magma_SInt_9_sub_inst0_out;
wire [8:0] magma_SInt_9_sub_inst1_out;
wire [8:0] magma_SInt_9_sub_inst2_out;
wire [7:0] magma_UInt_8_add_inst0_out;
wire [7:0] magma_UInt_8_add_inst1_out;
wire [7:0] magma_UInt_8_sub_inst0_out;
wire magma_UInt_8_ugt_inst0_out;
wire [8:0] magma_UInt_9_add_inst0_out;
wire magma_UInt_9_ugt_inst0_out;
PEGEN_Mux2xBit Mux2xBit_inst0 (
    .I0(bit_const_0_None_out),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst7_out),
    .O(Mux2xBit_inst0_O)
);
PEGEN_Mux2xBit Mux2xBit_inst1 (
    .I0(bit_const_0_None_out),
    .I1(magma_UInt_8_ugt_inst0_out),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xBit_inst1_O)
);
PEGEN_Mux2xBit Mux2xBit_inst10 (
    .I0(Mux2xBit_inst8_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst2_out),
    .O(Mux2xBit_inst10_O)
);
PEGEN_Mux2xBit Mux2xBit_inst2 (
    .I0(Mux2xBit_inst0_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xBit_inst2_O)
);
PEGEN_Mux2xBit Mux2xBit_inst3 (
    .I0(Mux2xBit_inst1_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst5_out),
    .O(Mux2xBit_inst3_O)
);
PEGEN_Mux2xBit Mux2xBit_inst4 (
    .I0(Mux2xBit_inst2_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst5_out),
    .O(Mux2xBit_inst4_O)
);
PEGEN_Mux2xBit Mux2xBit_inst5 (
    .I0(Mux2xBit_inst3_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst4_out),
    .O(Mux2xBit_inst5_O)
);
PEGEN_Mux2xBit Mux2xBit_inst6 (
    .I0(Mux2xBit_inst4_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst4_out),
    .O(Mux2xBit_inst6_O)
);
PEGEN_Mux2xBit Mux2xBit_inst7 (
    .I0(Mux2xBit_inst5_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst3_out),
    .O(Mux2xBit_inst7_O)
);
PEGEN_Mux2xBit Mux2xBit_inst8 (
    .I0(Mux2xBit_inst6_O),
    .I1(magma_UInt_9_ugt_inst0_out),
    .S(magma_Bits_3_eq_inst3_out),
    .O(Mux2xBit_inst8_O)
);
PEGEN_Mux2xBit Mux2xBit_inst9 (
    .I0(Mux2xBit_inst7_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_3_eq_inst2_out),
    .O(Mux2xBit_inst9_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst0 (
    .I0(const_0_16_out),
    .I1(const_32768_16_out),
    .S(magma_SInt_9_slt_inst0_out),
    .O(Mux2xBits16_inst0_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst1 (
    .I0(const_0_16_out),
    .I1(magma_Bits_16_and_inst0_out),
    .S(magma_Bits_1_eq_inst0_out),
    .O(Mux2xBits16_inst1_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst10 (
    .I0(magma_Bits_16_and_inst10_out),
    .I1(magma_Bits_16_and_inst8_out),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xBits16_inst10_O)
);
wire [15:0] Mux2xBits16_inst11_I1;
assign Mux2xBits16_inst11_I1 = {magma_Bits_23_lshr_inst0_out[15],magma_Bits_23_lshr_inst0_out[14],magma_Bits_23_lshr_inst0_out[13],magma_Bits_23_lshr_inst0_out[12],magma_Bits_23_lshr_inst0_out[11],magma_Bits_23_lshr_inst0_out[10],magma_Bits_23_lshr_inst0_out[9],magma_Bits_23_lshr_inst0_out[8],magma_Bits_23_lshr_inst0_out[7],magma_Bits_23_lshr_inst0_out[6],magma_Bits_23_lshr_inst0_out[5],magma_Bits_23_lshr_inst0_out[4],magma_Bits_23_lshr_inst0_out[3],magma_Bits_23_lshr_inst0_out[2],magma_Bits_23_lshr_inst0_out[1],magma_Bits_23_lshr_inst0_out[0]};
PEGEN_Mux2xBits16 Mux2xBits16_inst11 (
    .I0(magma_Bits_16_and_inst12_out),
    .I1(Mux2xBits16_inst11_I1),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xBits16_inst11_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst12 (
    .I0(Mux2xBits16_inst9_O),
    .I1(magma_Bits_16_or_inst1_out),
    .S(magma_Bits_3_eq_inst5_out),
    .O(Mux2xBits16_inst12_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst13 (
    .I0(Mux2xBits16_inst8_O),
    .I1(magma_Bits_16_and_inst7_out),
    .S(magma_Bits_3_eq_inst4_out),
    .O(Mux2xBits16_inst13_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst14 (
    .I0(Mux2xBits16_inst12_O),
    .I1(magma_Bits_16_or_inst6_out),
    .S(magma_Bits_3_eq_inst4_out),
    .O(Mux2xBits16_inst14_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst15 (
    .I0(Mux2xBits16_inst10_O),
    .I1(magma_Bits_16_and_inst5_out),
    .S(magma_Bits_3_eq_inst4_out),
    .O(Mux2xBits16_inst15_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst16 (
    .I0(magma_Bits_16_shl_inst2_out),
    .I1(magma_Bits_16_shl_inst1_out),
    .S(magma_Bits_3_eq_inst3_out),
    .O(Mux2xBits16_inst16_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst17 (
    .I0(Mux2xBits16_inst14_O),
    .I1(magma_Bits_16_or_inst3_out),
    .S(magma_Bits_3_eq_inst3_out),
    .O(Mux2xBits16_inst17_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst18 (
    .I0(Mux2xBits16_inst3_O),
    .I1(magma_Bits_16_and_inst3_out),
    .S(magma_Bits_3_eq_inst3_out),
    .O(Mux2xBits16_inst18_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst19 (
    .I0(Mux2xBits16_inst17_O),
    .I1(magma_Bits_16_and_inst2_out),
    .S(magma_Bits_3_eq_inst2_out),
    .O(Mux2xBits16_inst19_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst2 (
    .I0(a),
    .I1(magma_SInt_16_neg_inst0_out),
    .S(magma_Bit_not_inst8_out),
    .O(Mux2xBits16_inst2_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst20 (
    .I0(Mux2xBits16_inst18_O),
    .I1(Mux2xBits16_inst3_O),
    .S(magma_Bits_3_eq_inst2_out),
    .O(Mux2xBits16_inst20_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst3 (
    .I0(Mux2xBits16_inst1_O),
    .I1(Mux2xBits16_inst0_O),
    .S(magma_Bits_3_eq_inst0_out),
    .O(Mux2xBits16_inst3_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst4 (
    .I0(const_0_16_out),
    .I1(magma_SInt_16_and_inst0_out),
    .S(magma_SInt_16_sge_inst0_out),
    .O(Mux2xBits16_inst4_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst5 (
    .I0(Mux2xBits16_inst4_O),
    .I1(magma_Bits_16_lshr_inst0_out),
    .S(magma_Bits_3_eq_inst1_out),
    .O(Mux2xBits16_inst5_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst6 (
    .I0(magma_Bits_16_shl_inst3_out),
    .I1(magma_Bits_16_lshr_inst1_out),
    .S(magma_SInt_9_slt_inst2_out),
    .O(Mux2xBits16_inst6_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst7 (
    .I0(magma_Bits_16_or_inst1_out),
    .I1(Mux2xSInt16_inst29_O),
    .S(magma_Bits_3_eq_inst7_out),
    .O(Mux2xBits16_inst7_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst8 (
    .I0(magma_Bits_16_or_inst8_out),
    .I1(magma_Bits_16_or_inst7_out),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xBits16_inst8_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst9 (
    .I0(Mux2xBits16_inst7_O),
    .I1(Mux2xSInt16_inst28_O),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xBits16_inst9_O)
);
PEGEN_Mux2xBits23 Mux2xBits23_inst0 (
    .I0(magma_Bits_23_shl_inst0_out),
    .I1(const_0_23_out),
    .S(magma_SInt_9_slt_inst1_out),
    .O(Mux2xBits23_inst0_O)
);
wire [7:0] Mux2xBits8_inst0_I0;
assign Mux2xBits8_inst0_I0 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
wire [7:0] Mux2xBits8_inst0_I1;
assign Mux2xBits8_inst0_I1 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xBits8 Mux2xBits8_inst0 (
    .I0(Mux2xBits8_inst0_I0),
    .I1(Mux2xBits8_inst0_I1),
    .S(magma_Bits_3_eq_inst7_out),
    .O(Mux2xBits8_inst0_O)
);
wire [7:0] Mux2xBits8_inst1_I1;
assign Mux2xBits8_inst1_I1 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xBits8 Mux2xBits8_inst1 (
    .I0(Mux2xBits8_inst0_O),
    .I1(Mux2xBits8_inst1_I1),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xBits8_inst1_O)
);
wire [7:0] Mux2xBits8_inst2_I1;
assign Mux2xBits8_inst2_I1 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xBits8 Mux2xBits8_inst2 (
    .I0(Mux2xBits8_inst1_O),
    .I1(Mux2xBits8_inst2_I1),
    .S(magma_Bits_3_eq_inst5_out),
    .O(Mux2xBits8_inst2_O)
);
wire [7:0] Mux2xBits8_inst3_I1;
assign Mux2xBits8_inst3_I1 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xBits8 Mux2xBits8_inst3 (
    .I0(Mux2xBits8_inst2_O),
    .I1(Mux2xBits8_inst3_I1),
    .S(magma_Bits_3_eq_inst4_out),
    .O(Mux2xBits8_inst3_O)
);
wire [7:0] Mux2xBits8_inst4_I1;
assign Mux2xBits8_inst4_I1 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xBits8 Mux2xBits8_inst4 (
    .I0(Mux2xBits8_inst3_O),
    .I1(Mux2xBits8_inst4_I1),
    .S(magma_Bits_3_eq_inst3_out),
    .O(Mux2xBits8_inst4_O)
);
wire [7:0] Mux2xBits8_inst5_I1;
assign Mux2xBits8_inst5_I1 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xBits8 Mux2xBits8_inst5 (
    .I0(Mux2xBits8_inst4_O),
    .I1(Mux2xBits8_inst5_I1),
    .S(magma_Bits_3_eq_inst2_out),
    .O(Mux2xBits8_inst5_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst0 (
    .I0(const_65409_16_out),
    .I1(const_0_16_out),
    .S(magma_Bit_not_inst0_out),
    .O(Mux2xSInt16_inst0_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst1 (
    .I0(Mux2xSInt16_inst0_O),
    .I1(const_1_16_out),
    .S(magma_Bit_not_inst1_out),
    .O(Mux2xSInt16_inst1_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst10 (
    .I0(Mux2xSInt16_inst9_O),
    .I1(const_2_16_out),
    .S(magma_Bit_not_inst11_out),
    .O(Mux2xSInt16_inst10_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst11 (
    .I0(Mux2xSInt16_inst10_O),
    .I1(const_3_16_out),
    .S(magma_Bit_not_inst12_out),
    .O(Mux2xSInt16_inst11_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst12 (
    .I0(Mux2xSInt16_inst11_O),
    .I1(const_4_16_out),
    .S(magma_Bit_not_inst13_out),
    .O(Mux2xSInt16_inst12_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst13 (
    .I0(Mux2xSInt16_inst12_O),
    .I1(const_5_16_out),
    .S(magma_Bit_not_inst14_out),
    .O(Mux2xSInt16_inst13_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst14 (
    .I0(Mux2xSInt16_inst13_O),
    .I1(const_6_16_out),
    .S(magma_Bit_not_inst15_out),
    .O(Mux2xSInt16_inst14_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst15 (
    .I0(Mux2xSInt16_inst14_O),
    .I1(const_7_16_out),
    .S(magma_Bit_not_inst16_out),
    .O(Mux2xSInt16_inst15_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst16 (
    .I0(Mux2xSInt16_inst15_O),
    .I1(const_8_16_out),
    .S(magma_Bit_not_inst17_out),
    .O(Mux2xSInt16_inst16_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst17 (
    .I0(Mux2xSInt16_inst16_O),
    .I1(const_9_16_out),
    .S(magma_Bit_not_inst18_out),
    .O(Mux2xSInt16_inst17_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst18 (
    .I0(Mux2xSInt16_inst17_O),
    .I1(const_10_16_out),
    .S(magma_Bit_not_inst19_out),
    .O(Mux2xSInt16_inst18_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst19 (
    .I0(Mux2xSInt16_inst18_O),
    .I1(const_11_16_out),
    .S(magma_Bit_not_inst20_out),
    .O(Mux2xSInt16_inst19_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst2 (
    .I0(Mux2xSInt16_inst1_O),
    .I1(const_2_16_out),
    .S(magma_Bit_not_inst2_out),
    .O(Mux2xSInt16_inst2_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst20 (
    .I0(Mux2xSInt16_inst19_O),
    .I1(const_12_16_out),
    .S(magma_Bit_not_inst21_out),
    .O(Mux2xSInt16_inst20_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst21 (
    .I0(Mux2xSInt16_inst20_O),
    .I1(const_13_16_out),
    .S(magma_Bit_not_inst22_out),
    .O(Mux2xSInt16_inst21_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst22 (
    .I0(Mux2xSInt16_inst21_O),
    .I1(const_14_16_out),
    .S(magma_Bit_not_inst23_out),
    .O(Mux2xSInt16_inst22_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst23 (
    .I0(Mux2xSInt16_inst22_O),
    .I1(const_15_16_out),
    .S(magma_Bit_not_inst24_out),
    .O(Mux2xSInt16_inst23_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst24 (
    .I0(const_32512_16_out),
    .I1(const_127_16_out),
    .S(magma_Bits_3_eq_inst0_out),
    .O(Mux2xSInt16_inst24_O)
);
wire [15:0] Mux2xSInt16_inst25_I1;
assign Mux2xSInt16_inst25_I1 = {Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[7],Mux2xSInt9_inst0_O[6],Mux2xSInt9_inst0_O[5],Mux2xSInt9_inst0_O[4],Mux2xSInt9_inst0_O[3],Mux2xSInt9_inst0_O[2],Mux2xSInt9_inst0_O[1],Mux2xSInt9_inst0_O[0]};
PEGEN_Mux2xSInt16 Mux2xSInt16_inst25 (
    .I0(Mux2xBits16_inst2_O),
    .I1(Mux2xSInt16_inst25_I1),
    .S(magma_Bits_3_eq_inst0_out),
    .O(Mux2xSInt16_inst25_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst26 (
    .I0(magma_SInt_16_sub_inst1_out),
    .I1(magma_SInt_16_sub_inst0_out),
    .S(magma_Bits_3_eq_inst0_out),
    .O(Mux2xSInt16_inst26_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst27 (
    .I0(Mux2xSInt16_inst23_O),
    .I1(Mux2xSInt16_inst7_O),
    .S(magma_Bits_3_eq_inst0_out),
    .O(Mux2xSInt16_inst27_O)
);
wire [15:0] Mux2xSInt16_inst28_I0;
assign Mux2xSInt16_inst28_I0 = {magma_Bits_23_lshr_inst0_out[15],magma_Bits_23_lshr_inst0_out[14],magma_Bits_23_lshr_inst0_out[13],magma_Bits_23_lshr_inst0_out[12],magma_Bits_23_lshr_inst0_out[11],magma_Bits_23_lshr_inst0_out[10],magma_Bits_23_lshr_inst0_out[9],magma_Bits_23_lshr_inst0_out[8],magma_Bits_23_lshr_inst0_out[7],magma_Bits_23_lshr_inst0_out[6],magma_Bits_23_lshr_inst0_out[5],magma_Bits_23_lshr_inst0_out[4],magma_Bits_23_lshr_inst0_out[3],magma_Bits_23_lshr_inst0_out[2],magma_Bits_23_lshr_inst0_out[1],magma_Bits_23_lshr_inst0_out[0]};
PEGEN_Mux2xSInt16 Mux2xSInt16_inst28 (
    .I0(Mux2xSInt16_inst28_I0),
    .I1(magma_SInt_16_neg_inst1_out),
    .S(magma_Bits_16_eq_inst0_out),
    .O(Mux2xSInt16_inst28_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst29 (
    .I0(magma_Bits_16_and_inst12_out),
    .I1(magma_SInt_16_neg_inst2_out),
    .S(magma_Bits_16_eq_inst1_out),
    .O(Mux2xSInt16_inst29_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst3 (
    .I0(Mux2xSInt16_inst2_O),
    .I1(const_3_16_out),
    .S(magma_Bit_not_inst3_out),
    .O(Mux2xSInt16_inst3_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst30 (
    .I0(Mux2xSInt16_inst29_O),
    .I1(Mux2xSInt16_inst28_O),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xSInt16_inst30_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst4 (
    .I0(Mux2xSInt16_inst3_O),
    .I1(const_4_16_out),
    .S(magma_Bit_not_inst4_out),
    .O(Mux2xSInt16_inst4_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst5 (
    .I0(Mux2xSInt16_inst4_O),
    .I1(const_5_16_out),
    .S(magma_Bit_not_inst5_out),
    .O(Mux2xSInt16_inst5_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst6 (
    .I0(Mux2xSInt16_inst5_O),
    .I1(const_6_16_out),
    .S(magma_Bit_not_inst6_out),
    .O(Mux2xSInt16_inst6_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst7 (
    .I0(Mux2xSInt16_inst6_O),
    .I1(const_7_16_out),
    .S(magma_Bit_not_inst7_out),
    .O(Mux2xSInt16_inst7_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst8 (
    .I0(const_65409_16_out),
    .I1(const_0_16_out),
    .S(magma_Bit_not_inst9_out),
    .O(Mux2xSInt16_inst8_O)
);
PEGEN_Mux2xSInt16 Mux2xSInt16_inst9 (
    .I0(Mux2xSInt16_inst8_O),
    .I1(const_1_16_out),
    .S(magma_Bit_not_inst10_out),
    .O(Mux2xSInt16_inst9_O)
);
PEGEN_Mux2xSInt9 Mux2xSInt9_inst0 (
    .I0(magma_SInt_9_sub_inst0_out),
    .I1(magma_SInt_9_neg_inst0_out),
    .S(magma_SInt_9_slt_inst0_out),
    .O(Mux2xSInt9_inst0_O)
);
wire [8:0] Mux2xSInt9_inst1_I0;
assign Mux2xSInt9_inst1_I0 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
wire [8:0] Mux2xSInt9_inst1_I1;
assign Mux2xSInt9_inst1_I1 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xSInt9 Mux2xSInt9_inst1 (
    .I0(Mux2xSInt9_inst1_I0),
    .I1(Mux2xSInt9_inst1_I1),
    .S(magma_Bits_3_eq_inst7_out),
    .O(Mux2xSInt9_inst1_O)
);
PEGEN_Mux2xSInt9 Mux2xSInt9_inst10 (
    .I0(Mux2xSInt9_inst8_O),
    .I1(magma_SInt_9_sub_inst0_out),
    .S(magma_Bits_3_eq_inst3_out),
    .O(Mux2xSInt9_inst10_O)
);
wire [8:0] Mux2xSInt9_inst11_I1;
assign Mux2xSInt9_inst11_I1 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xSInt9 Mux2xSInt9_inst11 (
    .I0(Mux2xSInt9_inst9_O),
    .I1(Mux2xSInt9_inst11_I1),
    .S(magma_Bits_3_eq_inst2_out),
    .O(Mux2xSInt9_inst11_O)
);
PEGEN_Mux2xSInt9 Mux2xSInt9_inst12 (
    .I0(Mux2xSInt9_inst10_O),
    .I1(magma_SInt_9_sub_inst0_out),
    .S(magma_Bits_3_eq_inst2_out),
    .O(Mux2xSInt9_inst12_O)
);
PEGEN_Mux2xSInt9 Mux2xSInt9_inst2 (
    .I0(magma_SInt_9_sub_inst0_out),
    .I1(magma_SInt_9_sub_inst2_out),
    .S(magma_Bits_3_eq_inst7_out),
    .O(Mux2xSInt9_inst2_O)
);
wire [8:0] Mux2xSInt9_inst3_I1;
assign Mux2xSInt9_inst3_I1 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xSInt9 Mux2xSInt9_inst3 (
    .I0(Mux2xSInt9_inst1_O),
    .I1(Mux2xSInt9_inst3_I1),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xSInt9_inst3_O)
);
PEGEN_Mux2xSInt9 Mux2xSInt9_inst4 (
    .I0(Mux2xSInt9_inst2_O),
    .I1(magma_SInt_9_sub_inst1_out),
    .S(magma_Bits_3_eq_inst6_out),
    .O(Mux2xSInt9_inst4_O)
);
wire [8:0] Mux2xSInt9_inst5_I1;
assign Mux2xSInt9_inst5_I1 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xSInt9 Mux2xSInt9_inst5 (
    .I0(Mux2xSInt9_inst3_O),
    .I1(Mux2xSInt9_inst5_I1),
    .S(magma_Bits_3_eq_inst5_out),
    .O(Mux2xSInt9_inst5_O)
);
PEGEN_Mux2xSInt9 Mux2xSInt9_inst6 (
    .I0(Mux2xSInt9_inst4_O),
    .I1(magma_SInt_9_sub_inst0_out),
    .S(magma_Bits_3_eq_inst5_out),
    .O(Mux2xSInt9_inst6_O)
);
wire [8:0] Mux2xSInt9_inst7_I1;
assign Mux2xSInt9_inst7_I1 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xSInt9 Mux2xSInt9_inst7 (
    .I0(Mux2xSInt9_inst5_O),
    .I1(Mux2xSInt9_inst7_I1),
    .S(magma_Bits_3_eq_inst4_out),
    .O(Mux2xSInt9_inst7_O)
);
PEGEN_Mux2xSInt9 Mux2xSInt9_inst8 (
    .I0(Mux2xSInt9_inst6_O),
    .I1(magma_SInt_9_sub_inst0_out),
    .S(magma_Bits_3_eq_inst4_out),
    .O(Mux2xSInt9_inst8_O)
);
wire [8:0] Mux2xSInt9_inst9_I1;
assign Mux2xSInt9_inst9_I1 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_Mux2xSInt9 Mux2xSInt9_inst9 (
    .I0(Mux2xSInt9_inst7_O),
    .I1(Mux2xSInt9_inst9_I1),
    .S(magma_Bits_3_eq_inst3_out),
    .O(Mux2xSInt9_inst9_O)
);
PEGEN_corebit_const #(
    .value(1'b0)
) bit_const_0_None (
    .out(bit_const_0_None_out)
);
PEGEN_corebit_const #(
    .value(1'b1)
) bit_const_1_None (
    .out(bit_const_1_None_out)
);
PEGEN_coreir_const #(
    .value(16'h0000),
    .width(16)
) const_0_16 (
    .out(const_0_16_out)
);
PEGEN_coreir_const #(
    .value(23'h000000),
    .width(23)
) const_0_23 (
    .out(const_0_23_out)
);
PEGEN_coreir_const #(
    .value(3'h0),
    .width(3)
) const_0_3 (
    .out(const_0_3_out)
);
PEGEN_coreir_const #(
    .value(9'h000),
    .width(9)
) const_0_9 (
    .out(const_0_9_out)
);
PEGEN_coreir_const #(
    .value(16'h000a),
    .width(16)
) const_10_16 (
    .out(const_10_16_out)
);
PEGEN_coreir_const #(
    .value(16'h000b),
    .width(16)
) const_11_16 (
    .out(const_11_16_out)
);
PEGEN_coreir_const #(
    .value(16'h007f),
    .width(16)
) const_127_16 (
    .out(const_127_16_out)
);
PEGEN_coreir_const #(
    .value(8'h7f),
    .width(8)
) const_127_8 (
    .out(const_127_8_out)
);
PEGEN_coreir_const #(
    .value(9'h07f),
    .width(9)
) const_127_9 (
    .out(const_127_9_out)
);
PEGEN_coreir_const #(
    .value(16'h0080),
    .width(16)
) const_128_16 (
    .out(const_128_16_out)
);
PEGEN_coreir_const #(
    .value(16'h000c),
    .width(16)
) const_12_16 (
    .out(const_12_16_out)
);
PEGEN_coreir_const #(
    .value(16'h000d),
    .width(16)
) const_13_16 (
    .out(const_13_16_out)
);
PEGEN_coreir_const #(
    .value(8'h8e),
    .width(8)
) const_142_8 (
    .out(const_142_8_out)
);
PEGEN_coreir_const #(
    .value(16'h000e),
    .width(16)
) const_14_16 (
    .out(const_14_16_out)
);
PEGEN_coreir_const #(
    .value(16'h000f),
    .width(16)
) const_15_16 (
    .out(const_15_16_out)
);
PEGEN_coreir_const #(
    .value(1'h1),
    .width(1)
) const_1_1 (
    .out(const_1_1_out)
);
PEGEN_coreir_const #(
    .value(16'h0001),
    .width(16)
) const_1_16 (
    .out(const_1_16_out)
);
PEGEN_coreir_const #(
    .value(3'h1),
    .width(3)
) const_1_3 (
    .out(const_1_3_out)
);
PEGEN_coreir_const #(
    .value(9'h0ff),
    .width(9)
) const_255_9 (
    .out(const_255_9_out)
);
PEGEN_coreir_const #(
    .value(16'h0002),
    .width(16)
) const_2_16 (
    .out(const_2_16_out)
);
PEGEN_coreir_const #(
    .value(3'h2),
    .width(3)
) const_2_3 (
    .out(const_2_3_out)
);
PEGEN_coreir_const #(
    .value(16'h7f00),
    .width(16)
) const_32512_16 (
    .out(const_32512_16_out)
);
PEGEN_coreir_const #(
    .value(16'h7f80),
    .width(16)
) const_32640_16 (
    .out(const_32640_16_out)
);
PEGEN_coreir_const #(
    .value(16'h8000),
    .width(16)
) const_32768_16 (
    .out(const_32768_16_out)
);
PEGEN_coreir_const #(
    .value(16'h0003),
    .width(16)
) const_3_16 (
    .out(const_3_16_out)
);
PEGEN_coreir_const #(
    .value(3'h3),
    .width(3)
) const_3_3 (
    .out(const_3_3_out)
);
PEGEN_coreir_const #(
    .value(16'h0004),
    .width(16)
) const_4_16 (
    .out(const_4_16_out)
);
PEGEN_coreir_const #(
    .value(3'h4),
    .width(3)
) const_4_3 (
    .out(const_4_3_out)
);
PEGEN_coreir_const #(
    .value(16'h0005),
    .width(16)
) const_5_16 (
    .out(const_5_16_out)
);
PEGEN_coreir_const #(
    .value(3'h5),
    .width(3)
) const_5_3 (
    .out(const_5_3_out)
);
PEGEN_coreir_const #(
    .value(16'hff81),
    .width(16)
) const_65409_16 (
    .out(const_65409_16_out)
);
PEGEN_coreir_const #(
    .value(16'h0006),
    .width(16)
) const_6_16 (
    .out(const_6_16_out)
);
PEGEN_coreir_const #(
    .value(3'h6),
    .width(3)
) const_6_3 (
    .out(const_6_3_out)
);
PEGEN_coreir_const #(
    .value(16'h0007),
    .width(16)
) const_7_16 (
    .out(const_7_16_out)
);
PEGEN_coreir_const #(
    .value(23'h000007),
    .width(23)
) const_7_23 (
    .out(const_7_23_out)
);
PEGEN_coreir_const #(
    .value(16'h0008),
    .width(16)
) const_8_16 (
    .out(const_8_16_out)
);
PEGEN_coreir_const #(
    .value(16'h0009),
    .width(16)
) const_9_16 (
    .out(const_9_16_out)
);
PEGEN_corebit_not magma_Bit_not_inst0 (
    .in(magma_Bit_xor_inst0_out),
    .out(magma_Bit_not_inst0_out)
);
PEGEN_corebit_not magma_Bit_not_inst1 (
    .in(magma_Bit_xor_inst1_out),
    .out(magma_Bit_not_inst1_out)
);
PEGEN_corebit_not magma_Bit_not_inst10 (
    .in(magma_Bit_xor_inst10_out),
    .out(magma_Bit_not_inst10_out)
);
PEGEN_corebit_not magma_Bit_not_inst11 (
    .in(magma_Bit_xor_inst11_out),
    .out(magma_Bit_not_inst11_out)
);
PEGEN_corebit_not magma_Bit_not_inst12 (
    .in(magma_Bit_xor_inst12_out),
    .out(magma_Bit_not_inst12_out)
);
PEGEN_corebit_not magma_Bit_not_inst13 (
    .in(magma_Bit_xor_inst13_out),
    .out(magma_Bit_not_inst13_out)
);
PEGEN_corebit_not magma_Bit_not_inst14 (
    .in(magma_Bit_xor_inst14_out),
    .out(magma_Bit_not_inst14_out)
);
PEGEN_corebit_not magma_Bit_not_inst15 (
    .in(magma_Bit_xor_inst15_out),
    .out(magma_Bit_not_inst15_out)
);
PEGEN_corebit_not magma_Bit_not_inst16 (
    .in(magma_Bit_xor_inst16_out),
    .out(magma_Bit_not_inst16_out)
);
PEGEN_corebit_not magma_Bit_not_inst17 (
    .in(magma_Bit_xor_inst17_out),
    .out(magma_Bit_not_inst17_out)
);
PEGEN_corebit_not magma_Bit_not_inst18 (
    .in(magma_Bit_xor_inst18_out),
    .out(magma_Bit_not_inst18_out)
);
PEGEN_corebit_not magma_Bit_not_inst19 (
    .in(magma_Bit_xor_inst19_out),
    .out(magma_Bit_not_inst19_out)
);
PEGEN_corebit_not magma_Bit_not_inst2 (
    .in(magma_Bit_xor_inst2_out),
    .out(magma_Bit_not_inst2_out)
);
PEGEN_corebit_not magma_Bit_not_inst20 (
    .in(magma_Bit_xor_inst20_out),
    .out(magma_Bit_not_inst20_out)
);
PEGEN_corebit_not magma_Bit_not_inst21 (
    .in(magma_Bit_xor_inst21_out),
    .out(magma_Bit_not_inst21_out)
);
PEGEN_corebit_not magma_Bit_not_inst22 (
    .in(magma_Bit_xor_inst22_out),
    .out(magma_Bit_not_inst22_out)
);
PEGEN_corebit_not magma_Bit_not_inst23 (
    .in(magma_Bit_xor_inst23_out),
    .out(magma_Bit_not_inst23_out)
);
PEGEN_corebit_not magma_Bit_not_inst24 (
    .in(magma_Bit_xor_inst24_out),
    .out(magma_Bit_not_inst24_out)
);
PEGEN_corebit_not magma_Bit_not_inst3 (
    .in(magma_Bit_xor_inst3_out),
    .out(magma_Bit_not_inst3_out)
);
PEGEN_corebit_not magma_Bit_not_inst4 (
    .in(magma_Bit_xor_inst4_out),
    .out(magma_Bit_not_inst4_out)
);
PEGEN_corebit_not magma_Bit_not_inst5 (
    .in(magma_Bit_xor_inst5_out),
    .out(magma_Bit_not_inst5_out)
);
PEGEN_corebit_not magma_Bit_not_inst6 (
    .in(magma_Bit_xor_inst6_out),
    .out(magma_Bit_not_inst6_out)
);
PEGEN_corebit_not magma_Bit_not_inst7 (
    .in(magma_Bit_xor_inst7_out),
    .out(magma_Bit_not_inst7_out)
);
PEGEN_corebit_not magma_Bit_not_inst8 (
    .in(magma_Bit_xor_inst8_out),
    .out(magma_Bit_not_inst8_out)
);
PEGEN_corebit_not magma_Bit_not_inst9 (
    .in(magma_Bit_xor_inst9_out),
    .out(magma_Bit_not_inst9_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst0 (
    .in0(Mux2xSInt9_inst0_O[0]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst0_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst1 (
    .in0(Mux2xSInt9_inst0_O[1]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst1_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst10 (
    .in0(Mux2xBits16_inst2_O[1]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst10_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst11 (
    .in0(Mux2xBits16_inst2_O[2]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst11_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst12 (
    .in0(Mux2xBits16_inst2_O[3]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst12_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst13 (
    .in0(Mux2xBits16_inst2_O[4]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst13_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst14 (
    .in0(Mux2xBits16_inst2_O[5]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst14_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst15 (
    .in0(Mux2xBits16_inst2_O[6]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst15_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst16 (
    .in0(Mux2xBits16_inst2_O[7]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst16_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst17 (
    .in0(Mux2xBits16_inst2_O[8]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst17_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst18 (
    .in0(Mux2xBits16_inst2_O[9]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst18_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst19 (
    .in0(Mux2xBits16_inst2_O[10]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst19_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst2 (
    .in0(Mux2xSInt9_inst0_O[2]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst2_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst20 (
    .in0(Mux2xBits16_inst2_O[11]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst20_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst21 (
    .in0(Mux2xBits16_inst2_O[12]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst21_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst22 (
    .in0(Mux2xBits16_inst2_O[13]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst22_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst23 (
    .in0(Mux2xBits16_inst2_O[14]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst23_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst24 (
    .in0(Mux2xBits16_inst2_O[15]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst24_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst3 (
    .in0(Mux2xSInt9_inst0_O[3]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst3_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst4 (
    .in0(Mux2xSInt9_inst0_O[4]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst4_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst5 (
    .in0(Mux2xSInt9_inst0_O[5]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst5_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst6 (
    .in0(Mux2xSInt9_inst0_O[6]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst6_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst7 (
    .in0(Mux2xSInt9_inst0_O[7]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst7_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst8 (
    .in0(Mux2xBits16_inst1_O[15]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst8_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst9 (
    .in0(Mux2xBits16_inst2_O[0]),
    .in1(bit_const_1_None_out),
    .out(magma_Bit_xor_inst9_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst0 (
    .in0(a),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_and_inst0_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst1 (
    .in0(magma_Bits_16_shl_inst0_out),
    .in1(const_32640_16_out),
    .out(magma_Bits_16_and_inst1_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst10 (
    .in0(a),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_and_inst10_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst11 (
    .in0(a),
    .in1(const_127_16_out),
    .out(magma_Bits_16_and_inst11_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst12 (
    .in0(Mux2xBits16_inst6_O),
    .in1(const_127_16_out),
    .out(magma_Bits_16_and_inst12_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst2 (
    .in0(a),
    .in1(const_127_16_out),
    .out(magma_Bits_16_and_inst2_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst3 (
    .in0(a),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_and_inst3_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst4 (
    .in0(a),
    .in1(const_127_16_out),
    .out(magma_Bits_16_and_inst4_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst5 (
    .in0(a),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_and_inst5_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst6 (
    .in0(b),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_and_inst6_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst7 (
    .in0(a),
    .in1(const_127_16_out),
    .out(magma_Bits_16_and_inst7_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst8 (
    .in0(a),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_and_inst8_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst9 (
    .in0(a),
    .in1(const_127_16_out),
    .out(magma_Bits_16_and_inst9_out)
);
PEGEN_coreir_eq #(
    .width(16)
) magma_Bits_16_eq_inst0 (
    .in0(magma_Bits_16_and_inst8_out),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(16)
) magma_Bits_16_eq_inst1 (
    .in0(magma_Bits_16_and_inst10_out),
    .in1(const_32768_16_out),
    .out(magma_Bits_16_eq_inst1_out)
);
PEGEN_coreir_lshr #(
    .width(16)
) magma_Bits_16_lshr_inst0 (
    .in0(Mux2xBits16_inst4_O),
    .in1(const_8_16_out),
    .out(magma_Bits_16_lshr_inst0_out)
);
wire [15:0] magma_Bits_16_lshr_inst1_in1;
assign magma_Bits_16_lshr_inst1_in1 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,magma_SInt_9_neg_inst1_out};
PEGEN_coreir_lshr #(
    .width(16)
) magma_Bits_16_lshr_inst1 (
    .in0(magma_Bits_16_or_inst8_out),
    .in1(magma_Bits_16_lshr_inst1_in1),
    .out(magma_Bits_16_lshr_inst1_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst0 (
    .in0(Mux2xBits16_inst3_O),
    .in1(magma_Bits_16_and_inst1_out),
    .out(magma_Bits_16_or_inst0_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst1 (
    .in0(magma_Bits_16_or_inst0_out),
    .in1(Mux2xBits16_inst5_O),
    .out(magma_Bits_16_or_inst1_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst2 (
    .in0(magma_Bits_16_and_inst3_out),
    .in1(magma_Bits_16_shl_inst1_out),
    .out(magma_Bits_16_or_inst2_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst3 (
    .in0(magma_Bits_16_or_inst2_out),
    .in1(magma_Bits_16_and_inst4_out),
    .out(magma_Bits_16_or_inst3_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst4 (
    .in0(magma_Bits_16_and_inst5_out),
    .in1(magma_Bits_16_and_inst6_out),
    .out(magma_Bits_16_or_inst4_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst5 (
    .in0(magma_Bits_16_or_inst4_out),
    .in1(magma_Bits_16_shl_inst2_out),
    .out(magma_Bits_16_or_inst5_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst6 (
    .in0(magma_Bits_16_or_inst5_out),
    .in1(magma_Bits_16_and_inst7_out),
    .out(magma_Bits_16_or_inst6_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst7 (
    .in0(magma_Bits_16_and_inst9_out),
    .in1(const_128_16_out),
    .out(magma_Bits_16_or_inst7_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst8 (
    .in0(magma_Bits_16_and_inst11_out),
    .in1(const_128_16_out),
    .out(magma_Bits_16_or_inst8_out)
);
PEGEN_coreir_shl #(
    .width(16)
) magma_Bits_16_shl_inst0 (
    .in0(magma_SInt_16_add_inst0_out),
    .in1(const_7_16_out),
    .out(magma_Bits_16_shl_inst0_out)
);
wire [15:0] magma_Bits_16_shl_inst1_in0;
assign magma_Bits_16_shl_inst1_in0 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,magma_UInt_8_add_inst0_out};
PEGEN_coreir_shl #(
    .width(16)
) magma_Bits_16_shl_inst1 (
    .in0(magma_Bits_16_shl_inst1_in0),
    .in1(const_7_16_out),
    .out(magma_Bits_16_shl_inst1_out)
);
wire [15:0] magma_Bits_16_shl_inst2_in0;
assign magma_Bits_16_shl_inst2_in0 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,magma_UInt_8_add_inst1_out};
PEGEN_coreir_shl #(
    .width(16)
) magma_Bits_16_shl_inst2 (
    .in0(magma_Bits_16_shl_inst2_in0),
    .in1(const_7_16_out),
    .out(magma_Bits_16_shl_inst2_out)
);
wire [15:0] magma_Bits_16_shl_inst3_in1;
assign magma_Bits_16_shl_inst3_in1 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,magma_SInt_9_sub_inst2_out};
PEGEN_coreir_shl #(
    .width(16)
) magma_Bits_16_shl_inst3 (
    .in0(magma_Bits_16_or_inst8_out),
    .in1(magma_Bits_16_shl_inst3_in1),
    .out(magma_Bits_16_shl_inst3_out)
);
PEGEN_coreir_eq #(
    .width(1)
) magma_Bits_1_eq_inst0 (
    .in0(signed_),
    .in1(const_1_1_out),
    .out(magma_Bits_1_eq_inst0_out)
);
PEGEN_coreir_lshr #(
    .width(23)
) magma_Bits_23_lshr_inst0 (
    .in0(Mux2xBits23_inst0_O),
    .in1(const_7_23_out),
    .out(magma_Bits_23_lshr_inst0_out)
);
wire [22:0] magma_Bits_23_shl_inst0_in0;
assign magma_Bits_23_shl_inst0_in0 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,magma_Bits_16_or_inst7_out};
wire [22:0] magma_Bits_23_shl_inst0_in1;
assign magma_Bits_23_shl_inst0_in1 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,magma_SInt_9_sub_inst1_out};
PEGEN_coreir_shl #(
    .width(23)
) magma_Bits_23_shl_inst0 (
    .in0(magma_Bits_23_shl_inst0_in0),
    .in1(magma_Bits_23_shl_inst0_in1),
    .out(magma_Bits_23_shl_inst0_out)
);
PEGEN_coreir_eq #(
    .width(3)
) magma_Bits_3_eq_inst0 (
    .in0(op),
    .in1(const_3_3_out),
    .out(magma_Bits_3_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(3)
) magma_Bits_3_eq_inst1 (
    .in0(op),
    .in1(const_6_3_out),
    .out(magma_Bits_3_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(3)
) magma_Bits_3_eq_inst2 (
    .in0(op),
    .in1(const_0_3_out),
    .out(magma_Bits_3_eq_inst2_out)
);
PEGEN_coreir_eq #(
    .width(3)
) magma_Bits_3_eq_inst3 (
    .in0(op),
    .in1(const_1_3_out),
    .out(magma_Bits_3_eq_inst3_out)
);
PEGEN_coreir_eq #(
    .width(3)
) magma_Bits_3_eq_inst4 (
    .in0(op),
    .in1(const_2_3_out),
    .out(magma_Bits_3_eq_inst4_out)
);
PEGEN_coreir_eq #(
    .width(3)
) magma_Bits_3_eq_inst5 (
    .in0(op),
    .in1(const_3_3_out),
    .out(magma_Bits_3_eq_inst5_out)
);
PEGEN_coreir_eq #(
    .width(3)
) magma_Bits_3_eq_inst6 (
    .in0(op),
    .in1(const_4_3_out),
    .out(magma_Bits_3_eq_inst6_out)
);
PEGEN_coreir_eq #(
    .width(3)
) magma_Bits_3_eq_inst7 (
    .in0(op),
    .in1(const_5_3_out),
    .out(magma_Bits_3_eq_inst7_out)
);
PEGEN_coreir_add #(
    .width(16)
) magma_SInt_16_add_inst0 (
    .in0(Mux2xSInt16_inst27_O),
    .in1(const_127_16_out),
    .out(magma_SInt_16_add_inst0_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_SInt_16_and_inst0 (
    .in0(magma_SInt_16_shl_inst0_out),
    .in1(Mux2xSInt16_inst24_O),
    .out(magma_SInt_16_and_inst0_out)
);
PEGEN_coreir_neg #(
    .width(16)
) magma_SInt_16_neg_inst0 (
    .in(a),
    .out(magma_SInt_16_neg_inst0_out)
);
wire [15:0] magma_SInt_16_neg_inst1_in;
assign magma_SInt_16_neg_inst1_in = {magma_Bits_23_lshr_inst0_out[15],magma_Bits_23_lshr_inst0_out[14],magma_Bits_23_lshr_inst0_out[13],magma_Bits_23_lshr_inst0_out[12],magma_Bits_23_lshr_inst0_out[11],magma_Bits_23_lshr_inst0_out[10],magma_Bits_23_lshr_inst0_out[9],magma_Bits_23_lshr_inst0_out[8],magma_Bits_23_lshr_inst0_out[7],magma_Bits_23_lshr_inst0_out[6],magma_Bits_23_lshr_inst0_out[5],magma_Bits_23_lshr_inst0_out[4],magma_Bits_23_lshr_inst0_out[3],magma_Bits_23_lshr_inst0_out[2],magma_Bits_23_lshr_inst0_out[1],magma_Bits_23_lshr_inst0_out[0]};
PEGEN_coreir_neg #(
    .width(16)
) magma_SInt_16_neg_inst1 (
    .in(magma_SInt_16_neg_inst1_in),
    .out(magma_SInt_16_neg_inst1_out)
);
PEGEN_coreir_neg #(
    .width(16)
) magma_SInt_16_neg_inst2 (
    .in(magma_Bits_16_and_inst12_out),
    .out(magma_SInt_16_neg_inst2_out)
);
PEGEN_coreir_sge #(
    .width(16)
) magma_SInt_16_sge_inst0 (
    .in0(Mux2xSInt16_inst27_O),
    .in1(const_0_16_out),
    .out(magma_SInt_16_sge_inst0_out)
);
PEGEN_coreir_shl #(
    .width(16)
) magma_SInt_16_shl_inst0 (
    .in0(Mux2xSInt16_inst25_O),
    .in1(Mux2xSInt16_inst26_O),
    .out(magma_SInt_16_shl_inst0_out)
);
PEGEN_coreir_sub #(
    .width(16)
) magma_SInt_16_sub_inst0 (
    .in0(const_7_16_out),
    .in1(Mux2xSInt16_inst7_O),
    .out(magma_SInt_16_sub_inst0_out)
);
PEGEN_coreir_sub #(
    .width(16)
) magma_SInt_16_sub_inst1 (
    .in0(const_15_16_out),
    .in1(Mux2xSInt16_inst23_O),
    .out(magma_SInt_16_sub_inst1_out)
);
PEGEN_coreir_neg #(
    .width(9)
) magma_SInt_9_neg_inst0 (
    .in(magma_SInt_9_sub_inst0_out),
    .out(magma_SInt_9_neg_inst0_out)
);
PEGEN_coreir_neg #(
    .width(9)
) magma_SInt_9_neg_inst1 (
    .in(magma_SInt_9_sub_inst2_out),
    .out(magma_SInt_9_neg_inst1_out)
);
PEGEN_coreir_slt #(
    .width(9)
) magma_SInt_9_slt_inst0 (
    .in0(magma_SInt_9_sub_inst0_out),
    .in1(const_0_9_out),
    .out(magma_SInt_9_slt_inst0_out)
);
PEGEN_coreir_slt #(
    .width(9)
) magma_SInt_9_slt_inst1 (
    .in0(magma_SInt_9_sub_inst1_out),
    .in1(const_0_9_out),
    .out(magma_SInt_9_slt_inst1_out)
);
PEGEN_coreir_slt #(
    .width(9)
) magma_SInt_9_slt_inst2 (
    .in0(magma_SInt_9_sub_inst2_out),
    .in1(const_0_9_out),
    .out(magma_SInt_9_slt_inst2_out)
);
wire [8:0] magma_SInt_9_sub_inst0_in0;
assign magma_SInt_9_sub_inst0_in0 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_coreir_sub #(
    .width(9)
) magma_SInt_9_sub_inst0 (
    .in0(magma_SInt_9_sub_inst0_in0),
    .in1(const_127_9_out),
    .out(magma_SInt_9_sub_inst0_out)
);
wire [8:0] magma_SInt_9_sub_inst1_in0;
assign magma_SInt_9_sub_inst1_in0 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_coreir_sub #(
    .width(9)
) magma_SInt_9_sub_inst1 (
    .in0(magma_SInt_9_sub_inst1_in0),
    .in1(const_127_9_out),
    .out(magma_SInt_9_sub_inst1_out)
);
wire [8:0] magma_SInt_9_sub_inst2_in0;
assign magma_SInt_9_sub_inst2_in0 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_coreir_sub #(
    .width(9)
) magma_SInt_9_sub_inst2 (
    .in0(magma_SInt_9_sub_inst2_in0),
    .in1(const_127_9_out),
    .out(magma_SInt_9_sub_inst2_out)
);
wire [7:0] magma_UInt_8_add_inst0_in0;
assign magma_UInt_8_add_inst0_in0 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
wire [7:0] magma_UInt_8_add_inst0_in1;
assign magma_UInt_8_add_inst0_in1 = {b[7],b[6],b[5],b[4],b[3],b[2],b[1],b[0]};
PEGEN_coreir_add #(
    .width(8)
) magma_UInt_8_add_inst0 (
    .in0(magma_UInt_8_add_inst0_in0),
    .in1(magma_UInt_8_add_inst0_in1),
    .out(magma_UInt_8_add_inst0_out)
);
PEGEN_coreir_add #(
    .width(8)
) magma_UInt_8_add_inst1 (
    .in0(magma_UInt_8_sub_inst0_out),
    .in1(const_127_8_out),
    .out(magma_UInt_8_add_inst1_out)
);
wire [7:0] magma_UInt_8_sub_inst0_in0;
assign magma_UInt_8_sub_inst0_in0 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
wire [7:0] magma_UInt_8_sub_inst0_in1;
assign magma_UInt_8_sub_inst0_in1 = {b[14],b[13],b[12],b[11],b[10],b[9],b[8],b[7]};
PEGEN_coreir_sub #(
    .width(8)
) magma_UInt_8_sub_inst0 (
    .in0(magma_UInt_8_sub_inst0_in0),
    .in1(magma_UInt_8_sub_inst0_in1),
    .out(magma_UInt_8_sub_inst0_out)
);
wire [7:0] magma_UInt_8_ugt_inst0_in0;
assign magma_UInt_8_ugt_inst0_in0 = {a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
PEGEN_coreir_ugt #(
    .width(8)
) magma_UInt_8_ugt_inst0 (
    .in0(magma_UInt_8_ugt_inst0_in0),
    .in1(const_142_8_out),
    .out(magma_UInt_8_ugt_inst0_out)
);
wire [8:0] magma_UInt_9_add_inst0_in0;
assign magma_UInt_9_add_inst0_in0 = {bit_const_0_None_out,a[14],a[13],a[12],a[11],a[10],a[9],a[8],a[7]};
wire [8:0] magma_UInt_9_add_inst0_in1;
assign magma_UInt_9_add_inst0_in1 = {b[8],b[7],b[6],b[5],b[4],b[3],b[2],b[1],b[0]};
PEGEN_coreir_add #(
    .width(9)
) magma_UInt_9_add_inst0 (
    .in0(magma_UInt_9_add_inst0_in0),
    .in1(magma_UInt_9_add_inst0_in1),
    .out(magma_UInt_9_add_inst0_out)
);
PEGEN_coreir_ugt #(
    .width(9)
) magma_UInt_9_ugt_inst0 (
    .in0(magma_UInt_9_add_inst0_out),
    .in1(const_255_9_out),
    .out(magma_UInt_9_ugt_inst0_out)
);
assign res = Mux2xBits16_inst19_O;
assign res_p = Mux2xBit_inst10_O;
assign V = Mux2xBit_inst9_O;
endmodule

module PEGEN_Cond (
    input [4:0] code,
    input alu,
    input lut,
    input Z,
    input N,
    input C,
    input V,
    output O,
    input CLK,
    input ASYNCRESET
);
wire Mux2xBit_inst0_O;
wire Mux2xBit_inst1_O;
wire Mux2xBit_inst10_O;
wire Mux2xBit_inst11_O;
wire Mux2xBit_inst12_O;
wire Mux2xBit_inst13_O;
wire Mux2xBit_inst14_O;
wire Mux2xBit_inst15_O;
wire Mux2xBit_inst16_O;
wire Mux2xBit_inst17_O;
wire Mux2xBit_inst18_O;
wire Mux2xBit_inst2_O;
wire Mux2xBit_inst3_O;
wire Mux2xBit_inst4_O;
wire Mux2xBit_inst5_O;
wire Mux2xBit_inst6_O;
wire Mux2xBit_inst7_O;
wire Mux2xBit_inst8_O;
wire Mux2xBit_inst9_O;
wire [4:0] const_0_5_out;
wire [4:0] const_10_5_out;
wire [4:0] const_11_5_out;
wire [4:0] const_12_5_out;
wire [4:0] const_13_5_out;
wire [4:0] const_14_5_out;
wire [4:0] const_15_5_out;
wire [4:0] const_16_5_out;
wire [4:0] const_17_5_out;
wire [4:0] const_18_5_out;
wire [4:0] const_1_5_out;
wire [4:0] const_2_5_out;
wire [4:0] const_3_5_out;
wire [4:0] const_4_5_out;
wire [4:0] const_5_5_out;
wire [4:0] const_6_5_out;
wire [4:0] const_7_5_out;
wire [4:0] const_8_5_out;
wire [4:0] const_9_5_out;
wire magma_Bit_and_inst0_out;
wire magma_Bit_and_inst1_out;
wire magma_Bit_and_inst2_out;
wire magma_Bit_and_inst3_out;
wire magma_Bit_not_inst0_out;
wire magma_Bit_not_inst1_out;
wire magma_Bit_not_inst10_out;
wire magma_Bit_not_inst11_out;
wire magma_Bit_not_inst12_out;
wire magma_Bit_not_inst2_out;
wire magma_Bit_not_inst3_out;
wire magma_Bit_not_inst4_out;
wire magma_Bit_not_inst5_out;
wire magma_Bit_not_inst6_out;
wire magma_Bit_not_inst7_out;
wire magma_Bit_not_inst8_out;
wire magma_Bit_not_inst9_out;
wire magma_Bit_or_inst0_out;
wire magma_Bit_or_inst1_out;
wire magma_Bit_or_inst2_out;
wire magma_Bit_or_inst3_out;
wire magma_Bit_or_inst4_out;
wire magma_Bit_or_inst5_out;
wire magma_Bit_xor_inst0_out;
wire magma_Bit_xor_inst1_out;
wire magma_Bit_xor_inst2_out;
wire magma_Bit_xor_inst3_out;
wire magma_Bits_5_eq_inst0_out;
wire magma_Bits_5_eq_inst1_out;
wire magma_Bits_5_eq_inst10_out;
wire magma_Bits_5_eq_inst11_out;
wire magma_Bits_5_eq_inst12_out;
wire magma_Bits_5_eq_inst13_out;
wire magma_Bits_5_eq_inst14_out;
wire magma_Bits_5_eq_inst15_out;
wire magma_Bits_5_eq_inst16_out;
wire magma_Bits_5_eq_inst17_out;
wire magma_Bits_5_eq_inst18_out;
wire magma_Bits_5_eq_inst19_out;
wire magma_Bits_5_eq_inst2_out;
wire magma_Bits_5_eq_inst20_out;
wire magma_Bits_5_eq_inst3_out;
wire magma_Bits_5_eq_inst4_out;
wire magma_Bits_5_eq_inst5_out;
wire magma_Bits_5_eq_inst6_out;
wire magma_Bits_5_eq_inst7_out;
wire magma_Bits_5_eq_inst8_out;
wire magma_Bits_5_eq_inst9_out;
PEGEN_Mux2xBit Mux2xBit_inst0 (
    .I0(magma_Bit_and_inst3_out),
    .I1(magma_Bit_or_inst5_out),
    .S(magma_Bits_5_eq_inst20_out),
    .O(Mux2xBit_inst0_O)
);
PEGEN_Mux2xBit Mux2xBit_inst1 (
    .I0(Mux2xBit_inst0_O),
    .I1(magma_Bit_and_inst2_out),
    .S(magma_Bits_5_eq_inst19_out),
    .O(Mux2xBit_inst1_O)
);
PEGEN_Mux2xBit Mux2xBit_inst10 (
    .I0(Mux2xBit_inst9_O),
    .I1(magma_Bit_and_inst0_out),
    .S(magma_Bits_5_eq_inst10_out),
    .O(Mux2xBit_inst10_O)
);
PEGEN_Mux2xBit Mux2xBit_inst11 (
    .I0(Mux2xBit_inst10_O),
    .I1(magma_Bit_not_inst3_out),
    .S(magma_Bits_5_eq_inst9_out),
    .O(Mux2xBit_inst11_O)
);
PEGEN_Mux2xBit Mux2xBit_inst12 (
    .I0(Mux2xBit_inst11_O),
    .I1(V),
    .S(magma_Bits_5_eq_inst8_out),
    .O(Mux2xBit_inst12_O)
);
PEGEN_Mux2xBit Mux2xBit_inst13 (
    .I0(Mux2xBit_inst12_O),
    .I1(magma_Bit_not_inst2_out),
    .S(magma_Bits_5_eq_inst7_out),
    .O(Mux2xBit_inst13_O)
);
PEGEN_Mux2xBit Mux2xBit_inst14 (
    .I0(Mux2xBit_inst13_O),
    .I1(N),
    .S(magma_Bits_5_eq_inst6_out),
    .O(Mux2xBit_inst14_O)
);
PEGEN_Mux2xBit Mux2xBit_inst15 (
    .I0(Mux2xBit_inst14_O),
    .I1(magma_Bit_not_inst1_out),
    .S(magma_Bit_or_inst1_out),
    .O(Mux2xBit_inst15_O)
);
PEGEN_Mux2xBit Mux2xBit_inst16 (
    .I0(Mux2xBit_inst15_O),
    .I1(C),
    .S(magma_Bit_or_inst0_out),
    .O(Mux2xBit_inst16_O)
);
PEGEN_Mux2xBit Mux2xBit_inst17 (
    .I0(Mux2xBit_inst16_O),
    .I1(magma_Bit_not_inst0_out),
    .S(magma_Bits_5_eq_inst1_out),
    .O(Mux2xBit_inst17_O)
);
PEGEN_Mux2xBit Mux2xBit_inst18 (
    .I0(Mux2xBit_inst17_O),
    .I1(Z),
    .S(magma_Bits_5_eq_inst0_out),
    .O(Mux2xBit_inst18_O)
);
PEGEN_Mux2xBit Mux2xBit_inst2 (
    .I0(Mux2xBit_inst1_O),
    .I1(magma_Bit_or_inst4_out),
    .S(magma_Bits_5_eq_inst18_out),
    .O(Mux2xBit_inst2_O)
);
PEGEN_Mux2xBit Mux2xBit_inst3 (
    .I0(Mux2xBit_inst2_O),
    .I1(lut),
    .S(magma_Bits_5_eq_inst17_out),
    .O(Mux2xBit_inst3_O)
);
PEGEN_Mux2xBit Mux2xBit_inst4 (
    .I0(Mux2xBit_inst3_O),
    .I1(alu),
    .S(magma_Bits_5_eq_inst16_out),
    .O(Mux2xBit_inst4_O)
);
PEGEN_Mux2xBit Mux2xBit_inst5 (
    .I0(Mux2xBit_inst4_O),
    .I1(magma_Bit_or_inst3_out),
    .S(magma_Bits_5_eq_inst15_out),
    .O(Mux2xBit_inst5_O)
);
PEGEN_Mux2xBit Mux2xBit_inst6 (
    .I0(Mux2xBit_inst5_O),
    .I1(magma_Bit_and_inst1_out),
    .S(magma_Bits_5_eq_inst14_out),
    .O(Mux2xBit_inst6_O)
);
PEGEN_Mux2xBit Mux2xBit_inst7 (
    .I0(Mux2xBit_inst6_O),
    .I1(magma_Bit_xor_inst1_out),
    .S(magma_Bits_5_eq_inst13_out),
    .O(Mux2xBit_inst7_O)
);
PEGEN_Mux2xBit Mux2xBit_inst8 (
    .I0(Mux2xBit_inst7_O),
    .I1(magma_Bit_not_inst6_out),
    .S(magma_Bits_5_eq_inst12_out),
    .O(Mux2xBit_inst8_O)
);
PEGEN_Mux2xBit Mux2xBit_inst9 (
    .I0(Mux2xBit_inst8_O),
    .I1(magma_Bit_or_inst2_out),
    .S(magma_Bits_5_eq_inst11_out),
    .O(Mux2xBit_inst9_O)
);
PEGEN_coreir_const #(
    .value(5'h00),
    .width(5)
) const_0_5 (
    .out(const_0_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0a),
    .width(5)
) const_10_5 (
    .out(const_10_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0b),
    .width(5)
) const_11_5 (
    .out(const_11_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0c),
    .width(5)
) const_12_5 (
    .out(const_12_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0d),
    .width(5)
) const_13_5 (
    .out(const_13_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0e),
    .width(5)
) const_14_5 (
    .out(const_14_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0f),
    .width(5)
) const_15_5 (
    .out(const_15_5_out)
);
PEGEN_coreir_const #(
    .value(5'h10),
    .width(5)
) const_16_5 (
    .out(const_16_5_out)
);
PEGEN_coreir_const #(
    .value(5'h11),
    .width(5)
) const_17_5 (
    .out(const_17_5_out)
);
PEGEN_coreir_const #(
    .value(5'h12),
    .width(5)
) const_18_5 (
    .out(const_18_5_out)
);
PEGEN_coreir_const #(
    .value(5'h01),
    .width(5)
) const_1_5 (
    .out(const_1_5_out)
);
PEGEN_coreir_const #(
    .value(5'h02),
    .width(5)
) const_2_5 (
    .out(const_2_5_out)
);
PEGEN_coreir_const #(
    .value(5'h03),
    .width(5)
) const_3_5 (
    .out(const_3_5_out)
);
PEGEN_coreir_const #(
    .value(5'h04),
    .width(5)
) const_4_5 (
    .out(const_4_5_out)
);
PEGEN_coreir_const #(
    .value(5'h05),
    .width(5)
) const_5_5 (
    .out(const_5_5_out)
);
PEGEN_coreir_const #(
    .value(5'h06),
    .width(5)
) const_6_5 (
    .out(const_6_5_out)
);
PEGEN_coreir_const #(
    .value(5'h07),
    .width(5)
) const_7_5 (
    .out(const_7_5_out)
);
PEGEN_coreir_const #(
    .value(5'h08),
    .width(5)
) const_8_5 (
    .out(const_8_5_out)
);
PEGEN_coreir_const #(
    .value(5'h09),
    .width(5)
) const_9_5 (
    .out(const_9_5_out)
);
PEGEN_corebit_and magma_Bit_and_inst0 (
    .in0(C),
    .in1(magma_Bit_not_inst4_out),
    .out(magma_Bit_and_inst0_out)
);
PEGEN_corebit_and magma_Bit_and_inst1 (
    .in0(magma_Bit_not_inst7_out),
    .in1(magma_Bit_not_inst8_out),
    .out(magma_Bit_and_inst1_out)
);
PEGEN_corebit_and magma_Bit_and_inst2 (
    .in0(magma_Bit_not_inst10_out),
    .in1(magma_Bit_not_inst11_out),
    .out(magma_Bit_and_inst2_out)
);
PEGEN_corebit_and magma_Bit_and_inst3 (
    .in0(N),
    .in1(magma_Bit_not_inst12_out),
    .out(magma_Bit_and_inst3_out)
);
PEGEN_corebit_not magma_Bit_not_inst0 (
    .in(Z),
    .out(magma_Bit_not_inst0_out)
);
PEGEN_corebit_not magma_Bit_not_inst1 (
    .in(C),
    .out(magma_Bit_not_inst1_out)
);
PEGEN_corebit_not magma_Bit_not_inst10 (
    .in(N),
    .out(magma_Bit_not_inst10_out)
);
PEGEN_corebit_not magma_Bit_not_inst11 (
    .in(Z),
    .out(magma_Bit_not_inst11_out)
);
PEGEN_corebit_not magma_Bit_not_inst12 (
    .in(Z),
    .out(magma_Bit_not_inst12_out)
);
PEGEN_corebit_not magma_Bit_not_inst2 (
    .in(N),
    .out(magma_Bit_not_inst2_out)
);
PEGEN_corebit_not magma_Bit_not_inst3 (
    .in(V),
    .out(magma_Bit_not_inst3_out)
);
PEGEN_corebit_not magma_Bit_not_inst4 (
    .in(Z),
    .out(magma_Bit_not_inst4_out)
);
PEGEN_corebit_not magma_Bit_not_inst5 (
    .in(C),
    .out(magma_Bit_not_inst5_out)
);
PEGEN_corebit_not magma_Bit_not_inst6 (
    .in(magma_Bit_xor_inst0_out),
    .out(magma_Bit_not_inst6_out)
);
PEGEN_corebit_not magma_Bit_not_inst7 (
    .in(Z),
    .out(magma_Bit_not_inst7_out)
);
PEGEN_corebit_not magma_Bit_not_inst8 (
    .in(magma_Bit_xor_inst2_out),
    .out(magma_Bit_not_inst8_out)
);
PEGEN_corebit_not magma_Bit_not_inst9 (
    .in(N),
    .out(magma_Bit_not_inst9_out)
);
PEGEN_corebit_or magma_Bit_or_inst0 (
    .in0(magma_Bits_5_eq_inst2_out),
    .in1(magma_Bits_5_eq_inst3_out),
    .out(magma_Bit_or_inst0_out)
);
PEGEN_corebit_or magma_Bit_or_inst1 (
    .in0(magma_Bits_5_eq_inst4_out),
    .in1(magma_Bits_5_eq_inst5_out),
    .out(magma_Bit_or_inst1_out)
);
PEGEN_corebit_or magma_Bit_or_inst2 (
    .in0(magma_Bit_not_inst5_out),
    .in1(Z),
    .out(magma_Bit_or_inst2_out)
);
PEGEN_corebit_or magma_Bit_or_inst3 (
    .in0(Z),
    .in1(magma_Bit_xor_inst3_out),
    .out(magma_Bit_or_inst3_out)
);
PEGEN_corebit_or magma_Bit_or_inst4 (
    .in0(magma_Bit_not_inst9_out),
    .in1(Z),
    .out(magma_Bit_or_inst4_out)
);
PEGEN_corebit_or magma_Bit_or_inst5 (
    .in0(N),
    .in1(Z),
    .out(magma_Bit_or_inst5_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst0 (
    .in0(N),
    .in1(V),
    .out(magma_Bit_xor_inst0_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst1 (
    .in0(N),
    .in1(V),
    .out(magma_Bit_xor_inst1_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst2 (
    .in0(N),
    .in1(V),
    .out(magma_Bit_xor_inst2_out)
);
PEGEN_corebit_xor magma_Bit_xor_inst3 (
    .in0(N),
    .in1(V),
    .out(magma_Bit_xor_inst3_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst0 (
    .in0(code),
    .in1(const_0_5_out),
    .out(magma_Bits_5_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst1 (
    .in0(code),
    .in1(const_1_5_out),
    .out(magma_Bits_5_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst10 (
    .in0(code),
    .in1(const_8_5_out),
    .out(magma_Bits_5_eq_inst10_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst11 (
    .in0(code),
    .in1(const_9_5_out),
    .out(magma_Bits_5_eq_inst11_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst12 (
    .in0(code),
    .in1(const_10_5_out),
    .out(magma_Bits_5_eq_inst12_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst13 (
    .in0(code),
    .in1(const_11_5_out),
    .out(magma_Bits_5_eq_inst13_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst14 (
    .in0(code),
    .in1(const_12_5_out),
    .out(magma_Bits_5_eq_inst14_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst15 (
    .in0(code),
    .in1(const_13_5_out),
    .out(magma_Bits_5_eq_inst15_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst16 (
    .in0(code),
    .in1(const_15_5_out),
    .out(magma_Bits_5_eq_inst16_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst17 (
    .in0(code),
    .in1(const_14_5_out),
    .out(magma_Bits_5_eq_inst17_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst18 (
    .in0(code),
    .in1(const_16_5_out),
    .out(magma_Bits_5_eq_inst18_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst19 (
    .in0(code),
    .in1(const_17_5_out),
    .out(magma_Bits_5_eq_inst19_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst2 (
    .in0(code),
    .in1(const_2_5_out),
    .out(magma_Bits_5_eq_inst2_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst20 (
    .in0(code),
    .in1(const_18_5_out),
    .out(magma_Bits_5_eq_inst20_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst3 (
    .in0(code),
    .in1(const_2_5_out),
    .out(magma_Bits_5_eq_inst3_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst4 (
    .in0(code),
    .in1(const_3_5_out),
    .out(magma_Bits_5_eq_inst4_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst5 (
    .in0(code),
    .in1(const_3_5_out),
    .out(magma_Bits_5_eq_inst5_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst6 (
    .in0(code),
    .in1(const_4_5_out),
    .out(magma_Bits_5_eq_inst6_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst7 (
    .in0(code),
    .in1(const_5_5_out),
    .out(magma_Bits_5_eq_inst7_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst8 (
    .in0(code),
    .in1(const_6_5_out),
    .out(magma_Bits_5_eq_inst8_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst9 (
    .in0(code),
    .in1(const_7_5_out),
    .out(magma_Bits_5_eq_inst9_out)
);
assign O = Mux2xBit_inst18_O;
endmodule

module PEGEN_ALU (
    input [4:0] alu,
    input [0:0] signed_,
    input [15:0] a,
    input [15:0] b,
    input [15:0] c,
    input d,
    output [15:0] res,
    output res_p,
    output Z,
    output N,
    output C,
    output V,
    input CLK,
    input ASYNCRESET
);
wire Mux2xBit_inst0_O;
wire Mux2xBit_inst1_O;
wire Mux2xBit_inst10_O;
wire Mux2xBit_inst11_O;
wire Mux2xBit_inst12_O;
wire Mux2xBit_inst13_O;
wire Mux2xBit_inst14_O;
wire Mux2xBit_inst15_O;
wire Mux2xBit_inst16_O;
wire Mux2xBit_inst17_O;
wire Mux2xBit_inst18_O;
wire Mux2xBit_inst19_O;
wire Mux2xBit_inst2_O;
wire Mux2xBit_inst20_O;
wire Mux2xBit_inst21_O;
wire Mux2xBit_inst22_O;
wire Mux2xBit_inst23_O;
wire Mux2xBit_inst24_O;
wire Mux2xBit_inst25_O;
wire Mux2xBit_inst26_O;
wire Mux2xBit_inst27_O;
wire Mux2xBit_inst28_O;
wire Mux2xBit_inst29_O;
wire Mux2xBit_inst3_O;
wire Mux2xBit_inst30_O;
wire Mux2xBit_inst4_O;
wire Mux2xBit_inst5_O;
wire Mux2xBit_inst6_O;
wire Mux2xBit_inst7_O;
wire Mux2xBit_inst8_O;
wire Mux2xBit_inst9_O;
wire [15:0] Mux2xBits16_inst0_O;
wire [15:0] Mux2xBits16_inst1_O;
wire [15:0] Mux2xBits16_inst10_O;
wire [15:0] Mux2xBits16_inst11_O;
wire [15:0] Mux2xBits16_inst12_O;
wire [15:0] Mux2xBits16_inst13_O;
wire [15:0] Mux2xBits16_inst14_O;
wire [15:0] Mux2xBits16_inst15_O;
wire [15:0] Mux2xBits16_inst16_O;
wire [15:0] Mux2xBits16_inst17_O;
wire [15:0] Mux2xBits16_inst18_O;
wire [15:0] Mux2xBits16_inst19_O;
wire [15:0] Mux2xBits16_inst2_O;
wire [15:0] Mux2xBits16_inst20_O;
wire [15:0] Mux2xBits16_inst21_O;
wire [15:0] Mux2xBits16_inst22_O;
wire [15:0] Mux2xBits16_inst23_O;
wire [15:0] Mux2xBits16_inst24_O;
wire [15:0] Mux2xBits16_inst3_O;
wire [15:0] Mux2xBits16_inst4_O;
wire [15:0] Mux2xBits16_inst5_O;
wire [15:0] Mux2xBits16_inst6_O;
wire [15:0] Mux2xBits16_inst7_O;
wire [15:0] Mux2xBits16_inst8_O;
wire [15:0] Mux2xBits16_inst9_O;
wire [15:0] Mux2xUInt16_inst0_O;
wire [31:0] Mux2xUInt32_inst0_O;
wire [31:0] Mux2xUInt32_inst1_O;
wire bit_const_0_None_out;
wire bit_const_1_None_out;
wire [15:0] const_0_16_out;
wire [4:0] const_0_5_out;
wire [4:0] const_11_5_out;
wire [4:0] const_12_5_out;
wire [4:0] const_13_5_out;
wire [4:0] const_15_5_out;
wire [4:0] const_17_5_out;
wire [4:0] const_18_5_out;
wire [4:0] const_19_5_out;
wire [0:0] const_1_1_out;
wire [4:0] const_1_5_out;
wire [4:0] const_20_5_out;
wire [15:0] const_21845_16_out;
wire [4:0] const_21_5_out;
wire [4:0] const_22_5_out;
wire [4:0] const_23_5_out;
wire [4:0] const_24_5_out;
wire [4:0] const_25_5_out;
wire [4:0] const_26_5_out;
wire [4:0] const_27_5_out;
wire [4:0] const_28_5_out;
wire [4:0] const_2_5_out;
wire [4:0] const_3_5_out;
wire [4:0] const_4_5_out;
wire [4:0] const_5_5_out;
wire [4:0] const_6_5_out;
wire [4:0] const_8_5_out;
wire magma_Bit_and_inst0_out;
wire magma_Bit_and_inst1_out;
wire magma_Bit_and_inst2_out;
wire magma_Bit_and_inst3_out;
wire magma_Bit_not_inst0_out;
wire magma_Bit_not_inst1_out;
wire magma_Bit_not_inst2_out;
wire magma_Bit_or_inst0_out;
wire magma_Bit_or_inst1_out;
wire magma_Bit_or_inst10_out;
wire magma_Bit_or_inst11_out;
wire magma_Bit_or_inst12_out;
wire magma_Bit_or_inst13_out;
wire magma_Bit_or_inst14_out;
wire magma_Bit_or_inst15_out;
wire magma_Bit_or_inst16_out;
wire magma_Bit_or_inst17_out;
wire magma_Bit_or_inst18_out;
wire magma_Bit_or_inst19_out;
wire magma_Bit_or_inst2_out;
wire magma_Bit_or_inst3_out;
wire magma_Bit_or_inst4_out;
wire magma_Bit_or_inst5_out;
wire magma_Bit_or_inst6_out;
wire magma_Bit_or_inst7_out;
wire magma_Bit_or_inst8_out;
wire magma_Bit_or_inst9_out;
wire [15:0] magma_Bits_16_and_inst0_out;
wire [15:0] magma_Bits_16_not_inst0_out;
wire [15:0] magma_Bits_16_not_inst1_out;
wire [15:0] magma_Bits_16_or_inst0_out;
wire [15:0] magma_Bits_16_shl_inst0_out;
wire [15:0] magma_Bits_16_xor_inst0_out;
wire magma_Bits_1_eq_inst0_out;
wire magma_Bits_1_eq_inst1_out;
wire magma_Bits_1_eq_inst2_out;
wire magma_Bits_5_eq_inst0_out;
wire magma_Bits_5_eq_inst1_out;
wire magma_Bits_5_eq_inst10_out;
wire magma_Bits_5_eq_inst11_out;
wire magma_Bits_5_eq_inst12_out;
wire magma_Bits_5_eq_inst13_out;
wire magma_Bits_5_eq_inst14_out;
wire magma_Bits_5_eq_inst15_out;
wire magma_Bits_5_eq_inst16_out;
wire magma_Bits_5_eq_inst17_out;
wire magma_Bits_5_eq_inst18_out;
wire magma_Bits_5_eq_inst19_out;
wire magma_Bits_5_eq_inst2_out;
wire magma_Bits_5_eq_inst20_out;
wire magma_Bits_5_eq_inst21_out;
wire magma_Bits_5_eq_inst22_out;
wire magma_Bits_5_eq_inst23_out;
wire magma_Bits_5_eq_inst24_out;
wire magma_Bits_5_eq_inst25_out;
wire magma_Bits_5_eq_inst26_out;
wire magma_Bits_5_eq_inst27_out;
wire magma_Bits_5_eq_inst28_out;
wire magma_Bits_5_eq_inst29_out;
wire magma_Bits_5_eq_inst3_out;
wire magma_Bits_5_eq_inst30_out;
wire magma_Bits_5_eq_inst31_out;
wire magma_Bits_5_eq_inst32_out;
wire magma_Bits_5_eq_inst33_out;
wire magma_Bits_5_eq_inst34_out;
wire magma_Bits_5_eq_inst35_out;
wire magma_Bits_5_eq_inst36_out;
wire magma_Bits_5_eq_inst37_out;
wire magma_Bits_5_eq_inst38_out;
wire magma_Bits_5_eq_inst39_out;
wire magma_Bits_5_eq_inst4_out;
wire magma_Bits_5_eq_inst5_out;
wire magma_Bits_5_eq_inst6_out;
wire magma_Bits_5_eq_inst7_out;
wire magma_Bits_5_eq_inst8_out;
wire magma_Bits_5_eq_inst9_out;
wire [15:0] magma_SInt_16_ashr_inst0_out;
wire [15:0] magma_SInt_16_ashr_inst1_out;
wire magma_SInt_16_eq_inst0_out;
wire [15:0] magma_SInt_16_neg_inst0_out;
wire magma_SInt_16_sge_inst0_out;
wire magma_SInt_16_sge_inst1_out;
wire magma_SInt_16_sle_inst0_out;
wire magma_SInt_16_sle_inst1_out;
wire [15:0] magma_UInt_16_lshr_inst0_out;
wire [15:0] magma_UInt_16_lshr_inst1_out;
wire magma_UInt_16_uge_inst0_out;
wire magma_UInt_16_uge_inst1_out;
wire magma_UInt_16_ule_inst0_out;
wire [16:0] magma_UInt_17_add_inst0_out;
wire [16:0] magma_UInt_17_add_inst1_out;
wire [16:0] magma_UInt_17_add_inst2_out;
wire [16:0] magma_UInt_17_add_inst3_out;
wire [31:0] magma_UInt_32_mul_inst0_out;
PEGEN_Mux2xBit Mux2xBit_inst0 (
    .I0(bit_const_1_None_out),
    .I1(magma_SInt_16_sle_inst1_out),
    .S(magma_Bits_1_eq_inst0_out),
    .O(Mux2xBit_inst0_O)
);
PEGEN_Mux2xBit Mux2xBit_inst1 (
    .I0(magma_UInt_16_uge_inst0_out),
    .I1(magma_SInt_16_sge_inst0_out),
    .S(magma_Bits_1_eq_inst0_out),
    .O(Mux2xBit_inst1_O)
);
PEGEN_Mux2xBit Mux2xBit_inst10 (
    .I0(Mux2xBit_inst9_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst31_out),
    .O(Mux2xBit_inst10_O)
);
PEGEN_Mux2xBit Mux2xBit_inst11 (
    .I0(Mux2xBit_inst10_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst30_out),
    .O(Mux2xBit_inst11_O)
);
PEGEN_Mux2xBit Mux2xBit_inst12 (
    .I0(Mux2xBit_inst11_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst29_out),
    .O(Mux2xBit_inst12_O)
);
PEGEN_Mux2xBit Mux2xBit_inst13 (
    .I0(Mux2xBit_inst12_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst28_out),
    .O(Mux2xBit_inst13_O)
);
PEGEN_Mux2xBit Mux2xBit_inst14 (
    .I0(Mux2xBit_inst13_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst27_out),
    .O(Mux2xBit_inst14_O)
);
PEGEN_Mux2xBit Mux2xBit_inst15 (
    .I0(Mux2xBit_inst14_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst26_out),
    .O(Mux2xBit_inst15_O)
);
PEGEN_Mux2xBit Mux2xBit_inst16 (
    .I0(Mux2xBit_inst15_O),
    .I1(a[15]),
    .S(magma_Bits_5_eq_inst25_out),
    .O(Mux2xBit_inst16_O)
);
PEGEN_Mux2xBit Mux2xBit_inst17 (
    .I0(Mux2xBit_inst16_O),
    .I1(Mux2xBit_inst2_O),
    .S(magma_Bits_5_eq_inst24_out),
    .O(Mux2xBit_inst17_O)
);
PEGEN_Mux2xBit Mux2xBit_inst18 (
    .I0(Mux2xBit_inst17_O),
    .I1(Mux2xBit_inst1_O),
    .S(magma_Bits_5_eq_inst23_out),
    .O(Mux2xBit_inst18_O)
);
PEGEN_Mux2xBit Mux2xBit_inst19 (
    .I0(bit_const_0_None_out),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst22_out),
    .O(Mux2xBit_inst19_O)
);
PEGEN_Mux2xBit Mux2xBit_inst2 (
    .I0(magma_UInt_16_ule_inst0_out),
    .I1(magma_SInt_16_sle_inst0_out),
    .S(magma_Bits_1_eq_inst0_out),
    .O(Mux2xBit_inst2_O)
);
PEGEN_Mux2xBit Mux2xBit_inst20 (
    .I0(bit_const_0_None_out),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst22_out),
    .O(Mux2xBit_inst20_O)
);
PEGEN_Mux2xBit Mux2xBit_inst21 (
    .I0(Mux2xBit_inst18_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst22_out),
    .O(Mux2xBit_inst21_O)
);
PEGEN_Mux2xBit Mux2xBit_inst22 (
    .I0(Mux2xBit_inst19_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst21_out),
    .O(Mux2xBit_inst22_O)
);
PEGEN_Mux2xBit Mux2xBit_inst23 (
    .I0(Mux2xBit_inst20_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst21_out),
    .O(Mux2xBit_inst23_O)
);
PEGEN_Mux2xBit Mux2xBit_inst24 (
    .I0(Mux2xBit_inst21_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst21_out),
    .O(Mux2xBit_inst24_O)
);
PEGEN_Mux2xBit Mux2xBit_inst25 (
    .I0(Mux2xBit_inst22_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst20_out),
    .O(Mux2xBit_inst25_O)
);
PEGEN_Mux2xBit Mux2xBit_inst26 (
    .I0(Mux2xBit_inst23_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst20_out),
    .O(Mux2xBit_inst26_O)
);
PEGEN_Mux2xBit Mux2xBit_inst27 (
    .I0(Mux2xBit_inst24_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst20_out),
    .O(Mux2xBit_inst27_O)
);
PEGEN_Mux2xBit Mux2xBit_inst28 (
    .I0(Mux2xBit_inst25_O),
    .I1(magma_UInt_17_add_inst1_out[16]),
    .S(magma_Bit_or_inst13_out),
    .O(Mux2xBit_inst28_O)
);
PEGEN_Mux2xBit Mux2xBit_inst29 (
    .I0(Mux2xBit_inst26_O),
    .I1(magma_Bit_or_inst14_out),
    .S(magma_Bit_or_inst13_out),
    .O(Mux2xBit_inst29_O)
);
PEGEN_Mux2xBit Mux2xBit_inst3 (
    .I0(magma_UInt_16_uge_inst1_out),
    .I1(magma_SInt_16_sge_inst1_out),
    .S(magma_Bits_1_eq_inst1_out),
    .O(Mux2xBit_inst3_O)
);
PEGEN_Mux2xBit Mux2xBit_inst30 (
    .I0(Mux2xBit_inst27_O),
    .I1(magma_UInt_17_add_inst1_out[16]),
    .S(magma_Bit_or_inst13_out),
    .O(Mux2xBit_inst30_O)
);
PEGEN_Mux2xBit Mux2xBit_inst4 (
    .I0(bit_const_0_None_out),
    .I1(d),
    .S(magma_Bit_or_inst5_out),
    .O(Mux2xBit_inst4_O)
);
PEGEN_Mux2xBit Mux2xBit_inst5 (
    .I0(Mux2xBit_inst4_O),
    .I1(bit_const_1_None_out),
    .S(magma_Bit_or_inst4_out),
    .O(Mux2xBit_inst5_O)
);
PEGEN_Mux2xBit Mux2xBit_inst6 (
    .I0(bit_const_0_None_out),
    .I1(bit_const_1_None_out),
    .S(magma_Bit_or_inst10_out),
    .O(Mux2xBit_inst6_O)
);
PEGEN_Mux2xBit Mux2xBit_inst7 (
    .I0(bit_const_0_None_out),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst39_out),
    .O(Mux2xBit_inst7_O)
);
PEGEN_Mux2xBit Mux2xBit_inst8 (
    .I0(Mux2xBit_inst7_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_5_eq_inst38_out),
    .O(Mux2xBit_inst8_O)
);
PEGEN_Mux2xBit Mux2xBit_inst9 (
    .I0(Mux2xBit_inst8_O),
    .I1(bit_const_0_None_out),
    .S(magma_Bit_or_inst19_out),
    .O(Mux2xBit_inst9_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst0 (
    .I0(magma_UInt_16_lshr_inst0_out),
    .I1(magma_SInt_16_ashr_inst0_out),
    .S(magma_Bits_1_eq_inst0_out),
    .O(Mux2xBits16_inst0_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst1 (
    .I0(b),
    .I1(a),
    .S(Mux2xBit_inst1_O),
    .O(Mux2xBits16_inst1_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst10 (
    .I0(Mux2xBits16_inst9_O),
    .I1(Mux2xBits16_inst3_O),
    .S(magma_Bits_5_eq_inst38_out),
    .O(Mux2xBits16_inst10_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst11 (
    .I0(Mux2xBits16_inst10_O),
    .I1(magma_UInt_17_add_inst3_out[15:0]),
    .S(magma_Bit_or_inst19_out),
    .O(Mux2xBits16_inst11_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst12 (
    .I0(Mux2xBits16_inst11_O),
    .I1(magma_Bits_16_shl_inst0_out),
    .S(magma_Bits_5_eq_inst31_out),
    .O(Mux2xBits16_inst12_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst13 (
    .I0(Mux2xBits16_inst12_O),
    .I1(Mux2xBits16_inst0_O),
    .S(magma_Bits_5_eq_inst30_out),
    .O(Mux2xBits16_inst13_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst14 (
    .I0(Mux2xBits16_inst13_O),
    .I1(magma_Bits_16_xor_inst0_out),
    .S(magma_Bits_5_eq_inst29_out),
    .O(Mux2xBits16_inst14_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst15 (
    .I0(Mux2xBits16_inst14_O),
    .I1(magma_Bits_16_or_inst0_out),
    .S(magma_Bits_5_eq_inst28_out),
    .O(Mux2xBits16_inst15_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst16 (
    .I0(Mux2xBits16_inst15_O),
    .I1(magma_Bits_16_and_inst0_out),
    .S(magma_Bits_5_eq_inst27_out),
    .O(Mux2xBits16_inst16_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst17 (
    .I0(Mux2xBits16_inst16_O),
    .I1(Mux2xBits16_inst8_O),
    .S(magma_Bits_5_eq_inst26_out),
    .O(Mux2xBits16_inst17_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst18 (
    .I0(Mux2xBits16_inst17_O),
    .I1(Mux2xBits16_inst7_O),
    .S(magma_Bits_5_eq_inst25_out),
    .O(Mux2xBits16_inst18_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst19 (
    .I0(Mux2xBits16_inst18_O),
    .I1(Mux2xBits16_inst2_O),
    .S(magma_Bits_5_eq_inst24_out),
    .O(Mux2xBits16_inst19_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst2 (
    .I0(b),
    .I1(a),
    .S(Mux2xBit_inst2_O),
    .O(Mux2xBits16_inst2_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst20 (
    .I0(Mux2xBits16_inst19_O),
    .I1(Mux2xBits16_inst1_O),
    .S(magma_Bits_5_eq_inst23_out),
    .O(Mux2xBits16_inst20_O)
);
wire [15:0] Mux2xBits16_inst21_I1;
assign Mux2xBits16_inst21_I1 = {magma_UInt_32_mul_inst0_out[31],magma_UInt_32_mul_inst0_out[30],magma_UInt_32_mul_inst0_out[29],magma_UInt_32_mul_inst0_out[28],magma_UInt_32_mul_inst0_out[27],magma_UInt_32_mul_inst0_out[26],magma_UInt_32_mul_inst0_out[25],magma_UInt_32_mul_inst0_out[24],magma_UInt_32_mul_inst0_out[23],magma_UInt_32_mul_inst0_out[22],magma_UInt_32_mul_inst0_out[21],magma_UInt_32_mul_inst0_out[20],magma_UInt_32_mul_inst0_out[19],magma_UInt_32_mul_inst0_out[18],magma_UInt_32_mul_inst0_out[17],magma_UInt_32_mul_inst0_out[16]};
PEGEN_Mux2xBits16 Mux2xBits16_inst21 (
    .I0(Mux2xBits16_inst20_O),
    .I1(Mux2xBits16_inst21_I1),
    .S(magma_Bits_5_eq_inst22_out),
    .O(Mux2xBits16_inst21_O)
);
wire [15:0] Mux2xBits16_inst22_I1;
assign Mux2xBits16_inst22_I1 = {magma_UInt_32_mul_inst0_out[23],magma_UInt_32_mul_inst0_out[22],magma_UInt_32_mul_inst0_out[21],magma_UInt_32_mul_inst0_out[20],magma_UInt_32_mul_inst0_out[19],magma_UInt_32_mul_inst0_out[18],magma_UInt_32_mul_inst0_out[17],magma_UInt_32_mul_inst0_out[16],magma_UInt_32_mul_inst0_out[15],magma_UInt_32_mul_inst0_out[14],magma_UInt_32_mul_inst0_out[13],magma_UInt_32_mul_inst0_out[12],magma_UInt_32_mul_inst0_out[11],magma_UInt_32_mul_inst0_out[10],magma_UInt_32_mul_inst0_out[9],magma_UInt_32_mul_inst0_out[8]};
PEGEN_Mux2xBits16 Mux2xBits16_inst22 (
    .I0(Mux2xBits16_inst21_O),
    .I1(Mux2xBits16_inst22_I1),
    .S(magma_Bits_5_eq_inst21_out),
    .O(Mux2xBits16_inst22_O)
);
wire [15:0] Mux2xBits16_inst23_I1;
assign Mux2xBits16_inst23_I1 = {magma_UInt_32_mul_inst0_out[15],magma_UInt_32_mul_inst0_out[14],magma_UInt_32_mul_inst0_out[13],magma_UInt_32_mul_inst0_out[12],magma_UInt_32_mul_inst0_out[11],magma_UInt_32_mul_inst0_out[10],magma_UInt_32_mul_inst0_out[9],magma_UInt_32_mul_inst0_out[8],magma_UInt_32_mul_inst0_out[7],magma_UInt_32_mul_inst0_out[6],magma_UInt_32_mul_inst0_out[5],magma_UInt_32_mul_inst0_out[4],magma_UInt_32_mul_inst0_out[3],magma_UInt_32_mul_inst0_out[2],magma_UInt_32_mul_inst0_out[1],magma_UInt_32_mul_inst0_out[0]};
PEGEN_Mux2xBits16 Mux2xBits16_inst23 (
    .I0(Mux2xBits16_inst22_O),
    .I1(Mux2xBits16_inst23_I1),
    .S(magma_Bits_5_eq_inst20_out),
    .O(Mux2xBits16_inst23_O)
);
wire [15:0] Mux2xBits16_inst24_I1;
assign Mux2xBits16_inst24_I1 = {magma_UInt_17_add_inst1_out[15],magma_UInt_17_add_inst1_out[14],magma_UInt_17_add_inst1_out[13],magma_UInt_17_add_inst1_out[12],magma_UInt_17_add_inst1_out[11],magma_UInt_17_add_inst1_out[10],magma_UInt_17_add_inst1_out[9],magma_UInt_17_add_inst1_out[8],magma_UInt_17_add_inst1_out[7],magma_UInt_17_add_inst1_out[6],magma_UInt_17_add_inst1_out[5],magma_UInt_17_add_inst1_out[4],magma_UInt_17_add_inst1_out[3],magma_UInt_17_add_inst1_out[2],magma_UInt_17_add_inst1_out[1],magma_UInt_17_add_inst1_out[0]};
PEGEN_Mux2xBits16 Mux2xBits16_inst24 (
    .I0(Mux2xBits16_inst23_O),
    .I1(Mux2xBits16_inst24_I1),
    .S(magma_Bit_or_inst13_out),
    .O(Mux2xBits16_inst24_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst3 (
    .I0(c),
    .I1(Mux2xBits16_inst2_O),
    .S(Mux2xBit_inst3_O),
    .O(Mux2xBits16_inst3_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst4 (
    .I0(b),
    .I1(magma_Bits_16_not_inst0_out),
    .S(magma_Bit_or_inst2_out),
    .O(Mux2xBits16_inst4_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst5 (
    .I0(c),
    .I1(magma_Bits_16_not_inst1_out),
    .S(magma_Bit_or_inst10_out),
    .O(Mux2xBits16_inst5_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst6 (
    .I0(magma_UInt_16_lshr_inst1_out),
    .I1(magma_SInt_16_ashr_inst1_out),
    .S(magma_Bits_1_eq_inst2_out),
    .O(Mux2xBits16_inst6_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst7 (
    .I0(magma_SInt_16_neg_inst0_out),
    .I1(a),
    .S(Mux2xBit_inst0_O),
    .O(Mux2xBits16_inst7_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst8 (
    .I0(Mux2xBits16_inst4_O),
    .I1(a),
    .S(d),
    .O(Mux2xBits16_inst8_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst9 (
    .I0(const_21845_16_out),
    .I1(Mux2xBits16_inst6_O),
    .S(magma_Bits_5_eq_inst39_out),
    .O(Mux2xBits16_inst9_O)
);
wire [15:0] Mux2xUInt16_inst0_I0;
assign Mux2xUInt16_inst0_I0 = {magma_UInt_32_mul_inst0_out[15],magma_UInt_32_mul_inst0_out[14],magma_UInt_32_mul_inst0_out[13],magma_UInt_32_mul_inst0_out[12],magma_UInt_32_mul_inst0_out[11],magma_UInt_32_mul_inst0_out[10],magma_UInt_32_mul_inst0_out[9],magma_UInt_32_mul_inst0_out[8],magma_UInt_32_mul_inst0_out[7],magma_UInt_32_mul_inst0_out[6],magma_UInt_32_mul_inst0_out[5],magma_UInt_32_mul_inst0_out[4],magma_UInt_32_mul_inst0_out[3],magma_UInt_32_mul_inst0_out[2],magma_UInt_32_mul_inst0_out[1],magma_UInt_32_mul_inst0_out[0]};
wire [15:0] Mux2xUInt16_inst0_I1;
assign Mux2xUInt16_inst0_I1 = {magma_UInt_17_add_inst1_out[15],magma_UInt_17_add_inst1_out[14],magma_UInt_17_add_inst1_out[13],magma_UInt_17_add_inst1_out[12],magma_UInt_17_add_inst1_out[11],magma_UInt_17_add_inst1_out[10],magma_UInt_17_add_inst1_out[9],magma_UInt_17_add_inst1_out[8],magma_UInt_17_add_inst1_out[7],magma_UInt_17_add_inst1_out[6],magma_UInt_17_add_inst1_out[5],magma_UInt_17_add_inst1_out[4],magma_UInt_17_add_inst1_out[3],magma_UInt_17_add_inst1_out[2],magma_UInt_17_add_inst1_out[1],magma_UInt_17_add_inst1_out[0]};
PEGEN_Mux2xUInt16 Mux2xUInt16_inst0 (
    .I0(Mux2xUInt16_inst0_I0),
    .I1(Mux2xUInt16_inst0_I1),
    .S(magma_Bit_or_inst8_out),
    .O(Mux2xUInt16_inst0_O)
);
wire [31:0] Mux2xUInt32_inst0_I0;
assign Mux2xUInt32_inst0_I0 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,a};
wire [31:0] Mux2xUInt32_inst0_I1;
assign Mux2xUInt32_inst0_I1 = {a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a[15],a};
PEGEN_Mux2xUInt32 Mux2xUInt32_inst0 (
    .I0(Mux2xUInt32_inst0_I0),
    .I1(Mux2xUInt32_inst0_I1),
    .S(magma_Bits_1_eq_inst0_out),
    .O(Mux2xUInt32_inst0_O)
);
wire [31:0] Mux2xUInt32_inst1_I0;
assign Mux2xUInt32_inst1_I0 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,b};
wire [31:0] Mux2xUInt32_inst1_I1;
assign Mux2xUInt32_inst1_I1 = {b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b[15],b};
PEGEN_Mux2xUInt32 Mux2xUInt32_inst1 (
    .I0(Mux2xUInt32_inst1_I0),
    .I1(Mux2xUInt32_inst1_I1),
    .S(magma_Bits_1_eq_inst0_out),
    .O(Mux2xUInt32_inst1_O)
);
PEGEN_corebit_const #(
    .value(1'b0)
) bit_const_0_None (
    .out(bit_const_0_None_out)
);
PEGEN_corebit_const #(
    .value(1'b1)
) bit_const_1_None (
    .out(bit_const_1_None_out)
);
PEGEN_coreir_const #(
    .value(16'h0000),
    .width(16)
) const_0_16 (
    .out(const_0_16_out)
);
PEGEN_coreir_const #(
    .value(5'h00),
    .width(5)
) const_0_5 (
    .out(const_0_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0b),
    .width(5)
) const_11_5 (
    .out(const_11_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0c),
    .width(5)
) const_12_5 (
    .out(const_12_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0d),
    .width(5)
) const_13_5 (
    .out(const_13_5_out)
);
PEGEN_coreir_const #(
    .value(5'h0f),
    .width(5)
) const_15_5 (
    .out(const_15_5_out)
);
PEGEN_coreir_const #(
    .value(5'h11),
    .width(5)
) const_17_5 (
    .out(const_17_5_out)
);
PEGEN_coreir_const #(
    .value(5'h12),
    .width(5)
) const_18_5 (
    .out(const_18_5_out)
);
PEGEN_coreir_const #(
    .value(5'h13),
    .width(5)
) const_19_5 (
    .out(const_19_5_out)
);
PEGEN_coreir_const #(
    .value(1'h1),
    .width(1)
) const_1_1 (
    .out(const_1_1_out)
);
PEGEN_coreir_const #(
    .value(5'h01),
    .width(5)
) const_1_5 (
    .out(const_1_5_out)
);
PEGEN_coreir_const #(
    .value(5'h14),
    .width(5)
) const_20_5 (
    .out(const_20_5_out)
);
PEGEN_coreir_const #(
    .value(16'h5555),
    .width(16)
) const_21845_16 (
    .out(const_21845_16_out)
);
PEGEN_coreir_const #(
    .value(5'h15),
    .width(5)
) const_21_5 (
    .out(const_21_5_out)
);
PEGEN_coreir_const #(
    .value(5'h16),
    .width(5)
) const_22_5 (
    .out(const_22_5_out)
);
PEGEN_coreir_const #(
    .value(5'h17),
    .width(5)
) const_23_5 (
    .out(const_23_5_out)
);
PEGEN_coreir_const #(
    .value(5'h18),
    .width(5)
) const_24_5 (
    .out(const_24_5_out)
);
PEGEN_coreir_const #(
    .value(5'h19),
    .width(5)
) const_25_5 (
    .out(const_25_5_out)
);
PEGEN_coreir_const #(
    .value(5'h1a),
    .width(5)
) const_26_5 (
    .out(const_26_5_out)
);
PEGEN_coreir_const #(
    .value(5'h1b),
    .width(5)
) const_27_5 (
    .out(const_27_5_out)
);
PEGEN_coreir_const #(
    .value(5'h1c),
    .width(5)
) const_28_5 (
    .out(const_28_5_out)
);
PEGEN_coreir_const #(
    .value(5'h02),
    .width(5)
) const_2_5 (
    .out(const_2_5_out)
);
PEGEN_coreir_const #(
    .value(5'h03),
    .width(5)
) const_3_5 (
    .out(const_3_5_out)
);
PEGEN_coreir_const #(
    .value(5'h04),
    .width(5)
) const_4_5 (
    .out(const_4_5_out)
);
PEGEN_coreir_const #(
    .value(5'h05),
    .width(5)
) const_5_5 (
    .out(const_5_5_out)
);
PEGEN_coreir_const #(
    .value(5'h06),
    .width(5)
) const_6_5 (
    .out(const_6_5_out)
);
PEGEN_coreir_const #(
    .value(5'h08),
    .width(5)
) const_8_5 (
    .out(const_8_5_out)
);
PEGEN_corebit_and magma_Bit_and_inst0 (
    .in0(a[15]),
    .in1(Mux2xBits16_inst4_O[15]),
    .out(magma_Bit_and_inst0_out)
);
PEGEN_corebit_and magma_Bit_and_inst1 (
    .in0(magma_Bit_and_inst0_out),
    .in1(magma_Bit_not_inst0_out),
    .out(magma_Bit_and_inst1_out)
);
PEGEN_corebit_and magma_Bit_and_inst2 (
    .in0(magma_Bit_not_inst1_out),
    .in1(magma_Bit_not_inst2_out),
    .out(magma_Bit_and_inst2_out)
);
PEGEN_corebit_and magma_Bit_and_inst3 (
    .in0(magma_Bit_and_inst2_out),
    .in1(magma_UInt_17_add_inst1_out[15]),
    .out(magma_Bit_and_inst3_out)
);
PEGEN_corebit_not magma_Bit_not_inst0 (
    .in(magma_UInt_17_add_inst1_out[15]),
    .out(magma_Bit_not_inst0_out)
);
PEGEN_corebit_not magma_Bit_not_inst1 (
    .in(a[15]),
    .out(magma_Bit_not_inst1_out)
);
PEGEN_corebit_not magma_Bit_not_inst2 (
    .in(Mux2xBits16_inst4_O[15]),
    .out(magma_Bit_not_inst2_out)
);
PEGEN_corebit_or magma_Bit_or_inst0 (
    .in0(magma_Bits_5_eq_inst0_out),
    .in1(magma_Bits_5_eq_inst1_out),
    .out(magma_Bit_or_inst0_out)
);
PEGEN_corebit_or magma_Bit_or_inst1 (
    .in0(magma_Bit_or_inst0_out),
    .in1(magma_Bits_5_eq_inst2_out),
    .out(magma_Bit_or_inst1_out)
);
PEGEN_corebit_or magma_Bit_or_inst10 (
    .in0(magma_Bit_or_inst9_out),
    .in1(magma_Bits_5_eq_inst15_out),
    .out(magma_Bit_or_inst10_out)
);
PEGEN_corebit_or magma_Bit_or_inst11 (
    .in0(magma_Bits_5_eq_inst16_out),
    .in1(magma_Bits_5_eq_inst17_out),
    .out(magma_Bit_or_inst11_out)
);
PEGEN_corebit_or magma_Bit_or_inst12 (
    .in0(magma_Bit_or_inst11_out),
    .in1(magma_Bits_5_eq_inst18_out),
    .out(magma_Bit_or_inst12_out)
);
PEGEN_corebit_or magma_Bit_or_inst13 (
    .in0(magma_Bit_or_inst12_out),
    .in1(magma_Bits_5_eq_inst19_out),
    .out(magma_Bit_or_inst13_out)
);
PEGEN_corebit_or magma_Bit_or_inst14 (
    .in0(magma_Bit_and_inst1_out),
    .in1(magma_Bit_and_inst3_out),
    .out(magma_Bit_or_inst14_out)
);
PEGEN_corebit_or magma_Bit_or_inst15 (
    .in0(magma_Bits_5_eq_inst32_out),
    .in1(magma_Bits_5_eq_inst33_out),
    .out(magma_Bit_or_inst15_out)
);
PEGEN_corebit_or magma_Bit_or_inst16 (
    .in0(magma_Bit_or_inst15_out),
    .in1(magma_Bits_5_eq_inst34_out),
    .out(magma_Bit_or_inst16_out)
);
PEGEN_corebit_or magma_Bit_or_inst17 (
    .in0(magma_Bit_or_inst16_out),
    .in1(magma_Bits_5_eq_inst35_out),
    .out(magma_Bit_or_inst17_out)
);
PEGEN_corebit_or magma_Bit_or_inst18 (
    .in0(magma_Bit_or_inst17_out),
    .in1(magma_Bits_5_eq_inst36_out),
    .out(magma_Bit_or_inst18_out)
);
PEGEN_corebit_or magma_Bit_or_inst19 (
    .in0(magma_Bit_or_inst18_out),
    .in1(magma_Bits_5_eq_inst37_out),
    .out(magma_Bit_or_inst19_out)
);
PEGEN_corebit_or magma_Bit_or_inst2 (
    .in0(magma_Bit_or_inst1_out),
    .in1(magma_Bits_5_eq_inst3_out),
    .out(magma_Bit_or_inst2_out)
);
PEGEN_corebit_or magma_Bit_or_inst3 (
    .in0(magma_Bits_5_eq_inst4_out),
    .in1(magma_Bits_5_eq_inst5_out),
    .out(magma_Bit_or_inst3_out)
);
PEGEN_corebit_or magma_Bit_or_inst4 (
    .in0(magma_Bit_or_inst3_out),
    .in1(magma_Bits_5_eq_inst6_out),
    .out(magma_Bit_or_inst4_out)
);
PEGEN_corebit_or magma_Bit_or_inst5 (
    .in0(magma_Bits_5_eq_inst7_out),
    .in1(magma_Bits_5_eq_inst8_out),
    .out(magma_Bit_or_inst5_out)
);
PEGEN_corebit_or magma_Bit_or_inst6 (
    .in0(magma_Bits_5_eq_inst9_out),
    .in1(magma_Bits_5_eq_inst10_out),
    .out(magma_Bit_or_inst6_out)
);
PEGEN_corebit_or magma_Bit_or_inst7 (
    .in0(magma_Bit_or_inst6_out),
    .in1(magma_Bits_5_eq_inst11_out),
    .out(magma_Bit_or_inst7_out)
);
PEGEN_corebit_or magma_Bit_or_inst8 (
    .in0(magma_Bit_or_inst7_out),
    .in1(magma_Bits_5_eq_inst12_out),
    .out(magma_Bit_or_inst8_out)
);
PEGEN_corebit_or magma_Bit_or_inst9 (
    .in0(magma_Bits_5_eq_inst13_out),
    .in1(magma_Bits_5_eq_inst14_out),
    .out(magma_Bit_or_inst9_out)
);
PEGEN_coreir_and #(
    .width(16)
) magma_Bits_16_and_inst0 (
    .in0(a),
    .in1(Mux2xBits16_inst4_O),
    .out(magma_Bits_16_and_inst0_out)
);
PEGEN_coreir_not #(
    .width(16)
) magma_Bits_16_not_inst0 (
    .in(b),
    .out(magma_Bits_16_not_inst0_out)
);
PEGEN_coreir_not #(
    .width(16)
) magma_Bits_16_not_inst1 (
    .in(c),
    .out(magma_Bits_16_not_inst1_out)
);
PEGEN_coreir_or #(
    .width(16)
) magma_Bits_16_or_inst0 (
    .in0(a),
    .in1(Mux2xBits16_inst4_O),
    .out(magma_Bits_16_or_inst0_out)
);
PEGEN_coreir_shl #(
    .width(16)
) magma_Bits_16_shl_inst0 (
    .in0(a),
    .in1(Mux2xBits16_inst4_O),
    .out(magma_Bits_16_shl_inst0_out)
);
PEGEN_coreir_xor #(
    .width(16)
) magma_Bits_16_xor_inst0 (
    .in0(a),
    .in1(Mux2xBits16_inst4_O),
    .out(magma_Bits_16_xor_inst0_out)
);
PEGEN_coreir_eq #(
    .width(1)
) magma_Bits_1_eq_inst0 (
    .in0(signed_),
    .in1(const_1_1_out),
    .out(magma_Bits_1_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(1)
) magma_Bits_1_eq_inst1 (
    .in0(signed_),
    .in1(const_1_1_out),
    .out(magma_Bits_1_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(1)
) magma_Bits_1_eq_inst2 (
    .in0(signed_),
    .in1(const_1_1_out),
    .out(magma_Bits_1_eq_inst2_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst0 (
    .in0(alu),
    .in1(const_1_5_out),
    .out(magma_Bits_5_eq_inst0_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst1 (
    .in0(alu),
    .in1(const_6_5_out),
    .out(magma_Bits_5_eq_inst1_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst10 (
    .in0(alu),
    .in1(const_25_5_out),
    .out(magma_Bits_5_eq_inst10_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst11 (
    .in0(alu),
    .in1(const_26_5_out),
    .out(magma_Bits_5_eq_inst11_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst12 (
    .in0(alu),
    .in1(const_27_5_out),
    .out(magma_Bits_5_eq_inst12_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst13 (
    .in0(alu),
    .in1(const_22_5_out),
    .out(magma_Bits_5_eq_inst13_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst14 (
    .in0(alu),
    .in1(const_25_5_out),
    .out(magma_Bits_5_eq_inst14_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst15 (
    .in0(alu),
    .in1(const_27_5_out),
    .out(magma_Bits_5_eq_inst15_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst16 (
    .in0(alu),
    .in1(const_0_5_out),
    .out(magma_Bits_5_eq_inst16_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst17 (
    .in0(alu),
    .in1(const_1_5_out),
    .out(magma_Bits_5_eq_inst17_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst18 (
    .in0(alu),
    .in1(const_2_5_out),
    .out(magma_Bits_5_eq_inst18_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst19 (
    .in0(alu),
    .in1(const_6_5_out),
    .out(magma_Bits_5_eq_inst19_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst2 (
    .in0(alu),
    .in1(const_26_5_out),
    .out(magma_Bits_5_eq_inst2_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst20 (
    .in0(alu),
    .in1(const_11_5_out),
    .out(magma_Bits_5_eq_inst20_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst21 (
    .in0(alu),
    .in1(const_12_5_out),
    .out(magma_Bits_5_eq_inst21_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst22 (
    .in0(alu),
    .in1(const_13_5_out),
    .out(magma_Bits_5_eq_inst22_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst23 (
    .in0(alu),
    .in1(const_4_5_out),
    .out(magma_Bits_5_eq_inst23_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst24 (
    .in0(alu),
    .in1(const_5_5_out),
    .out(magma_Bits_5_eq_inst24_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst25 (
    .in0(alu),
    .in1(const_3_5_out),
    .out(magma_Bits_5_eq_inst25_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst26 (
    .in0(alu),
    .in1(const_8_5_out),
    .out(magma_Bits_5_eq_inst26_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst27 (
    .in0(alu),
    .in1(const_19_5_out),
    .out(magma_Bits_5_eq_inst27_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst28 (
    .in0(alu),
    .in1(const_18_5_out),
    .out(magma_Bits_5_eq_inst28_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst29 (
    .in0(alu),
    .in1(const_20_5_out),
    .out(magma_Bits_5_eq_inst29_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst3 (
    .in0(alu),
    .in1(const_27_5_out),
    .out(magma_Bits_5_eq_inst3_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst30 (
    .in0(alu),
    .in1(const_15_5_out),
    .out(magma_Bits_5_eq_inst30_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst31 (
    .in0(alu),
    .in1(const_17_5_out),
    .out(magma_Bits_5_eq_inst31_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst32 (
    .in0(alu),
    .in1(const_21_5_out),
    .out(magma_Bits_5_eq_inst32_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst33 (
    .in0(alu),
    .in1(const_22_5_out),
    .out(magma_Bits_5_eq_inst33_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst34 (
    .in0(alu),
    .in1(const_24_5_out),
    .out(magma_Bits_5_eq_inst34_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst35 (
    .in0(alu),
    .in1(const_26_5_out),
    .out(magma_Bits_5_eq_inst35_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst36 (
    .in0(alu),
    .in1(const_25_5_out),
    .out(magma_Bits_5_eq_inst36_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst37 (
    .in0(alu),
    .in1(const_27_5_out),
    .out(magma_Bits_5_eq_inst37_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst38 (
    .in0(alu),
    .in1(const_28_5_out),
    .out(magma_Bits_5_eq_inst38_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst39 (
    .in0(alu),
    .in1(const_23_5_out),
    .out(magma_Bits_5_eq_inst39_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst4 (
    .in0(alu),
    .in1(const_1_5_out),
    .out(magma_Bits_5_eq_inst4_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst5 (
    .in0(alu),
    .in1(const_26_5_out),
    .out(magma_Bits_5_eq_inst5_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst6 (
    .in0(alu),
    .in1(const_27_5_out),
    .out(magma_Bits_5_eq_inst6_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst7 (
    .in0(alu),
    .in1(const_2_5_out),
    .out(magma_Bits_5_eq_inst7_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst8 (
    .in0(alu),
    .in1(const_6_5_out),
    .out(magma_Bits_5_eq_inst8_out)
);
PEGEN_coreir_eq #(
    .width(5)
) magma_Bits_5_eq_inst9 (
    .in0(alu),
    .in1(const_24_5_out),
    .out(magma_Bits_5_eq_inst9_out)
);
PEGEN_coreir_ashr #(
    .width(16)
) magma_SInt_16_ashr_inst0 (
    .in0(a),
    .in1(b),
    .out(magma_SInt_16_ashr_inst0_out)
);
wire [15:0] magma_SInt_16_ashr_inst1_in0;
assign magma_SInt_16_ashr_inst1_in0 = {magma_UInt_32_mul_inst0_out[15],magma_UInt_32_mul_inst0_out[14],magma_UInt_32_mul_inst0_out[13],magma_UInt_32_mul_inst0_out[12],magma_UInt_32_mul_inst0_out[11],magma_UInt_32_mul_inst0_out[10],magma_UInt_32_mul_inst0_out[9],magma_UInt_32_mul_inst0_out[8],magma_UInt_32_mul_inst0_out[7],magma_UInt_32_mul_inst0_out[6],magma_UInt_32_mul_inst0_out[5],magma_UInt_32_mul_inst0_out[4],magma_UInt_32_mul_inst0_out[3],magma_UInt_32_mul_inst0_out[2],magma_UInt_32_mul_inst0_out[1],magma_UInt_32_mul_inst0_out[0]};
PEGEN_coreir_ashr #(
    .width(16)
) magma_SInt_16_ashr_inst1 (
    .in0(magma_SInt_16_ashr_inst1_in0),
    .in1(c),
    .out(magma_SInt_16_ashr_inst1_out)
);
PEGEN_coreir_eq #(
    .width(16)
) magma_SInt_16_eq_inst0 (
    .in0(const_0_16_out),
    .in1(Mux2xBits16_inst24_O),
    .out(magma_SInt_16_eq_inst0_out)
);
PEGEN_coreir_neg #(
    .width(16)
) magma_SInt_16_neg_inst0 (
    .in(a),
    .out(magma_SInt_16_neg_inst0_out)
);
PEGEN_coreir_sge #(
    .width(16)
) magma_SInt_16_sge_inst0 (
    .in0(a),
    .in1(b),
    .out(magma_SInt_16_sge_inst0_out)
);
PEGEN_coreir_sge #(
    .width(16)
) magma_SInt_16_sge_inst1 (
    .in0(Mux2xBits16_inst2_O),
    .in1(c),
    .out(magma_SInt_16_sge_inst1_out)
);
PEGEN_coreir_sle #(
    .width(16)
) magma_SInt_16_sle_inst0 (
    .in0(a),
    .in1(b),
    .out(magma_SInt_16_sle_inst0_out)
);
PEGEN_coreir_sle #(
    .width(16)
) magma_SInt_16_sle_inst1 (
    .in0(const_0_16_out),
    .in1(a),
    .out(magma_SInt_16_sle_inst1_out)
);
PEGEN_coreir_lshr #(
    .width(16)
) magma_UInt_16_lshr_inst0 (
    .in0(a),
    .in1(b),
    .out(magma_UInt_16_lshr_inst0_out)
);
wire [15:0] magma_UInt_16_lshr_inst1_in0;
assign magma_UInt_16_lshr_inst1_in0 = {magma_UInt_32_mul_inst0_out[15],magma_UInt_32_mul_inst0_out[14],magma_UInt_32_mul_inst0_out[13],magma_UInt_32_mul_inst0_out[12],magma_UInt_32_mul_inst0_out[11],magma_UInt_32_mul_inst0_out[10],magma_UInt_32_mul_inst0_out[9],magma_UInt_32_mul_inst0_out[8],magma_UInt_32_mul_inst0_out[7],magma_UInt_32_mul_inst0_out[6],magma_UInt_32_mul_inst0_out[5],magma_UInt_32_mul_inst0_out[4],magma_UInt_32_mul_inst0_out[3],magma_UInt_32_mul_inst0_out[2],magma_UInt_32_mul_inst0_out[1],magma_UInt_32_mul_inst0_out[0]};
PEGEN_coreir_lshr #(
    .width(16)
) magma_UInt_16_lshr_inst1 (
    .in0(magma_UInt_16_lshr_inst1_in0),
    .in1(c),
    .out(magma_UInt_16_lshr_inst1_out)
);
PEGEN_coreir_uge #(
    .width(16)
) magma_UInt_16_uge_inst0 (
    .in0(a),
    .in1(b),
    .out(magma_UInt_16_uge_inst0_out)
);
PEGEN_coreir_uge #(
    .width(16)
) magma_UInt_16_uge_inst1 (
    .in0(Mux2xBits16_inst2_O),
    .in1(c),
    .out(magma_UInt_16_uge_inst1_out)
);
PEGEN_coreir_ule #(
    .width(16)
) magma_UInt_16_ule_inst0 (
    .in0(a),
    .in1(b),
    .out(magma_UInt_16_ule_inst0_out)
);
wire [16:0] magma_UInt_17_add_inst0_in0;
assign magma_UInt_17_add_inst0_in0 = {bit_const_0_None_out,a};
wire [16:0] magma_UInt_17_add_inst0_in1;
assign magma_UInt_17_add_inst0_in1 = {bit_const_0_None_out,Mux2xBits16_inst4_O};
PEGEN_coreir_add #(
    .width(17)
) magma_UInt_17_add_inst0 (
    .in0(magma_UInt_17_add_inst0_in0),
    .in1(magma_UInt_17_add_inst0_in1),
    .out(magma_UInt_17_add_inst0_out)
);
wire [16:0] magma_UInt_17_add_inst1_in1;
assign magma_UInt_17_add_inst1_in1 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,Mux2xBit_inst5_O};
PEGEN_coreir_add #(
    .width(17)
) magma_UInt_17_add_inst1 (
    .in0(magma_UInt_17_add_inst0_out),
    .in1(magma_UInt_17_add_inst1_in1),
    .out(magma_UInt_17_add_inst1_out)
);
wire [16:0] magma_UInt_17_add_inst2_in0;
assign magma_UInt_17_add_inst2_in0 = {bit_const_0_None_out,Mux2xUInt16_inst0_O};
wire [16:0] magma_UInt_17_add_inst2_in1;
assign magma_UInt_17_add_inst2_in1 = {bit_const_0_None_out,Mux2xBits16_inst5_O};
PEGEN_coreir_add #(
    .width(17)
) magma_UInt_17_add_inst2 (
    .in0(magma_UInt_17_add_inst2_in0),
    .in1(magma_UInt_17_add_inst2_in1),
    .out(magma_UInt_17_add_inst2_out)
);
wire [16:0] magma_UInt_17_add_inst3_in1;
assign magma_UInt_17_add_inst3_in1 = {bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,bit_const_0_None_out,Mux2xBit_inst6_O};
PEGEN_coreir_add #(
    .width(17)
) magma_UInt_17_add_inst3 (
    .in0(magma_UInt_17_add_inst2_out),
    .in1(magma_UInt_17_add_inst3_in1),
    .out(magma_UInt_17_add_inst3_out)
);
PEGEN_coreir_mul #(
    .width(32)
) magma_UInt_32_mul_inst0 (
    .in0(Mux2xUInt32_inst0_O),
    .in1(Mux2xUInt32_inst1_O),
    .out(magma_UInt_32_mul_inst0_out)
);
assign res = Mux2xBits16_inst24_O;
assign res_p = Mux2xBit_inst30_O;
assign Z = magma_SInt_16_eq_inst0_out;
assign N = Mux2xBits16_inst24_O[15];
assign C = Mux2xBit_inst28_O;
assign V = Mux2xBit_inst29_O;
endmodule

module PEGEN_PE (
    input [83:0] inst,
    input [15:0] data0,
    input [15:0] data1,
    input [15:0] data2,
    input bit0,
    input bit1,
    input bit2,
    input clk_en,
    output [15:0] O0,
    output O1,
    output [15:0] O2,
    output [15:0] O3,
    output [15:0] O4,
    input CLK,
    input ASYNCRESET
);
wire [15:0] ALU_inst0_res;
wire ALU_inst0_res_p;
wire ALU_inst0_Z;
wire ALU_inst0_N;
wire ALU_inst0_C;
wire ALU_inst0_V;
wire Cond_inst0_O;
wire [15:0] FPCustom_inst0_res;
wire FPCustom_inst0_res_p;
wire FPCustom_inst0_V;
wire [15:0] FPU_inst0_res;
wire FPU_inst0_N;
wire FPU_inst0_Z;
wire LUT_inst0_O;
wire Mux2xBit_inst0_O;
wire Mux2xBit_inst1_O;
wire Mux2xBit_inst2_O;
wire Mux2xBit_inst3_O;
wire Mux2xBit_inst4_O;
wire Mux2xBit_inst5_O;
wire Mux2xBit_inst6_O;
wire Mux2xBit_inst7_O;
wire [15:0] Mux2xBits16_inst0_O;
wire [15:0] Mux2xBits16_inst1_O;
wire [4:0] Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O;
wire [2:0] Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O;
wire [2:0] Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst1_O;
wire [1:0] Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O;
wire [1:0] Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst1_O;
wire [15:0] RegisterMode_inst0_O0;
wire [15:0] RegisterMode_inst0_O1;
wire [15:0] RegisterMode_inst1_O0;
wire [15:0] RegisterMode_inst1_O1;
wire [15:0] RegisterMode_inst2_O0;
wire [15:0] RegisterMode_inst2_O1;
wire RegisterMode_inst3_O0;
wire RegisterMode_inst3_O1;
wire RegisterMode_inst4_O0;
wire RegisterMode_inst4_O1;
wire RegisterMode_inst5_O0;
wire RegisterMode_inst5_O1;
wire bit_const_0_None_out;
wire [1:0] const_0_2_out;
wire [2:0] const_0_3_out;
wire [4:0] const_0_5_out;
wire [1:0] const_1_2_out;
wire [1:0] const_2_2_out;
wire magma_Bits_2_eq_inst0_out;
wire magma_Bits_2_eq_inst1_out;
wire magma_Bits_2_eq_inst2_out;
wire magma_Bits_2_eq_inst3_out;
wire magma_Bits_2_eq_inst4_out;
wire magma_Bits_2_eq_inst5_out;
wire magma_Bits_2_eq_inst6_out;
PEGEN_ALU ALU_inst0 (
    .alu(Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O),
    .signed_(inst[7:7]),
    .a(RegisterMode_inst0_O0),
    .b(RegisterMode_inst1_O0),
    .c(RegisterMode_inst2_O0),
    .d(RegisterMode_inst3_O0),
    .res(ALU_inst0_res),
    .res_p(ALU_inst0_res_p),
    .Z(ALU_inst0_Z),
    .N(ALU_inst0_N),
    .C(ALU_inst0_C),
    .V(ALU_inst0_V),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_Cond Cond_inst0 (
    .code(inst[20:16]),
    .alu(Mux2xBit_inst7_O),
    .lut(LUT_inst0_O),
    .Z(Mux2xBit_inst6_O),
    .N(Mux2xBit_inst4_O),
    .C(ALU_inst0_C),
    .V(Mux2xBit_inst5_O),
    .O(Cond_inst0_O),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_FPCustom FPCustom_inst0 (
    .op(Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst1_O),
    .signed_(inst[7:7]),
    .a(RegisterMode_inst0_O0),
    .b(RegisterMode_inst1_O0),
    .res(FPCustom_inst0_res),
    .res_p(FPCustom_inst0_res_p),
    .V(FPCustom_inst0_V),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_FPU FPU_inst0 (
    .fpu_op(Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst1_O),
    .a(RegisterMode_inst0_O0),
    .b(RegisterMode_inst1_O0),
    .res(FPU_inst0_res),
    .N(FPU_inst0_N),
    .Z(FPU_inst0_Z),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
wire [7:0] LUT_inst0_lut;
assign LUT_inst0_lut = {inst[15],inst[14],inst[13],inst[12],inst[11],inst[10],inst[9],inst[8]};
PEGEN_LUT LUT_inst0 (
    .lut(LUT_inst0_lut),
    .bit0(RegisterMode_inst3_O0),
    .bit1(RegisterMode_inst4_O0),
    .bit2(RegisterMode_inst5_O0),
    .O(LUT_inst0_O),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_Mux2xBit Mux2xBit_inst0 (
    .I0(bit_const_0_None_out),
    .I1(FPU_inst0_N),
    .S(magma_Bits_2_eq_inst6_out),
    .O(Mux2xBit_inst0_O)
);
PEGEN_Mux2xBit Mux2xBit_inst1 (
    .I0(FPCustom_inst0_V),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_2_eq_inst6_out),
    .O(Mux2xBit_inst1_O)
);
PEGEN_Mux2xBit Mux2xBit_inst2 (
    .I0(bit_const_0_None_out),
    .I1(FPU_inst0_Z),
    .S(magma_Bits_2_eq_inst6_out),
    .O(Mux2xBit_inst2_O)
);
PEGEN_Mux2xBit Mux2xBit_inst3 (
    .I0(FPCustom_inst0_res_p),
    .I1(bit_const_0_None_out),
    .S(magma_Bits_2_eq_inst6_out),
    .O(Mux2xBit_inst3_O)
);
PEGEN_Mux2xBit Mux2xBit_inst4 (
    .I0(Mux2xBit_inst0_O),
    .I1(ALU_inst0_N),
    .S(magma_Bits_2_eq_inst5_out),
    .O(Mux2xBit_inst4_O)
);
PEGEN_Mux2xBit Mux2xBit_inst5 (
    .I0(Mux2xBit_inst1_O),
    .I1(ALU_inst0_V),
    .S(magma_Bits_2_eq_inst5_out),
    .O(Mux2xBit_inst5_O)
);
PEGEN_Mux2xBit Mux2xBit_inst6 (
    .I0(Mux2xBit_inst2_O),
    .I1(ALU_inst0_Z),
    .S(magma_Bits_2_eq_inst5_out),
    .O(Mux2xBit_inst6_O)
);
PEGEN_Mux2xBit Mux2xBit_inst7 (
    .I0(Mux2xBit_inst3_O),
    .I1(ALU_inst0_res_p),
    .S(magma_Bits_2_eq_inst5_out),
    .O(Mux2xBit_inst7_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst0 (
    .I0(FPCustom_inst0_res),
    .I1(FPU_inst0_res),
    .S(magma_Bits_2_eq_inst6_out),
    .O(Mux2xBits16_inst0_O)
);
PEGEN_Mux2xBits16 Mux2xBits16_inst1 (
    .I0(Mux2xBits16_inst0_O),
    .I1(ALU_inst0_res),
    .S(magma_Bits_2_eq_inst5_out),
    .O(Mux2xBits16_inst1_O)
);
wire [4:0] Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I1;
assign Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I1 = {inst[6],inst[5],inst[4],inst[3],inst[2]};
PEGEN_Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3 Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0 (
    .I0(const_0_5_out),
    .I1(Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I1),
    .S(magma_Bits_2_eq_inst0_out),
    .O(Mux2xMagmaADTALU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O)
);
wire [2:0] Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I0;
assign Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I0 = {inst[4],inst[3],inst[2]};
PEGEN_Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3 Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0 (
    .I0(Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I0),
    .I1(const_0_3_out),
    .S(magma_Bits_2_eq_inst2_out),
    .O(Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O)
);
PEGEN_Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3 Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst1 (
    .I0(Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O),
    .I1(const_0_3_out),
    .S(magma_Bits_2_eq_inst0_out),
    .O(Mux2xMagmaADTFPCustom_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst1_O)
);
wire [1:0] Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I1;
assign Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I1 = {inst[3],inst[2]};
PEGEN_Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3 Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0 (
    .I0(const_0_2_out),
    .I1(Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_I1),
    .S(magma_Bits_2_eq_inst2_out),
    .O(Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O)
);
PEGEN_Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3 Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst1 (
    .I0(Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst0_O),
    .I1(const_0_2_out),
    .S(magma_Bits_2_eq_inst0_out),
    .O(Mux2xMagmaADTFPU_t_classpeakassemblerassemblerAssembler_Bits_DirectionUndirected3_inst1_O)
);
wire [15:0] RegisterMode_inst0_const_;
assign RegisterMode_inst0_const_ = {inst[38],inst[37],inst[36],inst[35],inst[34],inst[33],inst[32],inst[31],inst[30],inst[29],inst[28],inst[27],inst[26],inst[25],inst[24],inst[23]};
PEGEN_RegisterMode RegisterMode_inst0 (
    .mode(inst[22:21]),
    .const_(RegisterMode_inst0_const_),
    .value(data0),
    .clk_en(clk_en),
    .O0(RegisterMode_inst0_O0),
    .O1(RegisterMode_inst0_O1),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
wire [15:0] RegisterMode_inst1_const_;
assign RegisterMode_inst1_const_ = {inst[56],inst[55],inst[54],inst[53],inst[52],inst[51],inst[50],inst[49],inst[48],inst[47],inst[46],inst[45],inst[44],inst[43],inst[42],inst[41]};
PEGEN_RegisterMode RegisterMode_inst1 (
    .mode(inst[40:39]),
    .const_(RegisterMode_inst1_const_),
    .value(data1),
    .clk_en(clk_en),
    .O0(RegisterMode_inst1_O0),
    .O1(RegisterMode_inst1_O1),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
wire [15:0] RegisterMode_inst2_const_;
assign RegisterMode_inst2_const_ = {inst[74],inst[73],inst[72],inst[71],inst[70],inst[69],inst[68],inst[67],inst[66],inst[65],inst[64],inst[63],inst[62],inst[61],inst[60],inst[59]};
PEGEN_RegisterMode RegisterMode_inst2 (
    .mode(inst[58:57]),
    .const_(RegisterMode_inst2_const_),
    .value(data2),
    .clk_en(clk_en),
    .O0(RegisterMode_inst2_O0),
    .O1(RegisterMode_inst2_O1),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_RegisterMode_unq1 RegisterMode_inst3 (
    .mode(inst[76:75]),
    .const_(inst[77]),
    .value(bit0),
    .clk_en(clk_en),
    .O0(RegisterMode_inst3_O0),
    .O1(RegisterMode_inst3_O1),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_RegisterMode_unq1 RegisterMode_inst4 (
    .mode(inst[79:78]),
    .const_(inst[80]),
    .value(bit1),
    .clk_en(clk_en),
    .O0(RegisterMode_inst4_O0),
    .O1(RegisterMode_inst4_O1),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_RegisterMode_unq1 RegisterMode_inst5 (
    .mode(inst[82:81]),
    .const_(inst[83]),
    .value(bit2),
    .clk_en(clk_en),
    .O0(RegisterMode_inst5_O0),
    .O1(RegisterMode_inst5_O1),
    .CLK(CLK),
    .ASYNCRESET(ASYNCRESET)
);
PEGEN_corebit_const #(
    .value(1'b0)
) bit_const_0_None (
    .out(bit_const_0_None_out)
);
PEGEN_coreir_const #(
    .value(2'h0),
    .width(2)
) const_0_2 (
    .out(const_0_2_out)
);
PEGEN_coreir_const #(
    .value(3'h0),
    .width(3)
) const_0_3 (
    .out(const_0_3_out)
);
PEGEN_coreir_const #(
    .value(5'h00),
    .width(5)
) const_0_5 (
    .out(const_0_5_out)
);
PEGEN_coreir_const #(
    .value(2'h1),
    .width(2)
) const_1_2 (
    .out(const_1_2_out)
);
PEGEN_coreir_const #(
    .value(2'h2),
    .width(2)
) const_2_2 (
    .out(const_2_2_out)
);
wire [1:0] magma_Bits_2_eq_inst0_in0;
assign magma_Bits_2_eq_inst0_in0 = {inst[1],inst[0]};
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst0 (
    .in0(magma_Bits_2_eq_inst0_in0),
    .in1(const_0_2_out),
    .out(magma_Bits_2_eq_inst0_out)
);
wire [1:0] magma_Bits_2_eq_inst1_in0;
assign magma_Bits_2_eq_inst1_in0 = {inst[1],inst[0]};
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst1 (
    .in0(magma_Bits_2_eq_inst1_in0),
    .in1(const_0_2_out),
    .out(magma_Bits_2_eq_inst1_out)
);
wire [1:0] magma_Bits_2_eq_inst2_in0;
assign magma_Bits_2_eq_inst2_in0 = {inst[1],inst[0]};
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst2 (
    .in0(magma_Bits_2_eq_inst2_in0),
    .in1(const_2_2_out),
    .out(magma_Bits_2_eq_inst2_out)
);
wire [1:0] magma_Bits_2_eq_inst3_in0;
assign magma_Bits_2_eq_inst3_in0 = {inst[1],inst[0]};
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst3 (
    .in0(magma_Bits_2_eq_inst3_in0),
    .in1(const_2_2_out),
    .out(magma_Bits_2_eq_inst3_out)
);
wire [1:0] magma_Bits_2_eq_inst4_in0;
assign magma_Bits_2_eq_inst4_in0 = {inst[1],inst[0]};
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst4 (
    .in0(magma_Bits_2_eq_inst4_in0),
    .in1(const_1_2_out),
    .out(magma_Bits_2_eq_inst4_out)
);
wire [1:0] magma_Bits_2_eq_inst5_in0;
assign magma_Bits_2_eq_inst5_in0 = {inst[1],inst[0]};
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst5 (
    .in0(magma_Bits_2_eq_inst5_in0),
    .in1(const_0_2_out),
    .out(magma_Bits_2_eq_inst5_out)
);
wire [1:0] magma_Bits_2_eq_inst6_in0;
assign magma_Bits_2_eq_inst6_in0 = {inst[1],inst[0]};
PEGEN_coreir_eq #(
    .width(2)
) magma_Bits_2_eq_inst6 (
    .in0(magma_Bits_2_eq_inst6_in0),
    .in1(const_2_2_out),
    .out(magma_Bits_2_eq_inst6_out)
);
assign O0 = Mux2xBits16_inst1_O;
assign O1 = Cond_inst0_O;
assign O2 = RegisterMode_inst0_O1;
assign O3 = RegisterMode_inst1_O1;
assign O4 = RegisterMode_inst2_O1;
endmodule

