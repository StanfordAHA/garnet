/*=============================================================================
** Module: glb_core.sv
** Description:
**              Global Buffer Core
** Author: Taeyoung Kong
** Change history: 01/27/2020 - Implement first version of global buffer core
**===========================================================================*/
import  global_buffer_pkg::*;

module glb_core (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // Config
    input  logic                            cfg_store_dma_on,
    input  logic                            cfg_store_dma_auto_on,

    input  dma_header_t                     cfg_store_dma_header [QUEUE_DEPTH],
    output logic                            cfg_store_dma_invalidate_pulse [QUEUE_DEPTH],

    // Glb SRAM Config
    // TODO

    // sram - cgra

    // write packet
    input  wr_packet_t                      wr_packet_r2c,
    output wr_packet_t                      wr_packet_c2r,

    // cgra word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g,
    input  logic                            stream_data_valid_f2g,

    output logic                            stream_in_done_pulse

    // TODO
    // output logic [CGRA_DATA_WIDTH-1:0]      stream_out_data_stho,
    // output logic                            stream_out_data_valid_stho
);

//============================================================================//
// Internal variables
//============================================================================//
wr_packet_t wr_packet_from_dma;
wr_packet_t wr_packet_to_bank;

//============================================================================//
// Banks
//============================================================================//
genvar i;
generate
for (i=0; i<BANKS_PER_TILE; i=i+1) begin
    glb_core_bank bank (
        .wr_packet  (wr_packet_to_bank),
        .*);
end
endgenerate

//============================================================================//
// Store DMA
//============================================================================//
glb_core_store_dma store_dma (
    .wr_packet  (wr_packet_from_dma),
    .*);

//============================================================================//
// Write Arbiter
//============================================================================//
glb_core_wr_arbiter wr_arbiter (
    .wr_packet_from_router  (wr_packet_r2c),
    .wr_packet_to_router    (wr_packet_c2r),
    .wr_packet_from_dma     (wr_packet_from_dma),
    .wr_packet_to_bank      (wr_packet_to_bank),
    .*);

//============================================================================//
// Load DMA
//============================================================================//
// glb_core_load_dma load_dma (.*);

//============================================================================//
// Read Arbiter
//============================================================================//
// glb_core_rd_arbiter rd_arbiter (.*);

endmodule
