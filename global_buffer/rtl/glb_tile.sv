/*=============================================================================
** Module: glb_tile.sv
** Description:
**              Global Buffer Tile
** Author: Taeyoung Kong
** Change history: 01/08/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // processor packet
    input  proc_packet_t                    proc_packet_wsti,
    output proc_packet_t                    proc_packet_wsto,
    input  proc_packet_t                    proc_packet_esti,
    output proc_packet_t                    proc_packet_esto,

    // stream packet
    input  strm_packet_t                    strm_packet_wsti,
    output strm_packet_t                    strm_packet_wsto,
    input  strm_packet_t                    strm_packet_esti,
    output strm_packet_t                    strm_packet_esto,

    // stream data f2g
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g,
    input  logic                            stream_data_valid_f2g,
    // stream data g2f
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f,
    output logic                            stream_data_valid_g2f,

    // Config
    cfg_ifc.master                          if_cfg_est_m,
    cfg_ifc.slave                           if_cfg_wst_s,

    // interrupt
    input  logic [2*NUM_TILES-1:0]          interrupt_pulse_wsti,
    output logic [2*NUM_TILES-1:0]          interrupt_pulse_esto,

    // TODO
    // Glb SRAM Config

    // TODO
    // parallel configuration
    input  cgra_cfg_t                       cgra_cfg_wsti,
    output cgra_cfg_t                       cgra_cfg_esto,
    output cgra_cfg_t                       cgra_cfg_g2f
);

//============================================================================//
// Internal Logic
//============================================================================//
packet_t                strm_packet_r2c; // router to core
packet_t                strm_packet_c2r; // core to router

logic                   stream_f2g_done_pulse;
logic                   stream_g2f_done_pulse;
logic [2*NUM_TILES-1:0] interrupt_pulse_esto_int;
logic [2*NUM_TILES-1:0] interrupt_pulse_esto_int_d1;

logic                   cfg_store_dma_invalidate_pulse [QUEUE_DEPTH];
logic                   cfg_load_dma_invalidate_pulse [QUEUE_DEPTH];

cgra_cfg_t              cgra_cfg_g2f_switch;

//============================================================================//
// Configuration registers
//============================================================================//
logic [TILE_SEL_ADDR_WIDTH-1:0] cfg_multi_tile_size;
logic                           cfg_tile_is_start;
logic                           cfg_tile_is_end;
logic                           cfg_store_dma_on;
logic                           cfg_store_dma_auto_on;
dma_st_header_t                 cfg_store_dma_header [QUEUE_DEPTH];
logic                           cfg_load_dma_on;
logic                           cfg_load_dma_auto_on;
dma_ld_header_t                 cfg_load_dma_header [QUEUE_DEPTH];

//============================================================================//
// Configuration Controller
//============================================================================//
glb_tile_cfg glb_tile_cfg (.*);

//============================================================================//
// Global Buffer Core
//============================================================================//
glb_core glb_core (.*);

//============================================================================//
// Proc Packet Router
//============================================================================//
glb_tile_proc_router glb_tile_proc_router (.*);

//============================================================================//
// Stream Packet Router
//============================================================================//
glb_tile_strm_router glb_tile_strm_router (
    .packet_wsti(strm_packet_wsti),
    .packet_wsto(strm_packet_wsto),
    .packet_esti(strm_packet_esti),
    .packet_esto(strm_packet_esto),
    .packet_c2r(strm_packet_c2r),
    .packet_r2c(strm_packet_r2c),
    .*);

//============================================================================//
// CGRA configuration controller
//============================================================================//
glb_tile_cgra_cfg_ctrl glb_tile_cgra_cfg_ctrl (.*);

//============================================================================//
// Interrupt pulse
//============================================================================//
always_comb begin
    interrupt_pulse_esto_int                    = interrupt_pulse_wsti;
    // override with current tile interrupt
    interrupt_pulse_esto_int[2*glb_tile_id]     = stream_f2g_done_pulse;
    interrupt_pulse_esto_int[2*glb_tile_id + 1] = stream_g2f_done_pulse;
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        interrupt_pulse_esto_int_d1 <= '0;
    end
    else if (clk_en) begin
        interrupt_pulse_esto_int_d1 <= interrupt_pulse_esto_int;
    end
end
assign interrupt_pulse_esto = interrupt_pulse_esto_int_d1;

//============================================================================//
// Configuration clock gating pipeline
// Note that flipflop works at negative edge
//============================================================================//
always_ff @(negedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_est_m.wr_clk_en <= 0;
        if_cfg_est_m.rd_clk_en <= 0;
    end
    else begin
        if_cfg_est_m.wr_clk_en <= if_cfg_wst_s.wr_clk_en;
        if_cfg_est_m.rd_clk_en <= if_cfg_wst_s.rd_clk_en;
    end
end

endmodule
