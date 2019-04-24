module global_buffer_flatten #(
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
    input                                           clk,
    input                                           reset,

    input                                           host_wr_en,
    input  [BANK_DATA_WIDTH-1:0]                    host_wr_data,
    input  [GLB_ADDR_WIDTH-1:0]                     host_wr_addr,

    input                                           host_rd_en,
    output [BANK_DATA_WIDTH-1:0]                    host_rd_data,
    input  [GLB_ADDR_WIDTH-1:0]                     host_rd_addr,

    //input  [NUM_IO_CHANNELS-1:0]                    cgra_to_io_stall,
    input  [NUM_IO_CHANNELS-1:0]                    cgra_to_io_wr_en,
    input  [NUM_IO_CHANNELS-1:0]                    cgra_to_io_rd_en,
    output [NUM_IO_CHANNELS-1:0]                    io_to_cgra_rd_data_valid,
    input  [CGRA_DATA_WIDTH*NUM_IO_CHANNELS-1:0]    cgra_to_io_wr_data,
    output [CGRA_DATA_WIDTH*NUM_IO_CHANNELS-1:0]    io_to_cgra_rd_data,
    input  [CGRA_DATA_WIDTH*NUM_IO_CHANNELS-1:0]    cgra_to_io_addr_high,
    input  [CGRA_DATA_WIDTH*NUM_IO_CHANNELS-1:0]    cgra_to_io_addr_low,

    output [NUM_COLS-1:0]                           glb_to_cgra_cfg_wr,
    output [CFG_ADDR_WIDTH*NUM_COLS-1:0]            glb_to_cgra_cfg_addr,
    output [CFG_DATA_WIDTH*NUM_COLS-1:0]            glb_to_cgra_cfg_data,

    input                                           glc_to_io_stall,
    input                                           glc_to_cgra_cfg_wr,
    input  [CFG_ADDR_WIDTH-1:0]                     glc_to_cgra_cfg_addr,
    input  [CFG_DATA_WIDTH-1:0]                     glc_to_cgra_cfg_data,

    input                                           cgra_start_pulse,
    input                                           config_start_pulse,
    output                                          config_done_pulse,

    input                                           glb_config_wr,
    input                                           glb_config_rd,
    input  [CFG_ADDR_WIDTH-1:0]                     glb_config_addr,
    input  [CFG_DATA_WIDTH-1:0]                     glb_config_wr_data,
    output [CFG_DATA_WIDTH-1:0]                     glb_config_rd_data,

    input                                           top_config_wr,
    input                                           top_config_rd,
    input  [TOP_CFG_ADDR_WIDTH-1:0]                 top_config_addr,
    input  [CFG_DATA_WIDTH-1:0]                     top_config_wr_data,
    output [CFG_DATA_WIDTH-1:0]                     top_config_rd_data
);

//============================================================================//
// local parameter declaration
//============================================================================//
localparam integer NUM_BANKS_WIDTH = $clog2(NUM_BANKS);
localparam integer GLB_ADDR_WIDTH = NUM_BANKS_WIDTH + BANK_ADDR_WIDTH;

//============================================================================//
// signal connection
//============================================================================//
//wire                          int_cgra_to_io_stall [NUM_IO_CHANNELS-1:0];
reg                         int_cgra_to_io_wr_en [NUM_IO_CHANNELS-1:0];
reg                         int_cgra_to_io_rd_en [NUM_IO_CHANNELS-1:0];
reg                         int_io_to_cgra_rd_data_valid [NUM_IO_CHANNELS-1:0];
reg  [CGRA_DATA_WIDTH-1:0]  int_cgra_to_io_wr_data[NUM_IO_CHANNELS-1:0];
reg  [CGRA_DATA_WIDTH-1:0]  int_io_to_cgra_rd_data[NUM_IO_CHANNELS-1:0];
reg  [CGRA_DATA_WIDTH-1:0]  int_cgra_to_io_addr_high[NUM_IO_CHANNELS-1:0];
reg  [CGRA_DATA_WIDTH-1:0]  int_cgra_to_io_addr_low[NUM_IO_CHANNELS-1:0];

