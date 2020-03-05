/*=============================================================================
** Module: glb_memory_core.sv
** Description:
**              glb memory core
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of memory core
**===========================================================================*/
import global_buffer_pkg::*;

module glb_bank_memory (
    input  logic                            clk,
    input  logic                            reset,

    input  logic                            ren,
    input  logic                            wen,
    input  logic [BANK_ADDR_WIDTH-1:0]      addr,
    input  logic [BANK_DATA_WIDTH-1:0]      data_in,
    input  logic [BANK_DATA_WIDTH-1:0]      data_in_bit_sel,
    output logic [BANK_DATA_WIDTH-1:0]      data_out
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
glb_bank_sram_gen #(
    .DATA_WIDTH(BANK_DATA_WIDTH),
    .ADDR_WIDTH(BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET)
) glb_bank_sram_gen (
    .clk(clk),
    .clk_en(sram_to_mem_cen),
    .wen(sram_to_mem_wen),
    .addr(sram_to_mem_addr),
    .data_in(sram_to_mem_data),
    .bit_sel(sram_to_mem_bit_sel),
    .data_out(mem_to_sram_data)
);

endmodule
