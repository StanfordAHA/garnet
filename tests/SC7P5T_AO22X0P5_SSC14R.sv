module AO22D0BWP16P90 ( 
input logic  A1,
input logic  A2, 
input logic  B1, 
input logic  B2, 
output logic  Z);  
assign Z = ((A1 & A2) | (B1 & B2)); 
endmodule 

