module AO_CELL ( 
input logic  A1,
input logic  A2, 
input logic  B1, 
input logic  B2, 
output logic  Z);  

`ifdef TSMC16
AO22D0BWP16P90 inst(.A1(A1), .A2(A2), .B1(B1), .B2(B2), .Z(Z));
`elsif GF12
SC7P5T_AO22X0P5_SSC14R inst(.A1(A1), .A2(A2), .B1(B1), .B2(B2), .Z(Z));
`else
assign Z = ((A1 & A2) | (B1 & B2)); 
`endif

endmodule 
