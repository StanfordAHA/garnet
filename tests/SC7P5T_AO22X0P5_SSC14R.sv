module SC7P5T_AO22X0P5_SSC14R ( 
input logic  A1,
input logic  A2, 
input logic  B1, 
input logic  B2, 
output logic  Z);  
assign Z = ((A1 & A2) | (B1 & B2)); 
endmodule 

