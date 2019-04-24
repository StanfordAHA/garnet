/*=============================================================================
** Module: memory_core.sv
** Description:
**              memory core
** Author: Taeyoung Kong
** Change history:  04/10/2019 - Implement first version of memory core
**===========================================================================*/

module memory_core #(
    parameter BANK_DATA_WIDTH = 64,
    parameter BANK_ADDR_WIDTH = 16,
    parameter CONFIG_DATA_WIDTH = 32
)
(
    input                           clk,
    input                          reset,

    input                          ren,
    input                          wen,

    input  [BANK_ADDR_WIDTH-1:0]   addr,
    input  [BANK_DATA_WIDTH-1:0]   data_in,
    output [BANK_DATA_WIDTH-1:0]   data_out,

    input                          config_en,
    input                          config_wr,
    input                          config_rd,
    input  [BANK_ADDR_WIDTH-1:0]   config_addr,
    input  [CONFIG_DATA_WIDTH-1:0] config_wr_data,
    output [CONFIG_DATA_WIDTH-1:0] config_rd_data
);

//===========================================================================//
// local parameter declaration
//===========================================================================//

endmodule
