module cgra #(
    parameter int NUM_COLS_PER_PRR = 2,
    parameter int NUM_ROWS_PER_PRR = 16,
    parameter int TILE_ID_WIDTH = 16,
    parameter int NUM_PRR = 16
) (
    input  logic                            clk,
    input  logic                            reset,
    input  logic                            stall [NUM_PRR],
    input  logic                            cfg_wr_en [NUM_PRR],
    input  logic [CGRA_CFG_ADDR_WIDTH-1:0]  cfg_wr_addr [NUM_PRR],
    input  logic [CGRA_CFG_DATA_WIDTH-1:0]  cfg_wr_data [NUM_PRR],
    input  logic                            cfg_rd_en [NUM_PRR],
    input  logic [CGRA_CFG_ADDR_WIDTH-1:0]  cfg_rd_addr [NUM_PRR],
    output logic [CGRA_CFG_DATA_WIDTH-1:0]  cfg_rd_data [NUM_PRR],
    input  logic                            io1_g2io [NUM_PRR],
    input  logic [15:0]                     io16_g2io [NUM_PRR],
    output logic                            io1_io2g [NUM_PRR],
    output logic [15:0]                     io16_io2g [NUM_PRR]
);

genvar i;
generate
for (i = 0; i < NUM_PRR; i++) begin: prr
    prr prr (
        .*
    );
end
endgenerate

noc noc (
    .


endmodule
