/*=============================================================================
** Module: global_buffer.sv
** Description:
**              Global Buffer
** Author: Taeyoung Kong
** Change history: 10/08/2019 - Implement first version of global buffer
**===========================================================================*/
import global_buffer_pkg::*;

module global_buffer (
    input                                   clk,
    input                                   reset,

    input        [BANK_DATA_WIDTH/8-1:0]    host_wr_strb,
    input        [GLB_ADDR_WIDTH-1:0]       host_wr_addr,
    input        [BANK_DATA_WIDTH-1:0]      host_wr_data,

    input                                   host_rd_en,
    input        [GLB_ADDR_WIDTH-1:0]       host_rd_addr,
    output logic [BANK_DATA_WIDTH-1:0]      host_rd_data,

    //input                                   cgra_to_io_stall [`$num_io_channels-1`:0],
    input                                   cgra_to_io_wr_en [`$num_io_channels-1`:0],
    input                                   cgra_to_io_rd_en [`$num_io_channels-1`:0],
    output logic                            io_to_cgra_rd_data_valid [`$num_io_channels-1`:0],
    input        [CGRA_DATA_WIDTH-1:0]      cgra_to_io_wr_data [`$num_io_channels-1`:0],
    output logic [CGRA_DATA_WIDTH-1:0]      io_to_cgra_rd_data [`$num_io_channels-1`:0],
    input        [CGRA_DATA_WIDTH-1:0]      cgra_to_io_addr_high [`$num_io_channels-1`:0],
    input        [CGRA_DATA_WIDTH-1:0]      cgra_to_io_addr_low [`$num_io_channels-1`:0],

    input                                   glc_to_cgra_cfg_wr,
    input                                   glc_to_cgra_cfg_rd,
    input        [CFG_ADDR_WIDTH-1:0]       glc_to_cgra_cfg_addr,
    input        [CFG_DATA_WIDTH-1:0]       glc_to_cgra_cfg_data,

    output logic                            glb_to_cgra_cfg_wr [`$num_cfg_channels-1`:0],
    output logic                            glb_to_cgra_cfg_rd [`$num_cfg_channels-1`:0],
    output logic [CFG_ADDR_WIDTH-1:0]       glb_to_cgra_cfg_addr [`$num_cfg_channels-1`:0],
    output logic [CFG_DATA_WIDTH-1:0]       glb_to_cgra_cfg_data [`$num_cfg_channels-1`:0],

    input                                   glc_to_io_stall,
    input                                   cgra_start_pulse,
    output logic                            cgra_done_pulse,
    input                                   config_start_pulse,
    output logic                            config_done_pulse,

    input                                   glb_config_wr,
    input                                   glb_config_rd,
    input        [GLB_CFG_ADDR_WIDTH-1:0]   glb_config_addr,
    input        [CFG_DATA_WIDTH-1:0]       glb_config_wr_data,
    output logic [CFG_DATA_WIDTH-1:0]       glb_config_rd_data,

    input                                   glb_sram_config_wr,
    input                                   glb_sram_config_rd,
    input        [CFG_ADDR_WIDTH-1:0]       glb_sram_config_addr,
    input        [CFG_DATA_WIDTH-1:0]       glb_sram_config_wr_data,
    output logic [CFG_DATA_WIDTH-1:0]       glb_sram_config_rd_data
);

//============================================================================//
// global buffer sram configuration signal 
//============================================================================//
logic                                       glb_sram_config_en_bank [`$num_banks-1`:0];
logic [BANK_ADDR_WIDTH-1:0]                 glb_sram_config_addr_bank;
logic [CFG_ADDR_WIDTH-BANK_ADDR_WIDTH-1:0]  glb_sram_config_bank_sel;
logic [CFG_DATA_WIDTH-1:0]                  glb_sram_config_rd_data_bank [`$num_banks-1`:0];

assign glb_sram_config_addr_bank = glb_sram_config_addr[BANK_ADDR_WIDTH-1:0];
assign glb_sram_config_bank_sel = glb_sram_config_addr[CFG_ADDR_WIDTH-1: BANK_ADDR_WIDTH];

integer j;
always_comb begin
    for (j=0; j<`$num_banks`; j=j+1) begin
        glb_sram_config_en_bank[j] = (j == glb_sram_config_bank_sel);
    end
