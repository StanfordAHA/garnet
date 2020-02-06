/*=============================================================================
** Module: glb_bank.sv
** Description:
**              glb bank
** Author: Taeyoung Kong
** Change history:  01/08/2020 - Implement first version of memory bank
**===========================================================================*/
import global_buffer_pkg::*;

module glb_core_bank (
    input  logic                        clk,
    input  logic                        clk_en,
    input  logic                        reset,

    input  wr_packet_t                  wr_packet
);

// //===========================================================================//
// // signal declaration
// //===========================================================================//
// logic                       mem_rd_en;
// logic                       mem_wr_en;
// logic [BANK_ADDR_WIDTH-1:0] mem_addr;
// logic [BANK_DATA_WIDTH-1:0] mem_data_in;
// logic [BANK_DATA_WIDTH-1:0] mem_data_in_bit_sel;
// logic [BANK_DATA_WIDTH-1:0] mem_data_out;
// 
// //===========================================================================//
// // memory core declaration
// //===========================================================================//
// glb_memory_core glb_memory_core_inst (
//     .clk(clk),
//     .reset(reset),
// 
//     .ren(mem_rd_en),
//     .wen(mem_wr_en),
//     .addr(mem_addr),
//     .data_in(mem_data_in),
//     .data_in_bit_sel(mem_data_in_bit_sel),
//     .data_out(mem_data_out),
// 
//     .config_en(config_en),
//     .config_wr(config_wr),
//     .config_rd(config_rd),
//     .config_addr(config_addr),
//     .config_wr_data(config_wr_data),
//     .config_rd_data(config_rd_data)
// );
// 
// //===========================================================================//
// // bank controller declaration
// //===========================================================================//
// glb_bank_controller glb_bank_controller_inst (
//     .clk(clk),
//     .reset(reset),
// 
//     .host_wr_en(host_wr_en),
//     .host_wr_addr(host_wr_addr),
//     .host_wr_data(host_wr_data),
//     .host_wr_data_bit_sel(host_wr_data_bit_sel),
// 
//     .host_rd_en(host_rd_en),
//     .host_rd_addr(host_rd_addr),
//     .host_rd_data(host_rd_data),
// 
//     .cgra_wr_en(cgra_wr_en),
//     .cgra_wr_addr(cgra_wr_addr),
//     .cgra_wr_data(cgra_wr_data),
//     .cgra_wr_data_bit_sel(cgra_wr_data_bit_sel),
// 
//     .cgra_rd_en(cgra_rd_en),
//     .cgra_rd_addr(cgra_rd_addr),
//     .cgra_rd_data(cgra_rd_data),
// 
//     .cfg_rd_en(cfg_rd_en),
//     .cfg_rd_addr(cfg_rd_addr),
//     .cfg_rd_data(cfg_rd_data),
// 
//     .mem_rd_en(mem_rd_en),
//     .mem_wr_en(mem_wr_en),
//     .mem_addr(mem_addr),
//     .mem_data_in(mem_data_in),
//     .mem_data_in_bit_sel(mem_data_in_bit_sel),
//     .mem_data_out(mem_data_out)
// );

endmodule
