/*=============================================================================
** Module: glb_core_bank.sv
** Description:
**              glb core bank
** Author: Taeyoung Kong
** Change history:  02/25/2020 - Implement first version of glb core bank
**===========================================================================*/

module glb_bank 
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                        clk,
    input  logic                        reset,

    input  wr_packet_t                  wr_packet,
    input  rdrq_packet_t                rdrq_packet,
    output rdrs_packet_t                rdrs_packet,

    cfg_ifc.slave                       if_sram_cfg
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
    .data_out(mem_data_out),
    .*);

//===========================================================================//
// expand byte strb to bit strb
//===========================================================================//
logic [BANK_DATA_WIDTH-1:0] wr_data_bit_sel;
always_comb begin
    for (int i=0; i < (BANK_DATA_WIDTH/8); i=i+1) begin
        wr_data_bit_sel[i*8 +: 8] = {8{wr_packet.wr_strb[i]}};
    end
end

//===========================================================================//
// bank controller declaration
//===========================================================================//
glb_bank_ctrl glb_bank_ctrl (
    .clk(clk),
    .reset(reset),

    .packet_wr_en(wr_packet.wr_en),
    .packet_wr_addr(wr_packet.wr_addr[BANK_ADDR_WIDTH-1:0]),
    .packet_wr_data(wr_packet.wr_data),
    .packet_wr_data_bit_sel(wr_data_bit_sel),

    // .packet_rdrq_packet_sel(rdrq_packet.packet_sel),
    .packet_rd_en(rdrq_packet.rd_en),
    .packet_rd_addr(rdrq_packet.rd_addr[BANK_ADDR_WIDTH-1:0]),
    .packet_rd_data(rdrs_packet.rd_data),
    .packet_rd_data_valid(rdrs_packet.rd_data_valid),
    // .packet_rdrs_packet_sel(rdrs_packet.packet_sel),

    .mem_rd_en(mem_rd_en),
    .mem_wr_en(mem_wr_en),
    .mem_addr(mem_addr),
    .mem_data_in(mem_data_in),
    .mem_data_in_bit_sel(mem_data_in_bit_sel),
    .mem_data_out(mem_data_out),
    .*
);

endmodule
