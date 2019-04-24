/*=============================================================================
** Module: cfg_bank_interconnect.sv
** Description:
**              Interface between cgra configuration ports and bank ports
** Author: Taeyoung Kong
** Change history: 04/21/2019 - Implement first version
**===========================================================================*/

module cfg_bank_interconnect #(
    parameter integer NUM_BANKS = 32,
    parameter integer NUM_COLS = 32,
    parameter integer NUM_CFG_CHANNELS = 8,
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 17,
    parameter integer CONFIG_ADDR_WIDTH = 8,
    parameter integer CONFIG_FEATURE_WIDTH = 4,
    parameter integer CONFIG_DATA_WIDTH = 32,
    parameter integer CFG_ADDR_WIDTH = 32,
    parameter integer CFG_DATA_WIDTH = 32
)
(

    input                           clk,
    input                           reset,

    input                           config_start_pulse,
    output                          config_done_pulse,
    
    output                          cfg_rd_en [NUM_BANKS-1:0],
    output [BANK_ADDR_WIDTH-1:0]    cfg_rd_addr [NUM_BANKS-1:0],
    input  [BANK_DATA_WIDTH-1:0]    cfg_rd_data [NUM_BANKS-1:0],

    input                           glc_to_cgra_cfg_wr,
    input  [CFG_ADDR_WIDTH-1:0]     glc_to_cgra_cfg_addr,
    input  [CFG_DATA_WIDTH-1:0]     glc_to_cgra_cfg_data,

    output                          glb_to_cgra_cfg_wr [NUM_COLS-1:0],
    output [CFG_ADDR_WIDTH-1:0]     glb_to_cgra_cfg_addr [NUM_COLS-1:0],
    output [CFG_DATA_WIDTH-1:0]     glb_to_cgra_cfg_data [NUM_COLS-1:0],

    input                           config_en,
    input                           config_wr,
    input                           config_rd,
    input  [CONFIG_ADDR_WIDTH-1:0]  config_addr,
    input  [CONFIG_DATA_WIDTH-1:0]  config_wr_data,
    output [CONFIG_DATA_WIDTH-1:0]  config_rd_data
);

//============================================================================//
// local parameter declaration
//============================================================================//
localparam integer NUM_BANKS_WIDTH = $clog2(NUM_BANKS);
localparam integer BANKS_PER_CFG = $ceil(NUM_BANKS/NUM_CFG_CHANNELS);
localparam integer COLS_PER_CFG = $ceil(NUM_COLS/NUM_CFG_CHANNELS);
localparam integer GLB_ADDR_WIDTH = NUM_BANKS_WIDTH + BANK_ADDR_WIDTH;
localparam integer CONFIG_REG_WIDTH = CONFIG_ADDR_WIDTH - CONFIG_FEATURE_WIDTH;

endmodule
