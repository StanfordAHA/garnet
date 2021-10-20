module cgra (
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

logic        io1_io2f [NUM_PRR];
logic [15:0] io16_io2f [NUM_PRR];
logic        io1_f2io [NUM_PRR];
logic [15:0] io16_f2io [NUM_PRR];

genvar i;
generate
for (i = 0; i < NUM_PRR; i++) begin: prr
    logic [NUM_PRR_WIDTH-1:0] prr_id;
    assign prr_id = i;
    prr prr (
        .prr_id      ( prr_id         ),
        .stall       ( stall[i]       ),
        .cfg_wr_en   ( cfg_wr_en[i]   ),
        .cfg_wr_addr ( cfg_wr_addr[i] ),
        .cfg_wr_data ( cfg_wr_data[i] ),
        .cfg_rd_en   ( cfg_rd_en[i]   ),
        .cfg_rd_addr ( cfg_rd_addr[i] ),
        .cfg_rd_data ( cfg_rd_data[i] ),
        .io1_g2io    ( io1_g2io[i]    ),
        .io16_g2io   ( io16_g2io[i]   ),
        .io1_io2f    ( io1_io2f[i]    ),
        .io16_io2f   ( io16_io2f[i]   ),
        .io1_f2io    ( io1_f2io[i]    ),
        .io16_f2io   ( io16_f2io[i]   ),
        .io1_io2g    ( io1_io2g[i]    ),
        .io16_io2g   ( io16_io2g[i]   ),
        .*
    );
end
endgenerate

noc noc (
    .clk        (clk),
    .reset      (reset),
    .io1_io2f   (io1_io2f),
    .io16_io2f  (io16_io2f),
    .io1_f2io   (io1_f2io),
    .io16_f2io  (io16_f2io)
);

endmodule