integer i;
always_comb begin
    for (i=0; i<NUM_IO_CHANNELS; i=i+1) begin
        //assign int_cgra_to_io_stall[i] = cgra_to_io_stall[i];
        int_cgra_to_io_wr_en[i] = cgra_to_io_wr_en[i];
        int_cgra_to_io_rd_en[i] = cgra_to_io_rd_en[i];
        io_to_cgra_rd_data_valid[i] = int_io_to_cgra_rd_data_valid[i];
        int_cgra_to_io_wr_data[i] = cgra_to_io_wr_data[i*CGRA_DATA_WIDTH +: CGRA_DATA_WIDTH];
        io_to_cgra_rd_data[i*CGRA_DATA_WIDTH +: CGRA_DATA_WIDTH] = int_io_to_cgra_rd_data[i];
        int_cgra_to_io_addr_high[i] = cgra_to_io_addr_high[i*CGRA_DATA_WIDTH +: CGRA_DATA_WIDTH];
        int_cgra_to_io_addr_low[i] = cgra_to_io_addr_low[i*CGRA_DATA_WIDTH +: CGRA_DATA_WIDTH];
    end
end

wire                      int_glb_to_cgra_cfg_wr [NUM_COLS-1:0];
wire [CFG_ADDR_WIDTH-1:0] int_glb_to_cgra_cfg_addr [NUM_COLS-1:0];
wire [CFG_DATA_WIDTH-1:0] int_glb_to_cgra_cfg_data [NUM_COLS-1:0];

integer j;
always_comb begin
    for (j=0; j<NUM_COLS; j=j+1) begin
        glb_to_cgra_cfg_wr[j] = int_glb_to_cgra_cfg_wr[j];
        glb_to_cgra_cfg_addr[j*CFG_ADDR_WIDTH +: CFG_ADDR_WIDTH] = int_glb_to_cgra_cfg_addr[j];
        glb_to_cgra_cfg_data[j*CFG_DATA_WIDTH +: CFG_DATA_WIDTH] = int_glb_to_cgra_cfg_data[j];
    end
end


global_buffer #(
    .NUM_BANKS(NUM_BANKS),
    .NUM_COLS(NUM_COLS),
    .NUM_IO_CHANNELS(NUM_IO_CHANNELS),
    .NUM_CFG_CHANNELS(NUM_CFG_CHANNELS),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .CGRA_DATA_WIDTH(CGRA_DATA_WIDTH),
    .TOP_CFG_ADDR_WIDTH(TOP_CFG_ADDR_WIDTH),
    .TOP_CFG_TILE_WIDTH(TOP_CFG_TILE_WIDTH),
    .TOP_CFG_FEATURE_WIDTH(TOP_CFG_FEATURE_WIDTH),
    .CFG_ADDR_WIDTH(CFG_ADDR_WIDTH),
    .CFG_DATA_WIDTH(CFG_DATA_WIDTH)
) inst_global_buffer
(
    .clk(clk),
    .reset(reset),

    .host_wr_en(host_wr_en),
    .host_wr_data(host_wr_data),
    .host_wr_addr(host_wr_addr),

    .host_rd_en(host_rd_en),
    .host_rd_data(host_rd_data),
    .host_rd_addr(host_rd_addr),

    //.cgra_to_io_stall(int_cgra_to_io_stall),
    .cgra_to_io_wr_en(int_cgra_to_io_wr_en),
    .cgra_to_io_rd_en(int_cgra_to_io_rd_en),
    .io_to_cgra_rd_data_valid(int_io_to_cgra_rd_data_valid),
    .cgra_to_io_wr_data(int_cgra_to_io_wr_data),
    .io_to_cgra_rd_data(int_io_to_cgra_rd_data),
    .cgra_to_io_addr_high(int_cgra_to_io_addr_high),
    .cgra_to_io_addr_low(int_cgra_to_io_addr_low),

    .glb_to_cgra_cfg_wr(int_glb_to_cgra_cfg_wr),
    .glb_to_cgra_cfg_addr(int_glb_to_cgra_cfg_addr),
    .glb_to_cgra_cfg_data(int_glb_to_cgra_cfg_data),

    .glc_to_io_stall(glc_to_io_stall),
    .glc_to_cgra_cfg_wr(glc_to_cgra_cfg_wr),
    .glc_to_cgra_cfg_addr(glc_to_cgra_cfg_addr),
    .glc_to_cgra_cfg_data(glc_to_cgra_cfg_data),

    .cgra_start_pulse(cgra_start_pulse),
    .config_start_pulse(config_start_pulse),
    .config_done_pulse(config_done_pulse),
    
    .glb_config_wr(glb_config_wr),
    .glb_config_rd(glb_config_rd),
    .glb_config_addr(glb_config_addr),
    .glb_config_wr_data(glb_config_wr_data),
    .glb_config_rd_data(glb_config_rd_data),

    .top_config_wr(top_config_wr),
    .top_config_rd(top_config_rd),
    .top_config_addr(top_config_addr),
    .top_config_wr_data(top_config_wr_data),
    .top_config_rd_data(top_config_rd_data)
);

endmodule
