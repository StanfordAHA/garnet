/*=============================================================================
** Module: io_controller.sv
** Description:
**              io controller
** Author: Taeyoung Kong
** Change history: 04/10/2019 - Implement first version 
**===========================================================================*/

module io_controller #(
    parameter integer NUM_BANKS = 32,
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 16,
    parameter integer CGRA_DATA_WIDTH = 16,
    parameter integer CONFIG_DATA_WIDTH = 32
)
(
    input                           clk,
    input                           reset,

    input                           stall,
    input                           cgra_start_pulse,

    input [GLB_ADDR_WIDTH-1:0]      start_addr,
    input [CONFIG_DATA_WIDTH-1:0]   num_words,
    input [1:0]                     mode,

    input                           cgra_to_io_wr_en,
    input                           cgra_to_io_rd_en,
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_wr_data,
    output [CGRA_DATA_WIDTH-1:0]    io_to_cgra_rd_data,
    output                          io_to_cgra_rd_data_valid,
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_addr_high,
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_addr_low,
    
    output                          io_to_bank_wr_en,
    output [BANK_DATA_WIDTH-1:0]    io_to_bank_wr_data,
    output                          io_to_bank_rd_en,
    input  [BANK_DATA_WIDTH-1:0]    bank_to_io_rd_data,
    output [GLB_ADDR_WIDTH-1:0]     io_to_bank_addr
);

//============================================================================//
// local parameter declaration
//============================================================================//
localparam integer NUM_BANKS_WIDTH = $clog2(NUM_BANKS);
localparam integer GLB_ADDR_WIDTH = NUM_BANKS_WIDTH + BANK_ADDR_WIDTH;

endmodule
