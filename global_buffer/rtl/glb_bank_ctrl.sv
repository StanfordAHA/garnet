/*=============================================================================
** Module: glb_bank_ctrl.sv
** Description:
**              bank controller coordinates host-cgra read/write.
**              host read/write has priority
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of bank controller
**===========================================================================*/
import global_buffer_pkg::*;

module glb_bank_ctrl  (
    input  logic                        clk,
    input  logic                        reset,

    // packet interface
    input  logic                        packet_wr_en,
    input  logic  [BANK_ADDR_WIDTH-1:0] packet_wr_addr,
    input  logic  [BANK_DATA_WIDTH-1:0] packet_wr_data,
    input  logic  [BANK_DATA_WIDTH-1:0] packet_wr_data_bit_sel,

    input  logic                        packet_rd_en,
    input  logic  [BANK_ADDR_WIDTH-1:0] packet_rd_addr,
    output logic  [BANK_DATA_WIDTH-1:0] packet_rd_data,
    output logic                        packet_rd_data_valid,

    // interface with memory
    output logic                        mem_rd_en,
    output logic                        mem_wr_en,
    output logic  [BANK_ADDR_WIDTH-1:0] mem_addr,
    output logic  [BANK_DATA_WIDTH-1:0] mem_data_in,
    output logic  [BANK_DATA_WIDTH-1:0] mem_data_in_bit_sel,
    input  logic  [BANK_DATA_WIDTH-1:0] mem_data_out
);

//===========================================================================//
// signal declaration
//===========================================================================//
logic                       packet_rd_en_d1;
logic [BANK_DATA_WIDTH-1:0] packet_rd_data_d1;
logic                       cfg_rd_en_d1;
logic [BANK_DATA_WIDTH-1:0] cfg_rd_data_d1;

//===========================================================================//
// Set mem_wr_en and mem_data_in output
//===========================================================================//
always_comb begin
    if (packet_wr_en) begin
        mem_wr_en = 1;
        mem_data_in_bit_sel = packet_wr_data_bit_sel;
        mem_rd_en = 0;
        mem_data_in = packet_wr_data;
        mem_addr = packet_wr_addr;
    end
    else if (packet_rd_en) begin
        mem_wr_en = 0;
        mem_data_in_bit_sel = {BANK_DATA_WIDTH{1'b0}};
        mem_rd_en = 1;
        mem_data_in = 0;
        mem_addr = packet_rd_addr;
    end
    else begin
        mem_wr_en = 0;
        mem_data_in_bit_sel = {BANK_DATA_WIDTH{1'b0}};
        mem_rd_en = 0;
        mem_data_in = 0;
        mem_addr = 0;
    end
end

//===========================================================================//
// rd_data output assignment
//===========================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        packet_rd_en_d1 <= 0;
        packet_rd_data_d1 <= 0;
    end
    else begin
        packet_rd_en_d1 <= packet_rd_en;
        packet_rd_data_d1 <= packet_rd_data;
    end
end

assign packet_rd_data = packet_rd_en_d1 ? mem_data_out : packet_rd_data_d1;
assign packet_rd_data_valid = packet_rd_en_d1;

endmodule
