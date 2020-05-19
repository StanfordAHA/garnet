/*=============================================================================
** Module: glb_memory_core.sv
** Description:
**              glb memory core
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of memory core
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_bank_memory (
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
logic                                           sram_cen;
logic                                           sram_wen;
logic                                           sram_ren;
logic [BANK_ADDR_WIDTH-BANK_BYTE_OFFSET-1:0]    sram_addr;
logic [BANK_DATA_WIDTH-1:0]                     sram_data_in;
logic [BANK_DATA_WIDTH-1:0]                     sram_bit_sel;
logic [BANK_DATA_WIDTH-1:0]                     sram_data_out;
logic                                           sram_ren_d1, sram_ren_d2, sram_ren_d3;
logic [BANK_DATA_WIDTH-1:0]                     data_out_d1;

//===========================================================================//
// memory instantiation
//===========================================================================//
glb_bank_sram_gen #(
    .DATA_WIDTH(BANK_DATA_WIDTH),
    .ADDR_WIDTH(BANK_ADDR_WIDTH-BANK_BYTE_OFFSET)
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
        sram_ren_d1 <= 0;
        sram_ren_d2 <= 0;
        sram_ren_d3 <= 0;
        data_out_d1 <= 0;
    end
    else begin
        sram_ren_d1 <= sram_ren;
        sram_ren_d2 <= sram_ren_d1;
        sram_ren_d3 <= sram_ren_d2;
        data_out_d1 <= data_out;
    end
end
assign data_out = sram_ren_d3 ? sram_data_out : data_out_d1;

endmodule
