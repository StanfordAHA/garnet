// Stubs for horizontal and vertical pad cells

module PRWDWUWSWCDGH_H (C, DS0, DS1, DS2, I, IE, OEN, PAD, PU, PD, ST, SL, RTE);

  input  DS0, DS1, DS2, I, IE, OEN, PU, PD, ST, SL, RTE;
  output C;
  output  PAD;
  
  assign C = PAD;
  
  assign PAD = ((IE == 1'b0) & (OEN ==1'b0)) ? I : 1'bz;

endmodule