end

always_comb begin       
    if (glb_sram_config_rd) begin
        glb_sram_config_rd_data = glb_sram_config_rd_data_bank[glb_sram_config_bank_sel];
    end
    else begin
        glb_sram_config_rd_data = 0;
    end
end

//============================================================================//
// global buffer configuration signal 
//============================================================================//
localparam bit [GLB_CFG_TILE_WIDTH-1:0]
    GLB_CONFIG_IO = 1,
    GLB_CONFIG_CFG = 2;
localparam integer GLB_CFG_FEATURE_REG_WIDTH = GLB_CFG_FEATURE_WIDTH+GLB_CFG_REG_WIDTH;
localparam integer GLB_CFG_BYTE_OFFSET = $clog2(CFG_DATA_WIDTH/8);

logic [GLB_CFG_TILE_WIDTH-1:0]          glb_config_tile_addr;
logic                                   glb_config_en_io;
logic                                   glb_config_en_cfg;
logic [GLB_CFG_FEATURE_REG_WIDTH-1:0]   glb_config_addr_io;
logic [GLB_CFG_FEATURE_REG_WIDTH-1:0]   glb_config_addr_cfg;
logic [CFG_DATA_WIDTH-1:0]              glb_config_rd_data_io;
logic [CFG_DATA_WIDTH-1:0]              glb_config_rd_data_cfg;

assign glb_config_tile_addr = glb_config_addr[GLB_CFG_BYTE_OFFSET+GLB_CFG_FEATURE_REG_WIDTH +: GLB_CFG_TILE_WIDTH];
assign glb_config_en_io = (glb_config_tile_addr == GLB_CONFIG_IO);
assign glb_config_en_cfg = (glb_config_tile_addr == GLB_CONFIG_CFG);
assign glb_config_addr_io = glb_config_addr[GLB_CFG_BYTE_OFFSET +: GLB_CFG_FEATURE_REG_WIDTH];
assign glb_config_addr_cfg = glb_config_addr[GLB_CFG_BYTE_OFFSET +: GLB_CFG_FEATURE_REG_WIDTH];

always_comb begin       
    if (glb_config_rd && glb_config_en_io) begin
        glb_config_rd_data = glb_config_rd_data_io;
    end
    else if (glb_config_rd && glb_config_en_cfg) begin
        glb_config_rd_data = glb_config_rd_data_cfg;
    end
    else begin
        glb_config_rd_data = 0;
    end
end

//============================================================================//
// internal wire declaration
//============================================================================//
wire                        host_wr_en;
wire                        host_to_bank_wr_en [`$num_banks-1`:0];
wire [BANK_DATA_WIDTH-1:0]  host_to_bank_wr_data [`$num_banks-1`:0];
wire [BANK_DATA_WIDTH-1:0]  host_to_bank_wr_data_bit_sel [`$num_banks-1`:0];
wire [BANK_ADDR_WIDTH-1:0]  host_to_bank_wr_addr [`$num_banks-1`:0];

wire                        host_to_bank_rd_en [`$num_banks-1`:0];
wire [BANK_DATA_WIDTH-1:0]  bank_to_host_rd_data [`$num_banks-1`:0];
wire [BANK_ADDR_WIDTH-1:0]  host_to_bank_rd_addr [`$num_banks-1`:0];

assign host_wr_en = |host_wr_strb;

//============================================================================//
// host-bank interconnect
//============================================================================//
//; my $host_bank_interconnect = generate_base('host_bank_interconnect', 'host_bank_interconnect',
//;                                            "num_banks"=>$num_banks);
`$host_bank_interconnect->mname()` #(
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .GLB_ADDR_WIDTH(GLB_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH)
) `$host_bank_interconnect->iname()` (
    .clk(clk),
    .reset(reset),

    .host_wr_en(host_wr_en),
    .host_wr_strb(host_wr_strb),
    .host_wr_data(host_wr_data),
    .host_wr_addr(host_wr_addr),

    .host_rd_en(host_rd_en),
    .host_rd_addr(host_rd_addr),
    .host_rd_data(host_rd_data),

    .host_to_bank_wr_en(host_to_bank_wr_en),
    .host_to_bank_wr_data(host_to_bank_wr_data),
    .host_to_bank_wr_data_bit_sel(host_to_bank_wr_data_bit_sel),
    .host_to_bank_wr_addr(host_to_bank_wr_addr),

    .host_to_bank_rd_en(host_to_bank_rd_en),
    .host_to_bank_rd_addr(host_to_bank_rd_addr),
    .bank_to_host_rd_data(bank_to_host_rd_data)
);

