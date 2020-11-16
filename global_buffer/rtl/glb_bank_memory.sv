/*=============================================================================
** Module: glb_memory_core.sv
** Description:
**              glb memory core
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of memory core
**===========================================================================*/

module glb_bank_memory 
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                        clk,
    input  logic                        reset,

    input  logic                        ren,
    input  logic                        wen,
    input  logic [BANK_ADDR_WIDTH-1:0]  addr,
    input  logic [BANK_DATA_WIDTH-1:0]  data_in,
    input  logic [BANK_DATA_WIDTH-1:0]  data_in_bit_sel,
    output logic [BANK_DATA_WIDTH-1:0]  data_out
);

//===========================================================================//
// memory-SRAM interface signal declaration
//===========================================================================//
logic                                           sram_cen, sram_cen_d1;
logic                                           sram_wen, sram_wen_d1;
logic                                           sram_ren, sram_ren_d1, sram_ren_d2, sram_ren_d3;
logic [BANK_ADDR_WIDTH-BANK_BYTE_OFFSET-1:0]    sram_addr, sram_addr_d1;
logic [BANK_DATA_WIDTH-1:0]                     sram_data_in, sram_data_in_d1;
logic [BANK_DATA_WIDTH-1:0]                     sram_bit_sel, sram_bit_sel_d1;
logic [BANK_DATA_WIDTH-1:0]                     sram_data_out;
logic [BANK_DATA_WIDTH-1:0]                     data_out_d1;

//===========================================================================//
// memory instantiation
//===========================================================================//
glb_bank_sram_gen #(
    .DATA_WIDTH(BANK_DATA_WIDTH),
    .ADDR_WIDTH(BANK_ADDR_WIDTH-BANK_BYTE_OFFSET)
) glb_bank_sram_gen (
    .CLK(clk),
    .CEB(~sram_cen_d1),
    .WEB(~sram_wen_d1),
    .A(sram_addr_d1),
    .D(sram_data_in_d1),
    .BWEB(~sram_bit_sel_d1),
    .Q(sram_data_out)
);

//===========================================================================//
// sram control logic
//===========================================================================//
always_comb begin
    sram_wen = wen;
    sram_ren = ren;
    sram_cen = wen | ren;
    sram_addr = addr[BANK_ADDR_WIDTH-1:BANK_BYTE_OFFSET];
    sram_data_in = data_in;
    sram_bit_sel = data_in_bit_sel;
end

//===========================================================================//
// output assignment
//===========================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        sram_cen_d1 <= 0;
        sram_wen_d1 <= 0;
        sram_addr_d1 <= 0;
        sram_data_in_d1 <= 0;
        sram_bit_sel_d1 <= 0;
        sram_ren_d1 <= 0;
        sram_ren_d2 <= 0;
        sram_ren_d3 <= 0;
        data_out_d1 <= 0;
    end
    else begin
        sram_cen_d1 <= sram_cen;
        sram_wen_d1 <= sram_wen;
        sram_addr_d1 <= sram_addr;
        sram_data_in_d1 <= sram_data_in;
        sram_bit_sel_d1 <= sram_bit_sel;
        sram_ren_d1 <= sram_ren;
        sram_ren_d2 <= sram_ren_d1;
        sram_ren_d3 <= sram_ren_d2;
        data_out_d1 <= data_out;
    end
end
assign data_out = sram_ren_d3 ? sram_data_out : data_out_d1;

endmodule
