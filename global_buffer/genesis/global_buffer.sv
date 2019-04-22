/*=============================================================================
** Module: global_buffer.sv
** Description:
**              Global Buffer
** Author: Taeyoung Kong
** Change history: 04/12/2019 - Implement first version of global buffer
**                 04/18/2019 - Add interconnect between host and banks
**                 04/20/2019 - Add interconnect between io and banks
**                            - Add interconnect between configuration 
**                              and banks
**===========================================================================*/

module global_buffer #(
    parameter integer NUM_BANKS = 32,
    parameter integer NUM_COLS = 32,
    parameter integer NUM_IO_CHANNELS = 8,
    parameter integer NUM_CFG_CHANNELS = 8,
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 17,
    parameter integer CGRA_DATA_WIDTH = 16,
    parameter integer TOP_CFG_ADDR_WIDTH = 12,
    parameter integer TOP_CFG_TILE_WIDTH = 4,
    parameter integer TOP_CFG_FEATURE_WIDTH = 4,
    parameter integer CFG_ADDR_WIDTH = 32,
    parameter integer CFG_DATA_WIDTH = 32
)
(
    input                           clk,
    input                           reset,

    input                           host_wr_en,
    input  [GLB_ADDR_WIDTH-1:0]     host_wr_addr,
    input  [BANK_DATA_WIDTH-1:0]    host_wr_data,

    input                           host_rd_en,
    input  [GLB_ADDR_WIDTH-1:0]     host_rd_addr,
    output [BANK_DATA_WIDTH-1:0]    host_rd_data,

    input                           cgra_to_io_stall [NUM_IO_CHANNELS-1:0],
    input                           cgra_to_io_wr_en [NUM_IO_CHANNELS-1:0],
    input                           cgra_to_io_rd_en [NUM_IO_CHANNELS-1:0],
    output                          io_to_cgra_rd_data_valid [NUM_IO_CHANNELS-1:0],
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_wr_data [NUM_IO_CHANNELS-1:0],
    output [CGRA_DATA_WIDTH-1:0]    io_to_cgra_rd_data [NUM_IO_CHANNELS-1:0],
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_addr_high [NUM_IO_CHANNELS-1:0],
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_addr_low [NUM_IO_CHANNELS-1:0],

    output                          glb_to_cgra_cfg_wr [NUM_COLS-1:0],
    output [CFG_ADDR_WIDTH-1:0]     glb_to_cgra_cfg_addr [NUM_COLS-1:0],
    output [CFG_DATA_WIDTH-1:0]     glb_to_cgra_cfg_data [NUM_COLS-1:0],

    input                           glc_to_io_stall,
    input                           glc_to_cgra_cfg_wr,
    input  [CFG_ADDR_WIDTH-1:0]     glc_to_cgra_cfg_addr,
    input  [CFG_DATA_WIDTH-1:0]     glc_to_cgra_cfg_data,

    input                           cgra_start_pulse,
    input                           config_start_pulse,
    output                          config_done_pulse,

    input                           glb_config_wr,
    input                           glb_config_rd,
    input                           top_config_wr,
    input                           top_config_rd,
    input  [CFG_ADDR_WIDTH-1:0]     top_config_addr,
    input  [CFG_DATA_WIDTH-1:0]     top_config_wr_data,
    output [CFG_DATA_WIDTH-1:0]     top_config_rd_data
);

//============================================================================//
// local parameter declaration
//============================================================================//
localparam integer NUM_BANKS_WIDTH = $clog2(NUM_BANKS);
localparam integer TILE_CFG_ADDR_WIDTH = TOP_CFG_ADDR_WIDTH-TOP_CFG_TILE_WIDTH;
localparam integer GLB_ADDR_WIDTH = NUM_BANKS_WIDTH + BANK_ADDR_WIDTH;

//============================================================================//
// global buffer configuration signal 
//============================================================================//
reg                         top_config_en_bank [NUM_BANKS-1:0];
wire [BANK_ADDR_WIDTH-1:0]  top_config_addr_bank;
wire [CFG_DATA_WIDTH-1:0]   top_config_rd_data_bank [NUM_BANKS-1:0];
reg [CFG_DATA_WIDTH-1:0]    top_config_rd_data_glb;

assign top_config_addr_bank = top_config_addr[BANK_ADDR_WIDTH-1:0];

integer j;
always_comb begin
    for (j=0; j<NUM_BANKS; j=j+1) begin
        top_config_en_bank[j] = (j == top_config_addr[BANK_ADDR_WIDTH +: NUM_BANKS_WIDTH]);
    end
end

