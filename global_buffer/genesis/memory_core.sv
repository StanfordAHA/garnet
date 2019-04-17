/*=============================================================================
** Module: memory_core.sv
** Description:
**              memory core
** Author: Taeyoung Kong
** Change history:  04/10/2019 - Implement first version of memory core
**===========================================================================*/

module memory_core #(
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 16,
    parameter integer CONFIG_DATA_WIDTH = 32
)
(
    input wire                          clk,
    input wire                          reset,

    input wire                          ren,
    input wire                          wen,

    input wire  [BANK_ADDR_WIDTH-1:0]   addr,
    input wire  [BANK_DATA_WIDTH-1:0]   data_in,
    output wire [BANK_DATA_WIDTH-1:0]   data_out,

    input wire                          config_en,
    input wire                          config_wr,
    input wire                          config_rd,
    input wire  [BANK_ADDR_WIDTH-1:0]   config_addr,
    input wire  [CONFIG_DATA_WIDTH-1:0] config_wr_data,
    output wire [CONFIG_DATA_WIDTH-1:0] config_rd_data
);

//===========================================================================//
// local parameter declaration
//===========================================================================//
localparam integer ADDR_OFFSET = $clog2(BANK_DATA_WIDTH/8);

//===========================================================================//
// memory-SRAM interface signal declaration
//===========================================================================//
wire                                    sram_to_mem_cen;
wire                                    sram_to_mem_wen;
wire [BANK_ADDR_WIDTH-ADDR_OFFSET-1:0]  sram_to_mem_addr;
wire [BANK_DATA_WIDTH-1:0]              sram_to_mem_data;
wire [BANK_DATA_WIDTH-1:0]              mem_to_sram_data;

//===========================================================================//
// memory instantiation
//===========================================================================//
memory #(
    .WIDTH(BANK_DATA_WIDTH),
    .ADDR_WIDTH(BANK_ADDR_WIDTH-ADDR_OFFSET)
)
inst_memory_0 (
    .clk(clk),
    .clk_en(sram_to_mem_cen),
    .wen(sram_to_mem_wen),
    .addr(sram_to_mem_addr),
    .data_in(sram_to_mem_data),
    .data_out(mem_to_sram_data)
);

//===========================================================================//
// SRAM controller instantiation
//===========================================================================//
sram_controller #(
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .CONFIG_DATA_WIDTH(CONFIG_DATA_WIDTH)
)
inst_sram_controller (
    .clk(clk),
    .reset(reset),

    .ren(ren),
    .wen(wen),

    .addr(addr),
    .data_in(data_in),
    .data_out(data_out),

    .config_en(config_en),
    .config_wr(config_wr),
    .config_rd(config_rd),
    .config_addr(config_addr),
    .config_wr_data(config_wr_data),
    .config_rd_data(config_rd_data),

    .sram_to_mem_data(sram_to_mem_data),
    .sram_to_mem_cen(sram_to_mem_cen),
    .sram_to_mem_wen(sram_to_mem_wen),
    .sram_to_mem_addr(sram_to_mem_addr),
    .mem_to_sram_data(mem_to_sram_data)
);

endmodule
