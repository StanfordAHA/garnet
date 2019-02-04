module corebit_and (
  input in0,
  input in1,
  output out
);
  assign out = in0 & in1;

endmodule  // corebit_and

module coreir_reg_arst #(parameter arst_posedge=1, parameter clk_posedge=1, parameter init=1, parameter width=1) (
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

endmodule  // coreir_reg_arst

module coreir_ult #(parameter width=1) (
  input [width-1:0] in0,
  input [width-1:0] in1,
  output out
);
  assign out = in0 < in1;

endmodule  // coreir_ult

module coreir_const #(parameter value=1, parameter width=1) (
  output [width-1:0] out
);
  assign out = value;

endmodule  // coreir_const

module coreir_mux #(parameter width=1) (
  input [width-1:0] in0,
  input [width-1:0] in1,
  input sel,
  output [width-1:0] out
);
  assign out = sel ? in1 : in0;

endmodule  // coreir_mux

// Generated from commonlib.muxn(N:2, width:32)
module muxn_U2 (
  input [31:0] in_data_0,
  input [31:0] in_data_1,
  input [0:0] in_sel,
  output [31:0] out
);


  // Instancing generated Module: coreir.mux(width:32)
  wire [31:0] _join__in0;
  wire [31:0] _join__in1;
  wire [31:0] _join__out;
  wire  _join__sel;
  coreir_mux #(.width(32)) _join(
    .in0(_join__in0),
    .in1(_join__in1),
    .out(_join__out),
    .sel(_join__sel)
  );

  assign _join__in0[31:0] = in_data_0[31:0];

  assign _join__in1[31:0] = in_data_1[31:0];

  assign out[31:0] = _join__out[31:0];

  assign _join__sel = in_sel[0];


endmodule  // muxn_U2

module coreir_eq #(parameter width=1) (
  input [width-1:0] in0,
  input [width-1:0] in1,
  output out
);
  assign out = in0 == in1;

endmodule  // coreir_eq

module Mux2x32 (
  input [31:0] I0,
  input [31:0] I1,
  output [31:0] O,
  input  S
);


  // Instancing generated Module: commonlib.muxn(N:2, width:32)
  wire [31:0] coreir_commonlib_mux2x32_inst0__in_data_0;
  wire [31:0] coreir_commonlib_mux2x32_inst0__in_data_1;
  wire [0:0] coreir_commonlib_mux2x32_inst0__in_sel;
  wire [31:0] coreir_commonlib_mux2x32_inst0__out;
  muxn_U2 coreir_commonlib_mux2x32_inst0(
    .in_data_0(coreir_commonlib_mux2x32_inst0__in_data_0),
    .in_data_1(coreir_commonlib_mux2x32_inst0__in_data_1),
    .in_sel(coreir_commonlib_mux2x32_inst0__in_sel),
    .out(coreir_commonlib_mux2x32_inst0__out)
  );

  assign coreir_commonlib_mux2x32_inst0__in_data_0[31:0] = I0[31:0];

  assign coreir_commonlib_mux2x32_inst0__in_data_1[31:0] = I1[31:0];

  assign coreir_commonlib_mux2x32_inst0__in_sel[0] = S;

  assign O[31:0] = coreir_commonlib_mux2x32_inst0__out[31:0];


endmodule  // Mux2x32

module MuxWrapper_2_32 (
  input [31:0] I_0,
  input [31:0] I_1,
  output [31:0] O,
  input [0:0] S
);


  wire [31:0] Mux2x32_inst0__I0;
  wire [31:0] Mux2x32_inst0__I1;
  wire [31:0] Mux2x32_inst0__O;
  wire  Mux2x32_inst0__S;
  Mux2x32 Mux2x32_inst0(
    .I0(Mux2x32_inst0__I0),
    .I1(Mux2x32_inst0__I1),
    .O(Mux2x32_inst0__O),
    .S(Mux2x32_inst0__S)
  );

  assign Mux2x32_inst0__I0[31:0] = I_0[31:0];

  assign Mux2x32_inst0__I1[31:0] = I_1[31:0];

  assign O[31:0] = Mux2x32_inst0__O[31:0];

  assign Mux2x32_inst0__S = S[0];


endmodule  // MuxWrapper_2_32

