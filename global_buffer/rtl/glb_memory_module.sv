module glb_memory_module #(
    parameter DATA_WIDTH=64,
    parameter ADDR_WIDTH=14
)
(
    input logic                   clk,
    input logic                   clk_en,
    input logic                   wen,
    input logic [DATA_WIDTH-1:0]  data_in,
    input logic [DATA_WIDTH-1:0]  bit_sel,
    input logic [ADDR_WIDTH-1:0]  addr,
    output logic [DATA_WIDTH-1:0] data_out
);


glb_sram_gen #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH)
) glb_sram_gen_inst (
    .Q(data_out),
    .CLK(clk),
    .CEB(~clk_en), 
    .WEB(~wen), 
    .BWEB(~bit_sel), 
    .A(addr), 
    .D(data_in)
);


endmodule
