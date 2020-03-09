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

    // processor packet
    input  packet_t                         proc_packet_wsti,
    output packet_t                         proc_packet_wsto,
    input  packet_t                         proc_packet_esti,
    output packet_t                         proc_packet_esto,

    // stream packet
    input  packet_t                         strm_packet_wsti,
    output packet_t                         strm_packet_wsto,
    input  packet_t                         strm_packet_esti,
    output packet_t                         strm_packet_esto,

    // cgra word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g,
    input  logic                            stream_data_valid_f2g,
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f,
    output logic                            stream_data_valid_g2f,

    // Configuration registers
    input  logic                            cfg_tile_is_start,
    input  logic                            cfg_tile_is_end,
    input  logic                            cfg_store_dma_on,
    input  logic                            cfg_store_dma_auto_on,
    input  dma_st_header_t                  cfg_store_dma_header [QUEUE_DEPTH],

    input  logic                            cfg_load_dma_on,
    input  logic                            cfg_load_dma_auto_on,
    input  dma_ld_header_t                  cfg_load_dma_header [QUEUE_DEPTH],

    // internal dma invalidation pulse
    output logic                            cfg_store_dma_invalidate_pulse [QUEUE_DEPTH],
    output logic                            cfg_load_dma_invalidate_pulse [QUEUE_DEPTH],

    // parallel configuration
    input  logic                            cfg_pc_dma_on,
    input  dma_pc_header_t                  cfg_pc_dma_header,

    output cgra_cfg_t                       cgra_cfg_c2sw,

    // application control
    input  logic                            cfg_strm_start_pulse,
    input  logic                            cfg_pc_start_pulse,

    // interrupt
    output logic                            stream_f2g_done_pulse,
    output logic                            stream_g2f_done_pulse,
    output logic                            pc_done_pulse

    // Glb SRAM Config
    // TODO
);

//============================================================================//
// Internal variables
//============================================================================//
wr_packet_t     proc_wr_packet_pr2sw;
rdrq_packet_t   proc_rdrq_packet_pr2sw;
rdrs_packet_t   proc_rdrs_packet_sw2pr;

packet_t        strm_packet_sr2sw;
packet_t        strm_packet_sw2sr;

wr_packet_t     wr_packet_d2sw;
wr_packet_t     wr_packet_sw2b;
rdrq_packet_t   rdrq_packet_d2sw;
rdrq_packet_t   rdrq_packet_sw2b;
rdrs_packet_t   rdrs_packet_sw2d;
rdrs_packet_t   rdrs_packet_b2sw_arr [BANKS_PER_TILE];
rdrq_packet_t   rdrq_packet_pc2sw;
rdrs_packet_t   rdrs_packet_sw2pc;

//============================================================================//
// Banks
//============================================================================//
genvar i;
generate
for (i=0; i<BANKS_PER_TILE; i=i+1) begin
    glb_bank bank (
        .wr_packet      (wr_packet_sw2b),
        .rdrq_packet    (rdrq_packet_sw2b),
        .rdrs_packet    (rdrs_packet_b2sw_arr[i]),
        .*);
end
endgenerate

//============================================================================//
// Store DMA
//============================================================================//
glb_core_store_dma store_dma (
    .wr_packet  (wr_packet_d2sw),
    .*);

//============================================================================//
// Load DMA
//============================================================================//
glb_core_load_dma load_dma (
    .rdrq_packet  (rdrq_packet_d2sw),
    .rdrs_packet  (rdrs_packet_sw2d),
    .*);
    
//============================================================================//
// Parallel Config Ctrl DMA
//============================================================================//
glb_core_pc_dma pc_dma (
    .rdrq_packet  (rdrq_packet_pc2sw),
    .rdrs_packet  (rdrs_packet_sw2pc),
    .*);

//============================================================================//
// Packet Switch
//============================================================================//
glb_core_switch switch (
    .wr_packet_sr2sw        (strm_packet_sr2sw.wr),
    .wr_packet_pr2sw        (proc_wr_packet_pr2sw),
    .wr_packet_sw2sr        (strm_packet_sw2sr.wr),
    .wr_packet_d2sw         (wr_packet_d2sw),
    .wr_packet_sw2b         (wr_packet_sw2b),

    .rdrq_packet_sr2sw      (strm_packet_sr2sw.rdrq),
    .rdrq_packet_pr2sw      (proc_rdrq_packet_pr2sw),
    .rdrq_packet_sw2sr      (strm_packet_sw2sr.rdrq),
    .rdrq_packet_d2sw       (rdrq_packet_d2sw),
    .rdrq_packet_sw2b       (rdrq_packet_sw2b),

    .rdrs_packet_sr2sw      (strm_packet_sr2sw.rdrs),
    .rdrs_packet_sw2pr      (proc_rdrs_packet_sw2pr),
    .rdrs_packet_sw2sr      (strm_packet_sw2sr.rdrs),
    .rdrs_packet_sw2d       (rdrs_packet_sw2d),
    .rdrs_packet_b2sw_arr   (rdrs_packet_b2sw_arr),
    .*);

//============================================================================//
// Proc Packet Router
//============================================================================//
glb_core_proc_router glb_core_proc_router (
    .packet_wsti        (proc_packet_wsti),
    .packet_wsto        (proc_packet_wsto),
    .packet_esti        (proc_packet_esti),
    .packet_esto        (proc_packet_esto),
    .wr_packet_pr2sw    (proc_wr_packet_pr2sw),
    .rdrq_packet_pr2sw  (proc_rdrq_packet_pr2sw),
    .rdrs_packet_sw2pr  (proc_rdrs_packet_sw2pr),
    .*);

//============================================================================//
// Stream Packet Router
//============================================================================//
glb_core_strm_router glb_core_strm_router (
    .packet_wsti        (strm_packet_wsti),
    .packet_wsto        (strm_packet_wsto),
    .packet_esti        (strm_packet_esti),
    .packet_esto        (strm_packet_esto),
    .packet_sw2sr       (strm_packet_sw2sr),
    .packet_sr2sw       (strm_packet_sr2sw),
    .*);

endmodule
