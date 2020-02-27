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

    // write packet
    input  wr_packet_t                      wr_packet_wsti,
    output wr_packet_t                      wr_packet_wsto,
    input  wr_packet_t                      wr_packet_esti,
    output wr_packet_t                      wr_packet_esto,
    // read req packet
    input  rdrq_packet_t                    rdrq_packet_wsti,
    output rdrq_packet_t                    rdrq_packet_wsto,
    input  rdrq_packet_t                    rdrq_packet_esti,
    output rdrq_packet_t                    rdrq_packet_esto,
    // read res packet
    input  rdrs_packet_t                    rdrs_packet_wsti,
    output rdrs_packet_t                    rdrs_packet_wsto,
    input  rdrs_packet_t                    rdrs_packet_esti,
    output rdrs_packet_t                    rdrs_packet_esto,

    // stream data f2g
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g,
    input  logic                            stream_data_valid_f2g,
    // stream data g2f
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f,
    output logic                            stream_data_valid_g2f,

    // Config
    input  logic                            cfg_wr_clk_en_esti,
    input  logic                            cfg_rd_clk_en_esti,
    output logic                            cfg_wr_clk_en_wsto,
    output logic                            cfg_rd_clk_en_wsto,
    cfg_ifc.slave                           if_cfg_est_s,
    cfg_ifc.master                          if_cfg_wst_m,

    // interrupt
    input  logic [2*NUM_TILES-1:0]          interrupt_pulse_wsti,
    output logic [2*NUM_TILES-1:0]          interrupt_pulse_esto,

    // TODO
    // Glb SRAM Config

    // TODO
    // parallel configuration
    input  cgra_cfg_t                       cgra_cfg_esti,
    output cgra_cfg_t                       cgra_cfg_wsto,
    output cgra_cfg_t                       cgra_cfg_g2f
);

//============================================================================//
// Internal Logic
//============================================================================//
wr_packet_t     wr_packet_r2c; // router to core
wr_packet_t     wr_packet_c2r; // core to router
rdrq_packet_t   rdrq_packet_r2c; // router to core
rdrq_packet_t   rdrq_packet_c2r; // core to router
rdrs_packet_t   rdrs_packet_r2c; // router to core
rdrs_packet_t   rdrs_packet_c2r; // core to router

logic                   stream_f2g_done_pulse;
logic                   stream_g2f_done_pulse;
logic [2*NUM_TILES-1:0] interrupt_pulse_esto_int;
logic [2*NUM_TILES-1:0] interrupt_pulse_esto_int_d1;

logic                   cfg_store_dma_invalidate_pulse [QUEUE_DEPTH];
logic                   cfg_load_dma_invalidate_pulse [QUEUE_DEPTH];

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
glb_tile_cfg glb_tile_cfg (
    .cfg_wr_clk_en (cfg_wr_clk_en_esti),
    .cfg_rd_clk_en (cfg_rd_clk_en_esti),
    .*);

//============================================================================//
// Global Buffer Core
//============================================================================//
glb_core glb_core (.*);

//============================================================================//
// Router
//============================================================================//
glb_tile_router glb_tile_router (.*);

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
        cfg_wr_clk_en_wsto <= 0;
        cfg_rd_clk_en_wsto <= 0;
    end
    else begin
        cfg_wr_clk_en_wsto <= cfg_wr_clk_en_esti;
        cfg_rd_clk_en_wsto <= cfg_rd_clk_en_esti;
    end
end

//============================================================================//
// CGRA cfg from glc pipeline
//============================================================================//
always_ff @(negedge clk or posedge reset) begin
    if (reset) begin
        cgra_cfg_wsto <= '0;
    end
    else begin
        cgra_cfg_wsto <= cgra_cfg_esti;
    end
end
// TODO
assign cgra_cfg_g2f = cgra_cfg_wsto;

endmodule
