/*=============================================================================
** Module: glb_core_bank.sv
** Description:
**              glb core bank
** Author: Taeyoung Kong
** Change history:  02/25/2020 - Implement first version of glb core bank
**===========================================================================*/
import global_buffer_pkg::*;

module glb_core_bank (
    input  logic            clk,
    input  logic            clk_en,
    input  logic            reset,

    input  wr_packet_t      wr_packet,
    input  rdrq_packet_t    rdrq_packet
    // output rdrs_packet_t    rdrs_packet
);

//===========================================================================//
// signal declaration
//===========================================================================//
logic                       mem_rd_en;
logic                       mem_wr_en;
logic [BANK_ADDR_WIDTH-1:0] mem_addr;
logic [BANK_DATA_WIDTH-1:0] mem_data_in;
logic [BANK_DATA_WIDTH-1:0] mem_data_in_bit_sel;
logic [BANK_DATA_WIDTH-1:0] mem_data_out;

//===========================================================================//
// memory core declaration
//===========================================================================//
glb_bank_memory glb_bank_memory (
    .clk(clk),
    .reset(reset),

    .ren(mem_rd_en),
    .wen(mem_wr_en),
    .addr(mem_addr),
    .data_in(mem_data_in),
    .data_in_bit_sel(mem_data_in_bit_sel),
    .data_out(mem_data_out)

    // .config_en(config_en),
    // .config_wr(config_wr),
    // .config_rd(config_rd),
    // .config_addr(config_addr),
    // .config_wr_data(config_wr_data),
    // .config_rd_data(config_rd_data)
);

//===========================================================================//
// bank configuration controller declaration
//===========================================================================//
glb_bank_cfg_controller glb_bank_cfg_controller (
    .clk(clk),
    .reset(reset),

    // .host_wr_en(host_wr_en),
    // .host_wr_addr(host_wr_addr),
    // .host_wr_data(host_wr_data),
    // .host_wr_data_bit_sel(host_wr_data_bit_sel),

    // .host_rd_en(host_rd_en),
    // .host_rd_addr(host_rd_addr),
    // .host_rd_data(host_rd_data),

    .cgra_wr_en(wr_packet.wr_en),
    .cgra_wr_addr(wr_packet.wr_addr[BANK_ADDR_WIDTH-1:0]),
    .cgra_wr_data(wr_packet.wr_data),
    // TODO
    .cgra_wr_data_bit_sel({BANK_DATA_WIDTH{1'b1}}),

    .cgra_rd_en(rdrq_packet.rd_en),
    .cgra_rd_addr(rdrq_packet.rd_addr[BANK_ADDR_WIDTH-1:0]),
    .cgra_rd_data(),

    // .cfg_rd_en(cfg_rd_en),
    // .cfg_rd_addr(cfg_rd_addr),
    // .cfg_rd_data(cfg_rd_data),

    .mem_rd_en(mem_rd_en),
    .mem_wr_en(mem_wr_en),
    .mem_addr(mem_addr),
    .mem_data_in(mem_data_in),
    .mem_data_in_bit_sel(mem_data_in_bit_sel),
    .mem_data_out(mem_data_out)
);
assign rdrs_packet = '0;

endmodule
