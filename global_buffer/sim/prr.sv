module prr (
    input  logic [PRR_ID_WIDTH-1:0]         prr_id,
    input  logic                            clk,
    input  logic                            reset,
    input  logic                            stall,
    input  logic                            cfg_wr_en,
    input  logic [CGRA_CFG_ADDR_WIDTH-1:0]  cfg_wr_addr,
    input  logic [CGRA_CFG_DATA_WIDTH-1:0]  cfg_wr_data,
    input  logic                            cfg_rd_en,
    input  logic [CGRA_CFG_ADDR_WIDTH-1:0]  cfg_rd_addr,
    output logic [CGRA_CFG_DATA_WIDTH-1:0]  cfg_rd_data
    input  logic                            io1_g2io,
    input  logic [15:0]                     io16_g2io,
    output logic                            io1_io2f,
    output logic [15:0]                     io16_io2f,
    input  logic                            io1_f2io,
    input  logic [15:0]                     io16_f2io,
    output logic                            io1_io2g,
    output logic [15:0]                     io16_io2g
);

// ---------------------------------------
// Configuration
// ---------------------------------------
logic [CGRA_CFG_DATA_WIDTH-1:0] cfg_reg [CGRA_CFG_DEPTH];
localparam int CGRA_CFG_PRR_WIDTH = $clog2(CGRA_CFG_DEPTH);

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i = 0; i < CGRA_CFG_DEPTH; i++) begin
            cfg_reg[i] <= 0;
        end
    end else begin
        if (cfg_wr_en) begin
            if (cfg_wr_addr[CGRA_CFG_ADDR_WIDTH-1 -: PRR_ID_WIDTH] == prr_id) begin
                cfg_reg[cfg_wr_addr[CGRA_CFG_PRR_WIDTH-1:0]] <= cfg_wr_data;
            end
        end
    end
end

always_comb begin
    if (cfg_rd_en && cfg_rd_addr[CGRA_CFG_ADDR_WIDTH-1 -:PRR_ID_WIDTH] == prr_id) begin
        cfg_rd_data = cfg_reg[cfg_rd_addr[CGRA_CFG_PRR_WIDTH-1:0]];
    end else begin
        cfg_rd_data = '0;
    end
end

// ---------------------------------------
// Data
// ---------------------------------------
assign io1_io2f = io1_g2io;
assign io16_io2f = io16_g2io;

assign io1_io2g = io1_f2io;
assign io16_io2g = io16_f2io;

endmodule
