module column #(
    parameter CGRA_TILE_WIDTH = 5
) (
    input  logic                            clk,
    input  logic                            rst_n,
    input  logic [CGRA_TILE_WIDTH-1:0]      id,

    input  logic                            rf_wr_en,
    input  logic                            rf_rd_en,
    input  logic [CGRA_CFG_ADDR_WIDTH-1:0]  rf_addr,
    input  logic [CGRA_CFG_DATA_WIDTH-1:0]  rf_wr_data,
    output logic [CGRA_CFG_DATA_WIDTH-1:0]  rf_rd_data,
    output logic                            rf_rd_data_valid
);

//============================================================================//
// Register file
//============================================================================//
// just assume there are only 256 registers
logic [CGRA_CFG_DATA_WIDTH-1:0] reg_file [255:0];

// write
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for(int i=0; i < 2**CGRA_CFG_ADDR_WIDTH-1; i++) begin
            reg_file[i] <= '0;
        end
    end
    else begin
        if (rf_wr_en && rf_addr[4:0] == id) begin
            // reg_file[rf_addr[CGRA_CFG_ADDR_WIDTH-1:8]] <= rf_wr_data;
            reg_file[rf_addr[15:8]] <= rf_wr_data;
        end
    end
end

// read
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        rf_rd_data <= '0;
        rf_rd_data_valid <= 1'b0;
    end
    else begin
        if (rf_rd_en && rf_addr[4:0] == id) begin
            // rf_rd_data <= reg_file[rf_addr[CGRA_CFG_ADDR_WIDTH-1:8]];
            rf_rd_data <= reg_file[rf_addr[15:8]];
            rf_rd_data_valid <= 1'b1;
        end
        else begin
            rf_rd_data <= '0;
            rf_rd_data_valid <= 1'b0;
        end
    end
end

endmodule
