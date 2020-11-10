/*=============================================================================
** Module: glb_core.sv
** Description:
**              Global Buffer Core
** Author: Taeyoung Kong
** Change history: 01/27/2020 - Implement first version of global buffer core
**===========================================================================*/

module glb_core 
import  global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // processor packet
    input  packet_t                         proc_packet_w2e_wsti,
    output packet_t                         proc_packet_e2w_wsto,
    input  packet_t                         proc_packet_e2w_esti,
    output packet_t                         proc_packet_w2e_esto,

    // stream packet
    input  packet_t                         strm_packet_w2e_wsti_d1,
    output packet_t                         strm_packet_e2w_wsto,
    input  packet_t                         strm_packet_e2w_esti_d1,
    output packet_t                         strm_packet_w2e_esto,

    // pc packet
    input  rd_packet_t                      pc_packet_w2e_wsti,
    output rd_packet_t                      pc_packet_e2w_wsto,
    input  rd_packet_t                      pc_packet_e2w_esti,
    output rd_packet_t                      pc_packet_w2e_esto,

    // cgra word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g [CGRA_PER_GLB],
    input  logic                            stream_data_valid_f2g [CGRA_PER_GLB],
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f [CGRA_PER_GLB],
    output logic                            stream_data_valid_g2f [CGRA_PER_GLB],

    // SRAM Config
    cfg_ifc.master                          if_sram_cfg_est_m,
    cfg_ifc.slave                           if_sram_cfg_wst_s,

    // Configuration registers
    input  logic                            cfg_tile_connected_prev,
    input  logic                            cfg_tile_connected_next,
    input  logic                            cfg_pc_tile_connected_prev,
    input  logic                            cfg_pc_tile_connected_next,
    input  logic [1:0]                      cfg_soft_reset_mux,
    input  logic                            cfg_use_valid,
    input  logic [1:0]                      cfg_strm_g2f_mux,
    input  logic [1:0]                      cfg_strm_f2g_mux,
    input  logic [1:0]                      cfg_ld_dma_mode,
    input  logic [1:0]                      cfg_st_dma_mode,
    input  logic                            cfg_pc_dma_mode,
    input  logic [LATENCY_WIDTH-1:0]        cfg_latency,
    input  logic [LATENCY_WIDTH-1:0]        cfg_pc_latency,
    input  dma_st_header_t                  cfg_st_dma_header [QUEUE_DEPTH],
    input  dma_ld_header_t                  cfg_ld_dma_header [QUEUE_DEPTH],
    input  dma_pc_header_t                  cfg_pc_dma_header,

    // soft reset
    input  logic                            cgra_soft_reset,

    // internal dma invalidation pulse
    output logic                            cfg_store_dma_invalidate_pulse [QUEUE_DEPTH],
    output logic                            cfg_load_dma_invalidate_pulse [QUEUE_DEPTH],

    // parallel configuration
    output cgra_cfg_t                       cgra_cfg_c2sw,

    // application control
    input  logic                            strm_start_pulse,
    input  logic                            pc_start_pulse,

    // interrupt
    output logic                            strm_f2g_interrupt_pulse,
    output logic                            strm_g2f_interrupt_pulse,
    output logic                            pcfg_g2f_interrupt_pulse
);

//============================================================================//
// Internal variables
//============================================================================//
logic [CGRA_DATA_WIDTH-1:0] stream_data_g2f_dma;
logic                       stream_data_valid_g2f_dma;
logic [CGRA_DATA_WIDTH-1:0] stream_data_f2g_dma;
logic                       stream_data_valid_f2g_dma;
logic                       stream_f2g_done_pulse;
logic                       stream_g2f_done_pulse;
logic                       pc_done_pulse;

wr_packet_t                 proc_wr_packet_pr2sw;
rdrq_packet_t               proc_rdrq_packet_pr2sw;
rdrs_packet_t               proc_rdrs_packet_sw2pr;

packet_t                    strm_packet_sr2sw;
packet_t                    strm_packet_sw2sr;

rd_packet_t                 pc_packet_pcr2sw;
rd_packet_t                 pc_packet_sw2pcr;

wr_packet_t                 wr_packet_d2sw;
wr_packet_t                 wr_packet_sw2b_arr [BANKS_PER_TILE];
rdrq_packet_t               rdrq_packet_d2sw;
rdrq_packet_t               rdrq_packet_sw2b_arr [BANKS_PER_TILE];
rdrs_packet_t               rdrs_packet_sw2d;
rdrq_packet_t               rdrq_packet_pcd2sw;
rdrs_packet_t               rdrs_packet_sw2pcd;
rdrs_packet_t               rdrs_packet_b2sw_arr [BANKS_PER_TILE];

// Address width is BANK_ADDR_WIDTH, not GLB_ADDR_WIDTH
cfg_ifc #(.AWIDTH(BANK_ADDR_WIDTH), .DWIDTH(CGRA_CFG_DATA_WIDTH)) if_sram_cfg_bank [BANKS_PER_TILE]();

//============================================================================//
// Banks
//============================================================================//
genvar i;
generate
for (i=0; i<BANKS_PER_TILE; i=i+1) begin: glb_bank_gen
    glb_bank bank (
        .wr_packet      (wr_packet_sw2b_arr[i]),
        .rdrq_packet    (rdrq_packet_sw2b_arr[i]),
        .rdrs_packet    (rdrs_packet_b2sw_arr[i]),
        .if_sram_cfg    (if_sram_cfg_bank[i]),
        .*);
