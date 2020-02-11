/*=============================================================================
** Module: glb_core_wr_arbiter.sv
** Description:
**              Global Buffer Core Write Channel Arbiter
** Author: Taeyoung Kong
** Change history: 01/27/2020
**      - Implement first version of global buffer core write channel arbiter
**===========================================================================*/
import  global_buffer_pkg::*;

module glb_core_wr_arbiter (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // cgra word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g,
    input  logic                            stream_data_valid_f2g,

    // wr_packet input
    input  wr_packet_t                      wr_packet_from_router,
    input  wr_packet_t                      wr_packet_from_dma,

    // wr_packet output
    output wr_packet_t                      wr_packet_to_router,
    output wr_packet_t                      wr_packet_to_bank,

    // arbiter - dma

    // Configuration registers
    input  logic                            cfg_store_dma_on
);

//============================================================================//
// To router
//============================================================================//
assign wr_packet_to_router = cfg_store_dma_on
                           ? wr_packet_from_dma : wr_packet_from_router;

//============================================================================//
// To bank
// Pipeline register for timing
// If addr does not match, do not route
//============================================================================//
wr_packet_t wr_packet_to_bank_int;
wr_packet_t wr_packet_to_bank_int_filtered;
wr_packet_t wr_packet_to_bank_int_filtered_d1;

assign wr_packet_to_bank_int = cfg_store_dma_on
                             ? wr_packet_from_dma : wr_packet_from_router;

always_comb begin
    if (wr_packet_to_bank_int.wr_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) begin
        wr_packet_to_bank_int_filtered = wr_packet_to_bank_int;
    end
    else begin
        wr_packet_to_bank_int_filtered = '0;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        wr_packet_to_bank_int_filtered_d1 <= '0;
    end
    else if (clk_en) begin
        wr_packet_to_bank_int_filtered_d1 <= wr_packet_to_bank_int_filtered;
    end
end
assign wr_packet_to_bank = wr_packet_to_bank_int_filtered_d1;

endmodule
