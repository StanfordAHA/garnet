module priority_encoder_0
(
    input logic [0:0] data_0,
    input logic [0:0] data_1,
    input logic [0:0] data_2,
    input logic [0:0] data_3,
    input logic [3:0] sel,
    output logic [0:0] data_out
);

always_comb begin
    if (sel[0] == 1'b1) begin
        data_out = data_0;
    end
    else if (sel[1] == 1'b1) begin
        data_out = data_1;
    end
    else if (sel[2] == 1'b1) begin
        data_out = data_2;
    end
    else if (sel[3] == 1'b1) begin
        data_out = data_3;
    end
    else begin
        data_out = 'h0;
    end
end

endmodule
