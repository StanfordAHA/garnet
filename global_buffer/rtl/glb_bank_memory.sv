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
logic                                               sram_cen;
logic                                               sram_wen;
logic [BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET-1:0]   sram_addr;
logic [BANK_DATA_WIDTH-1:0]                         sram_data_in;
logic [BANK_DATA_WIDTH-1:0]                         sram_bit_sel;
logic [BANK_DATA_WIDTH-1:0]                         sram_data_out;
logic                                               ren_d1;
logic [BANK_DATA_WIDTH-1:0]                         data_out_d1;

assign sram_wen = wen;
assign sram_cen = wen | ren;
assign sram_addr = addr[BANK_ADDR_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET];
assign sram_data_in = data_in;
assign sram_bit_sel = data_in_bit_sel;

//===========================================================================//
// memory instantiation
//===========================================================================//
glb_bank_sram_gen #(
    .DATA_WIDTH(BANK_DATA_WIDTH),
    .ADDR_WIDTH(BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET)
) glb_bank_sram_gen (
    .CLK(clk),
    .CEB(~sram_cen),
    .WEB(~sram_wen),
    .A(sram_addr),
    .D(sram_data_in),
    .BWEB(~sram_bit_sel),
    .Q(sram_data_out)
);

//===========================================================================//
// output assignment
//===========================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        ren_d1 <= 0;
        data_out_d1 <= 0;
    end
    else begin
        ren_d1 <= ren;
        data_out_d1 <= data_out;
    end
end
assign data_out = ren_d1 ? sram_data_out : data_out_d1;

endmodule