end: glb_bank_gen
endgenerate

//============================================================================//
// SRAM config control logic
//============================================================================//
glb_core_sram_cfg_ctrl glb_core_sram_cfg_ctrl (
    .if_sram_cfg_bank   (if_sram_cfg_bank),
    .*);

//============================================================================//
// Store DMA
//============================================================================//
glb_core_store_dma store_dma (
    .wr_packet              (wr_packet_d2sw),
    .stream_data_f2g        (stream_data_f2g_dma),
    .stream_data_valid_f2g  (stream_data_valid_f2g_dma),
    .*);

//============================================================================//
// Load DMA
//============================================================================//
glb_core_load_dma load_dma (
    .rdrq_packet            (rdrq_packet_d2sw),
    .rdrs_packet            (rdrs_packet_sw2d),
    .stream_data_g2f        (stream_data_g2f_dma),
    .stream_data_valid_g2f  (stream_data_valid_g2f_dma),
    .*);
    
//============================================================================//
// Parallel Config Ctrl DMA
//============================================================================//
glb_core_pc_dma pc_dma (
    .rdrq_packet  (rdrq_packet_pcd2sw),
    .rdrs_packet  (rdrs_packet_sw2pcd),
    .*);

//============================================================================//
// Stream data to/from cgra mux
//============================================================================//
glb_core_strm_mux glb_core_strm_mux (.*);

//============================================================================//
// Packet Switch
//============================================================================//
glb_core_switch glb_core_switch (
    .wr_packet_sr2sw        (strm_packet_sr2sw.wr),
    .wr_packet_pr2sw        (proc_wr_packet_pr2sw),
    .wr_packet_sw2sr        (strm_packet_sw2sr.wr),
    .wr_packet_d2sw         (wr_packet_d2sw),
    .wr_packet_sw2b_arr     (wr_packet_sw2b_arr),

    .rdrq_packet_pr2sw      (proc_rdrq_packet_pr2sw),
    .rdrq_packet_sr2sw      (strm_packet_sr2sw.rdrq),
    .rdrq_packet_sw2sr      (strm_packet_sw2sr.rdrq),
    .rdrq_packet_d2sw       (rdrq_packet_d2sw),
    .rdrq_packet_pcr2sw     (pc_packet_pcr2sw.rdrq),
    .rdrq_packet_sw2pcr     (pc_packet_sw2pcr.rdrq),
    .rdrq_packet_pcd2sw     (rdrq_packet_pcd2sw),
    .rdrq_packet_sw2b_arr   (rdrq_packet_sw2b_arr),

    .rdrs_packet_sw2pr      (proc_rdrs_packet_sw2pr),
    .rdrs_packet_sr2sw      (strm_packet_sr2sw.rdrs),
    .rdrs_packet_sw2sr      (strm_packet_sw2sr.rdrs),
    .rdrs_packet_sw2d       (rdrs_packet_sw2d),
    .rdrs_packet_pcr2sw     (pc_packet_pcr2sw.rdrs),
    .rdrs_packet_sw2pcr     (pc_packet_sw2pcr.rdrs),
    .rdrs_packet_sw2pcd     (rdrs_packet_sw2pcd),
    .rdrs_packet_b2sw_arr   (rdrs_packet_b2sw_arr),
    .*);

//============================================================================//
// Proc Packet Router
//============================================================================//
glb_core_proc_router glb_core_proc_router (
    .packet_w2e_wsti    (proc_packet_w2e_wsti),
    .packet_e2w_wsto    (proc_packet_e2w_wsto),
    .packet_e2w_esti    (proc_packet_e2w_esti),
    .packet_w2e_esto    (proc_packet_w2e_esto),
    .wr_packet_pr2sw    (proc_wr_packet_pr2sw),
    .rdrq_packet_pr2sw  (proc_rdrq_packet_pr2sw),
    .rdrs_packet_sw2pr  (proc_rdrs_packet_sw2pr),
    .*);

//============================================================================//
// Stream Packet Router
//============================================================================//
glb_core_strm_router glb_core_strm_router (
    .packet_w2e_wsti_d1 (strm_packet_w2e_wsti_d1),
    .packet_e2w_wsto    (strm_packet_e2w_wsto),
    .packet_e2w_esti_d1 (strm_packet_e2w_esti_d1),
    .packet_w2e_esto    (strm_packet_w2e_esto),
    .packet_sw2sr       (strm_packet_sw2sr),
    .packet_sr2sw       (strm_packet_sr2sw),
    .*);

//============================================================================//
// Parallel Config Packet Router
//============================================================================//
glb_core_pc_router glb_core_pc_router (
    .packet_w2e_wsti     (pc_packet_w2e_wsti),
    .packet_e2w_wsto     (pc_packet_e2w_wsto),
    .packet_e2w_esti     (pc_packet_e2w_esti),
    .packet_w2e_esto     (pc_packet_w2e_esto),
    .packet_sw2pcr       (pc_packet_sw2pcr),
    .packet_pcr2sw       (pc_packet_pcr2sw),
    .*);

//============================================================================//
// Interrupt pulse
//============================================================================//
assign strm_f2g_interrupt_pulse = stream_f2g_done_pulse;
assign strm_g2f_interrupt_pulse = stream_g2f_done_pulse;
assign pcfg_g2f_interrupt_pulse = pc_done_pulse;

endmodule
