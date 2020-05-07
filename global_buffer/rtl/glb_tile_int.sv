/*=============================================================================
** Module: glb_tile.sv
** Description:
**              Global Buffer Tile
** Author: Taeyoung Kong
** Change history: 01/08/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_tile_int (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            cgra_stall_in,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // processor packet
    input  packet_t                         proc_packet_w2e_wsti,
    output packet_t                         proc_packet_e2w_wsto,
    input  packet_t                         proc_packet_e2w_esti,
    output packet_t                         proc_packet_w2e_esto,

    // stream packet
    input  packet_t                         strm_packet_w2e_wsti,
    output packet_t                         strm_packet_e2w_wsto,
    input  packet_t                         strm_packet_e2w_esti,
    output packet_t                         strm_packet_w2e_esto,

    // pc packet
    input  rd_packet_t                      pc_packet_w2e_wsti,
    output rd_packet_t                      pc_packet_e2w_wsto,
    input  rd_packet_t                      pc_packet_e2w_esti,
    output rd_packet_t                      pc_packet_w2e_esto,

    // cgra stall
    output logic [CGRA_PER_GLB-1:0]         cgra_stall,

    // stream data
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g [CGRA_PER_GLB],
    input  logic [0:0]                      stream_data_valid_f2g [CGRA_PER_GLB],
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f [CGRA_PER_GLB],
    output logic [0:0]                      stream_data_valid_g2f [CGRA_PER_GLB],

    // Config
    cfg_ifc.master                          if_cfg_est_m,
    cfg_ifc.slave                           if_cfg_wst_s,

    input  logic                            cfg_tile_connected_wsti,
    output logic                            cfg_tile_connected_esto,
    input  logic                            cfg_pc_tile_connected_wsti,
    output logic                            cfg_pc_tile_connected_esto,

    // SRAM Config
    cfg_ifc.master                          if_sram_cfg_est_m,
    cfg_ifc.slave                           if_sram_cfg_wst_s,

    // soft reset
    input  logic                            cgra_soft_reset,

    // trigger
    input  logic                            strm_start_pulse,
    input  logic                            pc_start_pulse,

    // interrupt
    output logic                            strm_f2g_interrupt_pulse,
    output logic                            strm_g2f_interrupt_pulse,
    output logic                            pcfg_g2f_interrupt_pulse,

    // parallel configuration
    input  cgra_cfg_t                       cgra_cfg_jtag_wsti,
    output cgra_cfg_t                       cgra_cfg_jtag_esto,
    input  cgra_cfg_t                       cgra_cfg_pc_wsti,
    output cgra_cfg_t                       cgra_cfg_pc_esto,
    output cgra_cfg_t                       cgra_cfg_g2f [CGRA_PER_GLB]
);

//============================================================================//
// Internal Logic
//============================================================================//
packet_t        strm_packet_r2c;
packet_t        strm_packet_c2r;
wr_packet_t     proc_wr_packet_r2c;
rdrq_packet_t   proc_rdrq_packet_r2c;
rdrs_packet_t   proc_rdrs_packet_c2r;

logic           stream_f2g_done_pulse;
logic           stream_g2f_done_pulse;
logic           pc_done_pulse;

logic           cfg_store_dma_invalidate_pulse [QUEUE_DEPTH];
logic           cfg_load_dma_invalidate_pulse [QUEUE_DEPTH];

cgra_cfg_t      cgra_cfg_c2sw;

//============================================================================//
// Configuration registers
//============================================================================//
logic                       cfg_tile_connected_prev;
logic                       cfg_tile_connected_next;
logic                       cfg_pc_tile_connected_prev;
logic                       cfg_pc_tile_connected_next;
logic [1:0]                 cfg_soft_reset_mux;
logic [1:0]                 cfg_strm_g2f_mux;
logic [1:0]                 cfg_strm_f2g_mux;
logic [1:0]                 cfg_ld_dma_mode;
logic [1:0]                 cfg_st_dma_mode;
logic                       cfg_pc_dma_mode;
logic [LATENCY_WIDTH-1:0]   cfg_latency;
logic [LATENCY_WIDTH-1:0]   cfg_pc_latency;
dma_st_header_t cfg_st_dma_header [QUEUE_DEPTH];
dma_ld_header_t cfg_ld_dma_header [QUEUE_DEPTH];
dma_pc_header_t cfg_pc_dma_header;

//============================================================================//
// assign
//============================================================================//
assign cfg_tile_connected_esto = cfg_tile_connected_next;
assign cfg_tile_connected_prev = cfg_tile_connected_wsti;
assign cfg_pc_tile_connected_esto = cfg_pc_tile_connected_next;
assign cfg_pc_tile_connected_prev = cfg_pc_tile_connected_wsti;

//============================================================================//
// pipeline registers for cgra stall
//============================================================================//
logic [CGRA_PER_GLB-1:0] cgra_stall_d1;
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cgra_stall_d1 <= '0;
    end
    else begin
        for (int i=0; i<CGRA_PER_GLB; i=i+1) begin
            cgra_stall_d1[i] <= cgra_stall_in;
        end
    end
end
assign cgra_stall = cgra_stall_d1;

//============================================================================//
// pipeline registers for start_pulse
//============================================================================//
logic strm_start_pulse_d1, strm_start_pulse_int;
logic pc_start_pulse_d1, pc_start_pulse_int;
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        strm_start_pulse_d1 <= 0;
        pc_start_pulse_d1 <= 0;
    end
    else begin
        strm_start_pulse_d1 <= strm_start_pulse;
        pc_start_pulse_d1 <= pc_start_pulse;
    end
end
assign strm_start_pulse_int = strm_start_pulse_d1;
assign pc_start_pulse_int = pc_start_pulse_d1;

//============================================================================//
// pipeline registers for interrupt
//============================================================================//
logic strm_f2g_interrupt_pulse_int, strm_f2g_interrupt_pulse_int_d1;
logic strm_g2f_interrupt_pulse_int, strm_g2f_interrupt_pulse_int_d1;
logic pcfg_g2f_interrupt_pulse_int, pcfg_g2f_interrupt_pulse_int_d1;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        strm_f2g_interrupt_pulse_int_d1 <= 0;
        strm_g2f_interrupt_pulse_int_d1 <= 0;
        pcfg_g2f_interrupt_pulse_int_d1 <= 0;
    end
    else begin
        strm_f2g_interrupt_pulse_int_d1 <= strm_f2g_interrupt_pulse_int;
        strm_g2f_interrupt_pulse_int_d1 <= strm_g2f_interrupt_pulse_int;
        pcfg_g2f_interrupt_pulse_int_d1 <= pcfg_g2f_interrupt_pulse_int;
    end
end
assign strm_f2g_interrupt_pulse = strm_f2g_interrupt_pulse_int_d1;
assign strm_g2f_interrupt_pulse = strm_g2f_interrupt_pulse_int_d1;
assign pcfg_g2f_interrupt_pulse = pcfg_g2f_interrupt_pulse_int_d1;

//============================================================================//
// Configuration Controller
//============================================================================//
glb_tile_cfg glb_tile_cfg (.*);

//============================================================================//
// Global Buffer Core
//============================================================================//
glb_core glb_core (
    .strm_f2g_interrupt_pulse   (strm_f2g_interrupt_pulse_int),
    .strm_g2f_interrupt_pulse   (strm_g2f_interrupt_pulse_int),
    .pcfg_g2f_interrupt_pulse   (pcfg_g2f_interrupt_pulse_int),
    .strm_start_pulse           (strm_start_pulse_int),
    .pc_start_pulse             (pc_start_pulse_int),
    .*);

//============================================================================//
// CGRA configuration switch
//============================================================================//
glb_tile_pc_switch glb_tile_pc_switch (.*);

endmodule