module Mux2xOutBits32 (
  input [31:0] I0,
  input [31:0] I1,
  output [31:0] O,
  input  S
);


  // Instancing generated Module: commonlib.muxn(N:2, width:32)
  wire [31:0] coreir_commonlib_mux2x32_inst0__in_data_0;
  wire [31:0] coreir_commonlib_mux2x32_inst0__in_data_1;
  wire [0:0] coreir_commonlib_mux2x32_inst0__in_sel;
  wire [31:0] coreir_commonlib_mux2x32_inst0__out;
  muxn_U2 coreir_commonlib_mux2x32_inst0(
    .in_data_0(coreir_commonlib_mux2x32_inst0__in_data_0),
    .in_data_1(coreir_commonlib_mux2x32_inst0__in_data_1),
    .in_sel(coreir_commonlib_mux2x32_inst0__in_sel),
    .out(coreir_commonlib_mux2x32_inst0__out)
  );

  assign coreir_commonlib_mux2x32_inst0__in_data_0[31:0] = I0[31:0];

  assign coreir_commonlib_mux2x32_inst0__in_data_1[31:0] = I1[31:0];

  assign coreir_commonlib_mux2x32_inst0__in_sel[0] = S;

  assign O[31:0] = coreir_commonlib_mux2x32_inst0__out[31:0];


endmodule  // Mux2xOutBits32

module MuxWithDefaultWrapper_2_32_8_0 (
  input [0:0] EN,
  input [31:0] I_0,
  input [31:0] I_1,
  output [31:0] O,
  input [7:0] S
);


  wire [31:0] MuxWrapper_2_32_inst0__I_0;
  wire [31:0] MuxWrapper_2_32_inst0__I_1;
  wire [31:0] MuxWrapper_2_32_inst0__O;
  wire [0:0] MuxWrapper_2_32_inst0__S;
  MuxWrapper_2_32 MuxWrapper_2_32_inst0(
    .I_0(MuxWrapper_2_32_inst0__I_0),
    .I_1(MuxWrapper_2_32_inst0__I_1),
    .O(MuxWrapper_2_32_inst0__O),
    .S(MuxWrapper_2_32_inst0__S)
  );

  wire [31:0] MuxWrapper_2_32_inst1__I_0;
  wire [31:0] MuxWrapper_2_32_inst1__I_1;
  wire [31:0] MuxWrapper_2_32_inst1__O;
  wire [0:0] MuxWrapper_2_32_inst1__S;
  MuxWrapper_2_32 MuxWrapper_2_32_inst1(
    .I_0(MuxWrapper_2_32_inst1__I_0),
    .I_1(MuxWrapper_2_32_inst1__I_1),
    .O(MuxWrapper_2_32_inst1__O),
    .S(MuxWrapper_2_32_inst1__S)
  );

  wire  and_inst0__in0;
  wire  and_inst0__in1;
  wire  and_inst0__out;
  corebit_and and_inst0(
    .in0(and_inst0__in0),
    .in1(and_inst0__in1),
    .out(and_inst0__out)
  );

  // Instancing generated Module: coreir.const(width:32)
  wire [31:0] const_0_32__out;
  coreir_const #(.value(32'h00000000),.width(32)) const_0_32(
    .out(const_0_32__out)
  );

  // Instancing generated Module: coreir.const(width:8)
  wire [7:0] const_2_8__out;
  coreir_const #(.value(8'h02),.width(8)) const_2_8(
    .out(const_2_8__out)
  );

  // Instancing generated Module: coreir.ult(width:8)
  wire [7:0] coreir_ult8_inst0__in0;
  wire [7:0] coreir_ult8_inst0__in1;
  wire  coreir_ult8_inst0__out;
  coreir_ult #(.width(8)) coreir_ult8_inst0(
    .in0(coreir_ult8_inst0__in0),
    .in1(coreir_ult8_inst0__in1),
    .out(coreir_ult8_inst0__out)
  );

  assign MuxWrapper_2_32_inst0__I_0[31:0] = I_0[31:0];

  assign MuxWrapper_2_32_inst0__I_1[31:0] = I_1[31:0];

  assign MuxWrapper_2_32_inst1__I_1[31:0] = MuxWrapper_2_32_inst0__O[31:0];

  assign MuxWrapper_2_32_inst0__S[0] = S[0];

  assign MuxWrapper_2_32_inst1__I_0[31:0] = const_0_32__out[31:0];

  assign O[31:0] = MuxWrapper_2_32_inst1__O[31:0];

  assign MuxWrapper_2_32_inst1__S[0] = and_inst0__out;

  assign and_inst0__in0 = coreir_ult8_inst0__out;

  assign and_inst0__in1 = EN[0];

  assign coreir_ult8_inst0__in1[7:0] = const_2_8__out[7:0];

  assign coreir_ult8_inst0__in0[7:0] = S[7:0];


endmodule  // MuxWithDefaultWrapper_2_32_8_0

module Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32 (
  input  ASYNCRESET,
  input  CE,
  input  CLK,
  input [31:0] I,
  output [31:0] O
);


  wire [31:0] enable_mux__I0;
  wire [31:0] enable_mux__I1;
  wire [31:0] enable_mux__O;
  wire  enable_mux__S;
  Mux2xOutBits32 enable_mux(
    .I0(enable_mux__I0),
    .I1(enable_mux__I1),
    .O(enable_mux__O),
    .S(enable_mux__S)
  );

  // Instancing generated Module: coreir.reg_arst(width:32)
  wire  value__arst;
  wire  value__clk;
  wire [31:0] value__in;
  wire [31:0] value__out;
  coreir_reg_arst #(.arst_posedge(1),.clk_posedge(1),.init(32'h00000000),.width(32)) value(
    .arst(value__arst),
    .clk(value__clk),
    .in(value__in),
    .out(value__out)
  );

  assign enable_mux__I0[31:0] = value__out[31:0];

  assign enable_mux__I1[31:0] = I[31:0];

  assign value__in[31:0] = enable_mux__O[31:0];

  assign enable_mux__S = CE;

  assign value__arst = ASYNCRESET;

  assign value__clk = CLK;

  assign O[31:0] = value__out[31:0];


endmodule  // Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32

module ConfigRegister_32_8_32_0 (
  output [31:0] O,
  input  clk,
  input [7:0] config_addr,
  input [31:0] config_data,
  input  config_en,
  input  reset
);


  wire  Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__ASYNCRESET;
  wire  Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CE;
  wire  Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CLK;
  wire [31:0] Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__I;
  wire [31:0] Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__O;
  Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32 Register_has_ce_True_has_reset_False_has_asyn
c_reset_True_type_Bits_n_32_inst0(
    .ASYNCRESET(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__ASYNCRESET),
    .CE(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CE),
    .CLK(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CLK),
    .I(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__I),
    .O(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__O)
  );

  wire  and_inst0__in0;
  wire  and_inst0__in1;
  wire  and_inst0__out;
  corebit_and and_inst0(
    .in0(and_inst0__in0),
    .in1(and_inst0__in1),
    .out(and_inst0__out)
  );

  // Instancing generated Module: coreir.const(width:8)
  wire [7:0] const_0_8__out;
  coreir_const #(.value(8'h00),.width(8)) const_0_8(
    .out(const_0_8__out)
  );

  // Instancing generated Module: coreir.eq(width:8)
  wire [7:0] coreir_eq_8_inst0__in0;
  wire [7:0] coreir_eq_8_inst0__in1;
  wire  coreir_eq_8_inst0__out;
  coreir_eq #(.width(8)) coreir_eq_8_inst0(
    .in0(coreir_eq_8_inst0__in0),
    .in1(coreir_eq_8_inst0__in1),
    .out(coreir_eq_8_inst0__out)
  );

  assign Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__ASYNCRESET = reset;

  assign Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CE = and_inst0__out;

  assign Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CLK = clk;

  assign Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__I[31:0] = config_data[31:0];

  assign O[31:0] = Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__O[31:0];

  assign and_inst0__in0 = coreir_eq_8_inst0__out;

  assign and_inst0__in1 = config_en;

  assign coreir_eq_8_inst0__in1[7:0] = const_0_8__out[7:0];

  assign coreir_eq_8_inst0__in0[7:0] = config_addr[7:0];


endmodule  // ConfigRegister_32_8_32_0

module ConfigRegister_32_8_32_1 (
  output [31:0] O,
  input  clk,
  input [7:0] config_addr,
  input [31:0] config_data,
  input  config_en,
  input  reset
);


  wire  Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__ASYNCRESET;
  wire  Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CE;
  wire  Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CLK;
  wire [31:0] Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__I;
  wire [31:0] Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__O;
  Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32 Register_has_ce_True_has_reset_False_has_asyn
c_reset_True_type_Bits_n_32_inst0(
    .ASYNCRESET(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__ASYNCRESET),
    .CE(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CE),
    .CLK(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CLK),
    .I(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__I),
    .O(Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__O)
  );

  wire  and_inst0__in0;
  wire  and_inst0__in1;
  wire  and_inst0__out;
  corebit_and and_inst0(
    .in0(and_inst0__in0),
    .in1(and_inst0__in1),
    .out(and_inst0__out)
  );

  // Instancing generated Module: coreir.const(width:8)
  wire [7:0] const_1_8__out;
  coreir_const #(.value(8'h01),.width(8)) const_1_8(
    .out(const_1_8__out)
  );

  // Instancing generated Module: coreir.eq(width:8)
  wire [7:0] coreir_eq_8_inst0__in0;
  wire [7:0] coreir_eq_8_inst0__in1;
  wire  coreir_eq_8_inst0__out;
  coreir_eq #(.width(8)) coreir_eq_8_inst0(
    .in0(coreir_eq_8_inst0__in0),
    .in1(coreir_eq_8_inst0__in1),
    .out(coreir_eq_8_inst0__out)
  );

  assign Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__ASYNCRESET = reset;

  assign Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CE = and_inst0__out;

  assign Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__CLK = clk;

  assign Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__I[31:0] = config_data[31:0];

  assign O[31:0] = Register_has_ce_True_has_reset_False_has_async_reset_True_type_Bits_n_32_inst0__O[31:0];

  assign and_inst0__in0 = coreir_eq_8_inst0__out;

  assign and_inst0__in1 = config_en;

  assign coreir_eq_8_inst0__in1[7:0] = const_1_8__out[7:0];

  assign coreir_eq_8_inst0__in0[7:0] = config_addr[7:0];


