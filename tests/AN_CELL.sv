module AN_CELL ( 
input logic  A1, 
input logic  A2, 
output logic  Z); 

`ifdef TSMC16
AN2D0BWP16P90 inst(.A1(A1), .A2(A2), .Z(Z));
`elsif GF12
SC7P5T_AN2X0P5_SSC14R inst(.A(A1), .B(A2), .Z(Z));
`else
assign Z = (A1 & A2); 
`endif

endmodule  