always_comb begin       
    top_config_rd_data_glb = {CFG_DATA_WIDTH{1'b0}};
    for (j=0; j<NUM_BANKS; j=j+1) begin
    	top_config_rd_data_glb = top_config_rd_data_glb | top_config_rd_data_bank[j];
    end
end

//============================================================================//
// top configuration signal 
//============================================================================//
enum reg [TOP_CFG_TILE_WIDTH-1:0] {TOP_CONFIG_IO=1, TOP_CONFIG_CFG=2} top_config_tile_addr;
assign top_config_tile_addr = top_config_addr[TOP_CFG_ADDR_WIDTH-1 -: TOP_CFG_TILE_WIDTH];

reg                             top_config_en_io;
reg                             top_config_en_cfg;
wire [TILE_CFG_ADDR_WIDTH-1:0]  top_config_addr_io;
wire [TILE_CFG_ADDR_WIDTH-1:0]  top_config_addr_cfg;
wire [CFG_DATA_WIDTH-1:0]       top_config_rd_data_io;
wire [CFG_DATA_WIDTH-1:0]       top_config_rd_data_cfg;

assign top_config_en_io = (top_config_tile_addr == TOP_CONFIG_IO);
assign top_config_en_cfg = (top_config_tile_addr == TOP_CONFIG_CFG);
assign top_config_addr_io = top_config_addr[TILE_CFG_ADDR_WIDTH-1:0];
assign top_config_addr_cfg = top_config_addr[TILE_CFG_ADDR_WIDTH-1:0];

always_comb begin
    if (glb_config_rd) begin
        top_config_rd_data = top_config_rd_data_glb;
    end
    else if (top_config_rd && top_config_en_io) begin
        top_config_rd_data = top_config_rd_data_io;
    end
    else if (top_config_rd && top_config_en_cfg) begin
        top_config_rd_data = top_config_rd_data_cfg;
    end
    else begin
        top_config_rd_data = 0;
    end
end

//============================================================================//
// internal wire declaration
//============================================================================//
wire                        host_to_bank_wr_en [NUM_BANKS-1:0];
wire [BANK_DATA_WIDTH-1:0]  host_to_bank_wr_data [NUM_BANKS-1:0];
wire [BANK_ADDR_WIDTH-1:0]  host_to_bank_wr_addr [NUM_BANKS-1:0];

wire                        host_to_bank_rd_en [NUM_BANKS-1:0];
wire [BANK_DATA_WIDTH-1:0]  bank_to_host_rd_data [NUM_BANKS-1:0];
wire [BANK_ADDR_WIDTH-1:0]  host_to_bank_rd_addr [NUM_BANKS-1:0];

//============================================================================//
// host-bank interconnect
//============================================================================//
host_bank_interconnect #(
    .NUM_BANKS(NUM_BANKS),
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH)
) inst_host_bank_interconnect (
    .clk(clk),

    .host_wr_en(host_wr_en),
    .host_wr_data(host_wr_data),
    .host_wr_addr(host_wr_addr),

    .host_rd_en(host_rd_en),
    .host_rd_addr(host_rd_addr),
    .host_rd_data(host_rd_data),

    .host_to_bank_wr_en(host_to_bank_wr_en),
    .host_to_bank_wr_data(host_to_bank_wr_data),
    .host_to_bank_wr_addr(host_to_bank_wr_addr),

    .host_to_bank_rd_en(host_to_bank_rd_en),
    .host_to_bank_rd_addr(host_to_bank_rd_addr),
    .bank_to_host_rd_data(bank_to_host_rd_data)
);

//============================================================================//
// bank generation
//============================================================================//
genvar i;
generate
for (i=0; i<NUM_BANKS; i=i+1) begin: generate_bank
    memory_bank #(
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .CONFIG_DATA_WIDTH(CFG_DATA_WIDTH)
    ) inst_bank (
        .clk(clk),
        .reset(reset),

        .host_wr_en(host_to_bank_wr_en[i]),
        .host_wr_data(host_to_bank_wr_data[i]),
        .host_wr_addr(host_to_bank_wr_addr[i]),

        .host_rd_en(host_to_bank_rd_en[i]),
        .host_rd_data(bank_to_host_rd_data[i]),
        .host_rd_addr(host_to_bank_rd_addr[i]),

        .cgra_wr_en(io_to_bank_wr_en[i]),
        .cgra_wr_data(io_to_bank_wr_data[i]),
        .cgra_wr_addr(io_to_bank_wr_addr[i]),

        .cgra_rd_en(io_to_bank_rd_en[i]),
        .cgra_rd_data(bank_to_io_rd_data[i]),
        .cgra_rd_addr(io_to_bank_rd_addr[i]),

        .cfg_rd_en(cfg_to_bank_rd_en[i]),
        .cfg_rd_data(bank_to_cfg_rd_data[i]),
        .cfg_rd_addr(cfg_to_bank_rd_addr[i]),

        .config_en(top_config_en_bank[i]),
        .config_wr(glb_config_wr),
        .config_rd(glb_config_rd),
        .config_addr(top_config_addr_bank),
        .config_wr_data(top_config_wr_data),
        .config_rd_data(top_config_rd_data_bank[i])
    );
end: generate_bank
endgenerate