//============================================================================//
// internal wire declaration
//============================================================================//
wire                        io_to_bank_wr_en [`$num_banks-1`:0];
wire [BANK_DATA_WIDTH-1:0]  io_to_bank_wr_data [`$num_banks-1`:0];
wire [BANK_DATA_WIDTH-1:0]  io_to_bank_wr_data_bit_sel [`$num_banks-1`:0];
wire [BANK_ADDR_WIDTH-1:0]  io_to_bank_wr_addr [`$num_banks-1`:0];

wire                        io_to_bank_rd_en [`$num_banks-1`:0];
wire [BANK_DATA_WIDTH-1:0]  bank_to_io_rd_data [`$num_banks-1`:0];
wire [BANK_ADDR_WIDTH-1:0]  io_to_bank_rd_addr [`$num_banks-1`:0];

wire                        cfg_to_bank_rd_en [`$num_banks-1`:0];
wire [BANK_DATA_WIDTH-1:0]  bank_to_cfg_rd_data [`$num_banks-1`:0];
wire [BANK_ADDR_WIDTH-1:0]  cfg_to_bank_rd_addr [`$num_banks-1`:0];

//============================================================================//
// bank generation
//============================================================================//
//; my $memory_bank = generate_base('memory_bank', 'memory_bank');
//; for(my $i=0; $i<$num_banks; $i++) {
//; $memory_bank = clone($memory_bank, "memory_bank_${i}");
`$memory_bank->mname()` #(
.BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
.BANK_DATA_WIDTH(BANK_DATA_WIDTH),
.CONFIG_DATA_WIDTH(CFG_DATA_WIDTH)
) `$memory_bank->iname()` (
    .clk(clk),
    .reset(reset),

    .host_wr_en(host_to_bank_wr_en[`$i`]),
    .host_wr_data(host_to_bank_wr_data[`$i`]),
    .host_wr_data_bit_sel(host_to_bank_wr_data_bit_sel[`$i`]),
    .host_wr_addr(host_to_bank_wr_addr[`$i`]),

    .host_rd_en(host_to_bank_rd_en[`$i`]),
    .host_rd_data(bank_to_host_rd_data[`$i`]),
    .host_rd_addr(host_to_bank_rd_addr[`$i`]),

    .cgra_wr_en(io_to_bank_wr_en[`$i`]),
    .cgra_wr_data(io_to_bank_wr_data[`$i`]),
    .cgra_wr_data_bit_sel(io_to_bank_wr_data_bit_sel[`$i`]),
    .cgra_wr_addr(io_to_bank_wr_addr[`$i`]),

    .cgra_rd_en(io_to_bank_rd_en[`$i`]),
    .cgra_rd_data(bank_to_io_rd_data[`$i`]),
    .cgra_rd_addr(io_to_bank_rd_addr[`$i`]),

    .cfg_rd_en(cfg_to_bank_rd_en[`$i`]),
    .cfg_rd_data(bank_to_cfg_rd_data[`$i`]),
    .cfg_rd_addr(cfg_to_bank_rd_addr[`$i`]),

    .config_en(glb_sram_config_en_bank[`$i`]),
    .config_wr(glb_sram_config_wr),
    .config_rd(glb_sram_config_rd),
    .config_addr(glb_sram_config_addr_bank),
    .config_wr_data(glb_sram_config_wr_data),
    .config_rd_data(glb_sram_config_rd_data_bank[`$i`])
);

//; }

