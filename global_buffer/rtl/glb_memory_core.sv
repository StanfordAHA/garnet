/*=============================================================================
** Module: glb_memory_core.sv
** Description:
**              glb memory core
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of memory core
**===========================================================================*/
import global_buffer_pkg::*;

module glb_memory_core (
    input  logic                            clk,
    input  logic                            reset,

    input  logic                            ren,
    input  logic                            wen,
    input  logic [BANK_ADDR_WIDTH-1:0]      addr,
    input  logic [BANK_DATA_WIDTH-1:0]      data_in,
    input  logic [BANK_DATA_WIDTH-1:0]      data_in_bit_sel,
    output logic [BANK_DATA_WIDTH-1:0]      data_out,

    input  logic                            config_en,
    input  logic                            config_wr,
    input  logic                            config_rd,
    input  logic [BANK_ADDR_WIDTH-1:0]      config_addr,
    input  logic [CONFIG_DATA_WIDTH-1:0]    config_wr_data,
    output logic [CONFIG_DATA_WIDTH-1:0]    config_rd_data
);

//===========================================================================//
// memory-SRAM interface signal declaration
//===========================================================================//
logic                                               sram_to_mem_cen;
logic                                               sram_to_mem_wen;
logic [BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET-1:0]   sram_to_mem_addr;
logic [BANK_DATA_WIDTH-1:0]                         sram_to_mem_data;
logic [BANK_DATA_WIDTH-1:0]                         sram_to_mem_bit_sel;
logic [BANK_DATA_WIDTH-1:0]                         mem_to_sram_data;

//===========================================================================//
// memory instantiation
//===========================================================================//
glb_memory_module #(
    .DATA_WIDTH(BANK_DATA_WIDTH),
    .ADDR_WIDTH(BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET)
) glb_memory_module_inst (
    .clk(clk),
    .clk_en(sram_to_mem_cen),
    .wen(sram_to_mem_wen),
    .addr(sram_to_mem_addr),
    .data_in(sram_to_mem_data),
    .bit_sel(sram_to_mem_bit_sel),
    .data_out(mem_to_sram_data)
);

//===========================================================================//
// SRAM controller instantiation
//===========================================================================//
glb_sram_controller glb_sram_controller_inst (
    .clk(clk),
    .reset(reset),

    .ren(ren),
    .wen(wen),

    .addr(addr),
    .data_in(data_in),
    .data_in_bit_sel(data_in_bit_sel),
    .data_out(data_out),

    .config_en(config_en),
    .config_wr(config_wr),
    .config_rd(config_rd),
    .config_addr(config_addr),
    .config_wr_data(config_wr_data),
    .config_rd_data(config_rd_data),

    .sram_to_mem_data(sram_to_mem_data),
    .sram_to_mem_bit_sel(sram_to_mem_bit_sel),
    .sram_to_mem_cen(sram_to_mem_cen),
    .sram_to_mem_wen(sram_to_mem_wen),
    .sram_to_mem_addr(sram_to_mem_addr),
    .mem_to_sram_data(mem_to_sram_data)
);

endmodule
