module TS1N16FFCLLSBLVTC2048X64M8SW
(
    Q, CLK, CEB, BWEB, WEB, A, D, RTSEL, WTSEL
);

localparam WIDTH = 64;
localparam ADDR_WIDTH = 11;

output reg [WIDTH-1:0] Q;
input        CLK;
input        CEB;
input        WEB;
input [ADDR_WIDTH-1:0]  A;
input [WIDTH-1:0] D;
input [WIDTH-1:0] BWEB;

input [1:0]  RTSEL;
input [1:0]  WTSEL;

reg[WIDTH-1:0] test_sig;

reg [WIDTH-1:0]   data_array [0:2**ADDR_WIDTH-1];
   
integer i;
always @(posedge CLK) begin
    if (CEB == 1'b0) begin                  // ACTIVE LOW!!
        Q = data_array[A];
        if (WEB == 1'b0) begin
            for(i=0; i<WIDTH; i=i+1) begin
                if (!(BWEB[i]) == 1) data_array[A][i] = D[i];  // ACTIVE LOW!!
            end
        end
        test_sig = data_array[A];
    end
end

endmodule
