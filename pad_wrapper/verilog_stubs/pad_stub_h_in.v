// Stubs for horizontal input pad cell

module PRWDWUWSWCDGH_H (C, DS0, DS1, DS2, I, IE, OEN, PAD, PU, PD, ST, SL, RTE);

  input  DS0, DS1, DS2, I, IE, OEN, PU, PD, ST, SL, RTE;
  output C;
  input  PAD;
  
  assign C = ((IE == 1'b1) & (OEN ==1'b1)) ? PAD : 1'bz;

endmodule