//============================================================================//
// cgra_io-bank interconnect
//============================================================================//
//; my $io_controller = generate_base('io_controller', 'io_controller',
//;                                               "num_banks"=>$num_banks, "num_io_channels"=>$num_io_channels);
`$io_controller->mname()` #(
    .GLB_ADDR_WIDTH(GLB_ADDR_WIDTH),
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .CGRA_DATA_WIDTH(CGRA_DATA_WIDTH),
    .CONFIG_FEATURE_WIDTH(GLB_CFG_FEATURE_WIDTH),
    .CONFIG_REG_WIDTH(GLB_CFG_REG_WIDTH),
    .CONFIG_DATA_WIDTH(CFG_DATA_WIDTH)
) `$io_controller->iname()` (
    .clk(clk),
    .reset(reset),

    .cgra_start_pulse(cgra_start_pulse),
    .cgra_done_pulse(cgra_done_pulse),

    .glc_to_io_stall(glc_to_io_stall),
    //.cgra_to_io_stall(cgra_to_io_stall),
    .cgra_to_io_rd_en(cgra_to_io_rd_en),
    .cgra_to_io_wr_en(cgra_to_io_wr_en),
    .cgra_to_io_addr_high(cgra_to_io_addr_high),
    .cgra_to_io_addr_low(cgra_to_io_addr_low),
    .cgra_to_io_wr_data(cgra_to_io_wr_data),
    .io_to_cgra_rd_data(io_to_cgra_rd_data),
    .io_to_cgra_rd_data_valid(io_to_cgra_rd_data_valid),

    .io_to_bank_wr_en(io_to_bank_wr_en),
    .io_to_bank_wr_data(io_to_bank_wr_data),
    .io_to_bank_wr_data_bit_sel(io_to_bank_wr_data_bit_sel),
    .io_to_bank_wr_addr(io_to_bank_wr_addr),
    .io_to_bank_rd_en(io_to_bank_rd_en),
    .io_to_bank_rd_addr(io_to_bank_rd_addr),
    .bank_to_io_rd_data(bank_to_io_rd_data),

    .config_en(glb_config_en_io),
    .config_wr(glb_config_wr),
    .config_rd(glb_config_rd),
    .config_addr(glb_config_addr_io),
    .config_wr_data(glb_config_wr_data),
    .config_rd_data(glb_config_rd_data_io)
);


//============================================================================//
// cfg-bank interconnect
//============================================================================//
//; my $cfg_controller = generate_base('cfg_controller', 'cfg_controller',
//;                                           "num_banks"=>$num_banks, "num_cfg_channels"=>$num_cfg_channels);
`$cfg_controller->mname()` #(
    .GLB_ADDR_WIDTH(GLB_ADDR_WIDTH),
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .CONFIG_FEATURE_WIDTH(GLB_CFG_FEATURE_WIDTH),
    .CONFIG_REG_WIDTH(GLB_CFG_REG_WIDTH),
    .CONFIG_DATA_WIDTH(CFG_DATA_WIDTH),
    .CFG_ADDR_WIDTH(CFG_ADDR_WIDTH),
    .CFG_DATA_WIDTH(CFG_DATA_WIDTH)
) `$cfg_controller->iname()` (
    .clk(clk),
    .reset(reset),

    .config_start_pulse(config_start_pulse),
    .config_done_pulse(config_done_pulse),

    .cfg_to_bank_rd_en(cfg_to_bank_rd_en),
    .cfg_to_bank_rd_addr(cfg_to_bank_rd_addr),
    .bank_to_cfg_rd_data(bank_to_cfg_rd_data),

    .glc_to_cgra_cfg_wr(glc_to_cgra_cfg_wr),
    .glc_to_cgra_cfg_rd(glc_to_cgra_cfg_rd),
    .glc_to_cgra_cfg_addr(glc_to_cgra_cfg_addr),
    .glc_to_cgra_cfg_data(glc_to_cgra_cfg_data),

    .glb_to_cgra_cfg_wr(glb_to_cgra_cfg_wr),
    .glb_to_cgra_cfg_rd(glb_to_cgra_cfg_rd),
    .glb_to_cgra_cfg_addr(glb_to_cgra_cfg_addr),
    .glb_to_cgra_cfg_data(glb_to_cgra_cfg_data),

    .config_en(glb_config_en_cfg),
    .config_wr(glb_config_wr),
    .config_rd(glb_config_rd),
    .config_addr(glb_config_addr_cfg),
    .config_wr_data(glb_config_wr_data),
    .config_rd_data(glb_config_rd_data_cfg)
);

endmodule