endmodule  // ConfigRegister_32_8_32_1

module DummyCore (
  input  clk,
  input [7:0] config_config_addr,
  input [31:0] config_config_data,
  input [0:0] config_read,
  input [0:0] config_write,
  input [15:0] data_in_16b,
  input [0:0] data_in_1b,
  output [15:0] data_out_16b,
  output [0:0] data_out_1b,
  output [31:0] read_config_data,
  input  reset
);


  wire [0:0] MuxWithDefaultWrapper_2_32_8_0_inst0__EN;
  wire [31:0] MuxWithDefaultWrapper_2_32_8_0_inst0__I_0;
  wire [31:0] MuxWithDefaultWrapper_2_32_8_0_inst0__I_1;
  wire [31:0] MuxWithDefaultWrapper_2_32_8_0_inst0__O;
  wire [7:0] MuxWithDefaultWrapper_2_32_8_0_inst0__S;
  MuxWithDefaultWrapper_2_32_8_0 MuxWithDefaultWrapper_2_32_8_0_inst0(
    .EN(MuxWithDefaultWrapper_2_32_8_0_inst0__EN),
    .I_0(MuxWithDefaultWrapper_2_32_8_0_inst0__I_0),
    .I_1(MuxWithDefaultWrapper_2_32_8_0_inst0__I_1),
    .O(MuxWithDefaultWrapper_2_32_8_0_inst0__O),
    .S(MuxWithDefaultWrapper_2_32_8_0_inst0__S)
  );

  wire [31:0] dummy_1__O;
  wire  dummy_1__clk;
  wire [7:0] dummy_1__config_addr;
  wire [31:0] dummy_1__config_data;
  wire  dummy_1__config_en;
  wire  dummy_1__reset;
  ConfigRegister_32_8_32_0 dummy_1(
    .O(dummy_1__O),
    .clk(dummy_1__clk),
    .config_addr(dummy_1__config_addr),
    .config_data(dummy_1__config_data),
    .config_en(dummy_1__config_en),
    .reset(dummy_1__reset)
  );

  wire [31:0] dummy_2__O;
  wire  dummy_2__clk;
  wire [7:0] dummy_2__config_addr;
  wire [31:0] dummy_2__config_data;
  wire  dummy_2__config_en;
  wire  dummy_2__reset;
  ConfigRegister_32_8_32_1 dummy_2(
    .O(dummy_2__O),
    .clk(dummy_2__clk),
    .config_addr(dummy_2__config_addr),
    .config_data(dummy_2__config_data),
    .config_en(dummy_2__config_en),
    .reset(dummy_2__reset)
  );

  assign MuxWithDefaultWrapper_2_32_8_0_inst0__EN[0:0] = config_read[0:0];

  assign MuxWithDefaultWrapper_2_32_8_0_inst0__I_0[31:0] = dummy_1__O[31:0];

  assign MuxWithDefaultWrapper_2_32_8_0_inst0__I_1[31:0] = dummy_2__O[31:0];

  assign read_config_data[31:0] = MuxWithDefaultWrapper_2_32_8_0_inst0__O[31:0];

  assign MuxWithDefaultWrapper_2_32_8_0_inst0__S[7:0] = config_config_addr[7:0];

  assign dummy_1__clk = clk;

  assign dummy_1__config_addr[7:0] = config_config_addr[7:0];

  assign dummy_1__config_data[31:0] = config_config_data[31:0];

  assign dummy_1__config_en = config_write[0];

  assign dummy_1__reset = reset;

  assign dummy_2__clk = clk;

  assign dummy_2__config_addr[7:0] = config_config_addr[7:0];

  assign dummy_2__config_data[31:0] = config_config_data[31:0];

  assign dummy_2__config_en = config_write[0];

  assign dummy_2__reset = reset;

  assign data_out_16b[15:0] = data_in_16b[15:0];

  assign data_out_1b[0:0] = data_in_1b[0:0];


endmodule  // DummyCore


