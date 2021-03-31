module cgra #(
    parameter NUM_GLB_TILES = 16,
    parameter NUM_CGRA_TILES = 32,
    parameter CGRA_CFG_DATA_WIDTH = 32,
    parameter CGRA_PER_GLB = 2
) (
    input  logic reset,
    input  logic clk,

    pcfg_ifc c_ifc[NUM_GLB_TILES],
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_f2g_rd_data,
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_cfg_f2g_rd_data_valid
);

logic                            rf_wr_en[NUM_CGRA_TILES-1:0];
logic                            rf_rd_en[NUM_CGRA_TILES-1:0];
logic [CGRA_CFG_ADDR_WIDTH-1:0]  rf_addr[NUM_CGRA_TILES-1:0];
logic [CGRA_CFG_DATA_WIDTH-1:0]  rf_wr_data[NUM_CGRA_TILES-1:0];
logic [CGRA_CFG_DATA_WIDTH-1:0]  rf_rd_data[NUM_CGRA_TILES-1:0];
logic                            rf_rd_data_valid[NUM_CGRA_TILES-1:0];

genvar i,j;
generate
    for(i=0; i<NUM_GLB_TILES; i++) begin
        for(j=0; j < CGRA_PER_GLB; j++) begin
            assign rf_wr_en[i*CGRA_PER_GLB+j]      = c_ifc[i].cgra_cfg_wr_en;
            assign rf_rd_en[i*CGRA_PER_GLB+j]      = c_ifc[i].cgra_cfg_rd_en;
            assign rf_addr[i*CGRA_PER_GLB+j]       = c_ifc[i].cgra_cfg_addr;
            assign rf_wr_data[i*CGRA_PER_GLB+j]    = c_ifc[i].cgra_cfg_data;
        end
    end
endgenerate

//============================================================================//
// Register file
//============================================================================//
// just assume there are only 256 registers
logic [CGRA_CFG_DATA_WIDTH-1:0] reg_file [NUM_CGRA_TILES-1:0][255:0];

// write
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for(int i=0; i < NUM_CGRA_TILES; i++) begin
            for(int j=0; j < 256; j++) begin
                reg_file[i][j] <= '0;
            end
        end
    end
    else begin
        for(int i=0; i < NUM_GLB_TILES; i++) begin
            for(int j=0; j < CGRA_PER_GLB; j++) begin
                for(int k=0; k < 256; k++) begin
                    if (rf_wr_en[i] && rf_addr[i][7:0] == (i*CGRA_PER_GLB+j)) begin
                        // reg_file[rf_addr[CGRA_CFG_ADDR_WIDTH-1:8]] <= rf_wr_data;
                        reg_file[(i*CGRA_PER_GLB+j)][rf_addr[i][15:8]] <= rf_wr_data[i];
                    end
                end
            end
        end
    end
end

// read
// always_ff @(posedge clk or negedge rst_n) begin
//     if (!rst_n) begin
//         rf_rd_data <= '0;
//         rf_rd_data_valid <= 1'b0;
//     end
//     else begin
//         if (rf_rd_en && rf_addr[4:0] == id) begin
//             // rf_rd_data <= reg_file[rf_addr[CGRA_CFG_ADDR_WIDTH-1:8]];
//             rf_rd_data <= reg_file[rf_addr[15:8]];
//             rf_rd_data_valid <= 1'b1;
//         end
//         else begin
//             rf_rd_data <= '0;
//             rf_rd_data_valid <= 1'b0;
//         end
//     end
// end

endmodule

