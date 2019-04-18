/*=============================================================================
** Module: global_buffer.sv
** Description:
**              Global Buffer
** Author: Taeyoung Kong
** Change history: 04/12/2019 - Implement first version of global buffer
**===========================================================================*/

module global_buffer #(
    parameter integer NUM_BANKS = 32,
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 16,
    parameter integer CONFIG_ADDR_WIDTH = 32,
    parameter integer CONFIG_DATA_WIDTH = 32
)
(
    input                           clk,
    input                           reset,
    
    input                           soc_port_wr_en,
    input  [GLB_ADDR_WIDTH-1:0]     soc_port_wr_addr,
    input  [BANK_DATA_WIDTH-1:0]    soc_port_wr_data,

    input                           soc_port_rd_en,
    input  [GLB_ADDR_WIDTH-1:0]     soc_port_rd_addr,
    output [BANK_DATA_WIDTH-1:0]    soc_port_rd_data,

    input                           cgra_wr_en [NUM_BANKS-1:0],
    input  [BANK_ADDR_WIDTH-1:0]    cgra_wr_addr [NUM_BANKS-1:0],
    input  [BANK_DATA_WIDTH-1:0]    cgra_wr_data [NUM_BANKS-1:0],

    input                           cgra_rd_en [NUM_BANKS-1:0],
    input  [BANK_ADDR_WIDTH-1:0]    cgra_rd_addr [NUM_BANKS-1:0],
    output [BANK_DATA_WIDTH-1:0]    cgra_rd_data [NUM_BANKS-1:0],

    input                           top_config_en_glb,
    input                           top_config_wr,
    input                           top_config_rd,
    input  [CONFIG_ADDR_WIDTH-1:0]  top_config_addr,
    input  [CONFIG_DATA_WIDTH-1:0]  top_config_wr_data,
    output [CONFIG_DATA_WIDTH-1:0]  top_config_rd_data
);

//============================================================================//
// local parameter declaration
//============================================================================//
localparam integer NUM_BANKS_WIDTH = $clog2(NUM_BANKS);
localparam integer GLB_ADDR_WIDTH = NUM_BANKS_WIDTH + BANK_ADDR_WIDTH;

//============================================================================//
// configuration signal declaration
//============================================================================//
reg [BANK_ADDR_WIDTH-1:0]       top_config_addr_bank;
reg                             top_config_en_bank [NUM_BANKS-1:0];
wire [CONFIG_DATA_WIDTH-1:0]    top_config_rd_data_bank [NUM_BANKS-1:0];

assign top_config_addr_bank = top_config_addr[BANK_ADDR_WIDTH-1:0];

integer j;
always_comb begin
    for (j=0; j<NUM_BANKS; j=j+1) begin
        top_config_en_bank[j] = top_config_en_glb && (j == top_config_addr[BANK_ADDR_WIDTH +: NUM_BANKS_WIDTH]);
    end
end

always_comb begin       
    top_config_rd_data = {CONFIG_DATA_WIDTH{1'b0}};
    for (j=0; j<NUM_BANKS; j=j+1) begin
    	top_config_rd_data = top_config_rd_data | top_config_rd_data_bank[j];
    end
end

//============================================================================//
// host-bank interface
//============================================================================//
host_bank_interface #(
    .NUM_BANKS(NUM_BANKS),
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH)
) inst_host_bank_interface (
    .clk(clk),
    .reset(reset),

    .soc_port_wr_en(soc_port_wr_en),
    .soc_port_wr_data(soc_port_wr_data),
    .soc_port_wr_addr(soc_port_wr_addr),

    .soc_port_rd_en(soc_port_rd_en),
    .soc_port_rd_addr(soc_port_rd_addr),
    .soc_port_rd_data(soc_port_rd_data),

    .host_wr_en(host_wr_en),
    .host_wr_data(host_wr_data),
    .host_wr_addr(host_wr_addr),

    .host_rd_en(host_rd_en),
    .host_rd_addr(host_rd_addr),
    .host_rd_data(host_rd_data)
);

//============================================================================//
// internal wire declaration
//============================================================================//
wire                        host_wr_en [NUM_BANKS-1:0];
wire [BANK_DATA_WIDTH-1:0]  host_wr_data [NUM_BANKS-1:0];
wire [BANK_ADDR_WIDTH-1:0]  host_wr_addr [NUM_BANKS-1:0];

wire                        host_rd_en [NUM_BANKS-1:0];
wire [BANK_DATA_WIDTH-1:0]  host_rd_data [NUM_BANKS-1:0];
wire [BANK_ADDR_WIDTH-1:0]  host_rd_addr [NUM_BANKS-1:0];

//============================================================================//
// bank generation
//============================================================================//
genvar i;
generate
for (i=0; i<NUM_BANKS; i=i+1) begin: generate_bank
    memory_bank #(
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .CONFIG_DATA_WIDTH(CONFIG_DATA_WIDTH)
    ) inst_bank (
        .clk(clk),
        .reset(reset),

        .host_wr_en(host_wr_en[i]),
        .host_wr_data(host_wr_data[i]),
        .host_wr_addr(host_wr_addr[i]),

        .host_rd_en(host_rd_en[i]),
        .host_rd_data(host_rd_data[i]),
        .host_rd_addr(host_rd_addr[i]),

        .cgra_wr_en(cgra_wr_en[i]),
        .cgra_wr_data(cgra_wr_data[i]),
        .cgra_wr_addr(cgra_wr_addr[i]),

        .cgra_rd_en(cgra_rd_en[i]),
        .cgra_rd_data(cgra_rd_data[i]),
        .cgra_rd_addr(cgra_rd_addr[i]),

        .config_en(top_config_en_bank[i]),
        .config_wr(top_config_wr),
        .config_rd(top_config_rd),
        .config_addr(top_config_addr_bank),
        .config_wr_data(top_config_wr_data),
        .config_rd_data(top_config_rd_data_bank[i])
    );
end: generate_bank
endgenerate

endmodule
