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

    // Glb SRAM Config
    // TODO

    // write packet
    input  wr_packet_t                      wr_packet_r2c,
    output wr_packet_t                      wr_packet_c2r,

    // read req packet
    input  rdrq_packet_t                    rdrq_packet_r2c,
    output rdrq_packet_t                    rdrq_packet_c2r,

    // read res packet
    input  rdrs_packet_t                    rdrs_packet_r2c,
    output rdrs_packet_t                    rdrs_packet_c2r,

    // cgra word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g,
    input  logic                            stream_data_valid_f2g,
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f,
    output logic                            stream_data_valid_g2f,

    // Configuration registers
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  cfg_multi_tile_size,
    input  logic                            cfg_store_dma_on,
    input  logic                            cfg_store_dma_auto_on,
    input  dma_st_header_t                  cfg_store_dma_header [QUEUE_DEPTH],
    input  logic                            cfg_load_dma_on,
    input  logic                            cfg_load_dma_auto_on,
    input  dma_ld_header_t                  cfg_load_dma_header [QUEUE_DEPTH],

    // internal dma invalidation pulse
    output logic                            cfg_store_dma_invalidate_pulse [QUEUE_DEPTH],
    output logic                            cfg_load_dma_invalidate_pulse [QUEUE_DEPTH],

    // interrupt
    output logic                            stream_f2g_done_pulse,
    output logic                            stream_g2f_done_pulse
);

//============================================================================//
// Internal variables
//============================================================================//
wr_packet_t     wr_packet_from_dma;
wr_packet_t     wr_packet_to_bank;
rdrq_packet_t   rdrq_packet_from_dma;
rdrq_packet_t   rdrq_packet_to_bank;
rdrs_packet_t   rdrs_packet_from_bank;
rdrs_packet_t   rdrs_packet_to_dma;

//============================================================================//
// Banks
//============================================================================//
genvar i;
generate
for (i=0; i<BANKS_PER_TILE; i=i+1) begin
    glb_core_bank bank (
        .wr_packet      (wr_packet_to_bank),
        .rdrq_packet    (rdrq_packet_to_bank),
        .rdrs_packet    (rdrs_packet_from_bank),
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
// Load DMA
//============================================================================//
glb_core_load_dma load_dma (
    .rdrq_packet  (rdrq_packet_from_dma),
    .rdrs_packet  (rdrs_packet_to_dma),
    .*);

//============================================================================//
// Packet Switch
//============================================================================//
glb_core_switch switch (
    .wr_packet_from_router      (wr_packet_r2c),
    .wr_packet_to_router        (wr_packet_c2r),
    .wr_packet_from_dma         (wr_packet_from_dma),
    .wr_packet_to_bank          (wr_packet_to_bank),

    .rdrq_packet_from_router    (rdrq_packet_r2c),
    .rdrq_packet_to_router      (rdrq_packet_c2r),
    .rdrq_packet_from_dma       (rdrq_packet_from_dma),
    .rdrq_packet_to_bank        (rdrq_packet_to_bank),

    .rdrs_packet_from_router    (rdrs_packet_r2c),
    .rdrs_packet_to_router      (rdrs_packet_c2r),
    .rdrs_packet_from_bank      (rdrs_packet_from_bank),
    .rdrs_packet_to_dma         (rdrs_packet_to_dma),
    .*);

endmodule