//============================================================================//
// internal wire declaration
//============================================================================//
wire                        io_to_bank_wr_en [NUM_BANKS-1:0];
wire [BANK_DATA_WIDTH-1:0]  io_to_bank_wr_data [NUM_BANKS-1:0];
wire [BANK_ADDR_WIDTH-1:0]  io_to_bank_wr_addr [NUM_BANKS-1:0];

wire                        io_to_bank_rd_en [NUM_BANKS-1:0];
wire [BANK_DATA_WIDTH-1:0]  bank_to_io_rd_data [NUM_BANKS-1:0];
wire [BANK_ADDR_WIDTH-1:0]  io_to_bank_rd_addr [NUM_BANKS-1:0];

//============================================================================//
// cgra_io-bank interconnect
//============================================================================//
io_bank_interconnect #(
    .NUM_BANKS(NUM_BANKS),
    .NUM_IO_CHANNELS(NUM_IO_CHANNELS),
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .CGRA_DATA_WIDTH(CGRA_DATA_WIDTH),
    .CONFIG_ADDR_WIDTH(TILE_CFG_ADDR_WIDTH),
    .CONFIG_FEATURE_WIDTH(TOP_CFG_FEATURE_WIDTH),
    .CONFIG_DATA_WIDTH(CFG_DATA_WIDTH)
) inst_io_bank_interconnect (
    .clk(clk),
    .reset(reset),

    .cgra_start_pulse(cgra_start_pulse),

    .glc_to_io_stall(glc_to_io_stall),
    .cgra_to_io_stall(cgra_to_io_stall),
    .cgra_to_io_rd_en(cgra_to_io_rd_en),
    .cgra_to_io_wr_en(cgra_to_io_wr_en),
    .cgra_to_io_addr_high(cgra_to_io_addr_high),
    .cgra_to_io_addr_low(cgra_to_io_addr_low),
    .cgra_to_io_wr_data(cgra_to_io_wr_data),
    .io_to_cgra_rd_data(io_to_cgra_rd_data),
    .io_to_cgra_rd_data_valid(io_to_cgra_rd_data_valid),

    .io_to_bank_wr_en(io_to_bank_wr_en),
    .io_to_bank_wr_data(io_to_bank_wr_data),
    .io_to_bank_wr_addr(io_to_bank_wr_addr),
    .io_to_bank_rd_en(io_to_bank_rd_en),
    .io_to_bank_rd_addr(io_to_bank_rd_addr),
    .bank_to_io_rd_data(bank_to_io_rd_data),

    .config_en(top_config_en_io),
    .config_wr(top_config_wr),
    .config_rd(top_config_rd),
    .config_addr(top_config_addr_io),
    .config_wr_data(top_config_wr_data),
    .config_rd_data(top_config_rd_data_io)
);

//============================================================================//
// internal wire declaration
//============================================================================//
wire                        cfg_to_bank_rd_en [NUM_BANKS-1:0];
wire [BANK_DATA_WIDTH-1:0]  bank_to_cfg_rd_data [NUM_BANKS-1:0];
wire [BANK_ADDR_WIDTH-1:0]  cfg_to_bank_rd_addr [NUM_BANKS-1:0];

//============================================================================//
// cfg-bank interconnect
//============================================================================//
cfg_bank_interconnect #(
    .NUM_BANKS(NUM_BANKS),
    .NUM_COLS(NUM_COLS),
    .NUM_CFG_CHANNELS(NUM_CFG_CHANNELS),
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .CONFIG_ADDR_WIDTH(TILE_CFG_ADDR_WIDTH),
    .CONFIG_FEATURE_WIDTH(TOP_CFG_FEATURE_WIDTH),
    .CONFIG_DATA_WIDTH(CFG_DATA_WIDTH),
    .CFG_ADDR_WIDTH(CFG_ADDR_WIDTH),
    .CFG_DATA_WIDTH(CFG_DATA_WIDTH)
) inst_cfg_bank_interconnect (
    .clk(clk),
    .reset(reset),

    .config_start_pulse(config_start_pulse),
    .config_done_pulse(config_done_pulse),

    .cfg_rd_en(cfg_to_bank_rd_en),
    .cfg_rd_addr(cfg_to_bank_rd_addr),
    .cfg_rd_data(bank_to_cfg_rd_data),

    .glc_to_cgra_cfg_wr(glc_to_cgra_cfg_wr),
    .glc_to_cgra_cfg_addr(glc_to_cgra_cfg_addr),
    .glc_to_cgra_cfg_data(glc_to_cgra_cfg_data),

    .glb_to_cgra_cfg_wr(glb_to_cgra_cfg_wr),
    .glb_to_cgra_cfg_addr(glb_to_cgra_cfg_addr),
    .glb_to_cgra_cfg_data(glb_to_cgra_cfg_data),

    .config_en(top_config_en_cfg),
    .config_wr(top_config_wr),
    .config_rd(top_config_rd),
    .config_addr(top_config_addr_cfg),
    .config_wr_data(top_config_wr_data),
    .config_rd_data(top_config_rd_data_cfg)
);

endmodule
