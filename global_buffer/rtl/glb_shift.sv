/*=============================================================================
** Module: glb_shift.sv
** Description:
**              Shift register
** Author: Taeyoung Kong
** Change history:
**      04/02/2020
**          - Implement first version of shift register
**===========================================================================*/
module glb_shift #(
    parameter DATA_WIDTH = 1,
    parameter DEPTH = 4
) (
    input  logic                    clk,
    input  logic                    clk_en,
    input  logic                    reset,
    input  logic [DATA_WIDTH-1:0]   data_in,
    output logic [DATA_WIDTH-1:0]   data_out [DEPTH]
);

logic [DATA_WIDTH-1:0] holding_register [DEPTH];

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<DEPTH; i=i+1) begin
            holding_register[i] <= '0;
        end
    end
    else if (clk_en) begin
        for (int i=0; i<DEPTH; i=i+1) begin
            if (i == 0) begin
                holding_register[i] <= data_in;
            end
            else begin
                holding_register[i] <= holding_register[i-1];
            end
        end
    end
end

assign data_out = holding_register;

endmodule
