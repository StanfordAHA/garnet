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
    input  packet_t                         proc_packet_wsti,
    output packet_t                         proc_packet_wsto,
    input  packet_t                         proc_packet_esti,
    output packet_t                         proc_packet_esto,

    // stream packet
    input  packet_t                         strm_packet_wsti,
    output packet_t                         strm_packet_wsto,
    input  packet_t                         strm_packet_esti,
    output packet_t                         strm_packet_esto,

    // stream data f2g
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g,
    input  logic                            stream_data_valid_f2g,
    // stream data g2f
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f,
    output logic                            stream_data_valid_g2f,

    // Config
    cfg_ifc.master                          if_cfg_est_m,
    cfg_ifc.slave                           if_cfg_wst_s,

    // trigger
    input  logic [NUM_TILES-1:0]            cfg_strm_start_pulse_wsti,
    output logic [NUM_TILES-1:0]            cfg_strm_start_pulse_esto,
    input  logic [NUM_TILES-1:0]            cfg_pc_start_pulse_wsti,
    output logic [NUM_TILES-1:0]            cfg_pc_start_pulse_esto,

    // interrupt
    input  logic [3*NUM_TILES-1:0]          interrupt_pulse_esti,
    output logic [3*NUM_TILES-1:0]          interrupt_pulse_wsto,

    // TODO
    // Glb SRAM Config

    // parallel configuration
    input  cgra_cfg_t                       cgra_cfg_jtag_wsti,
    output cgra_cfg_t                       cgra_cfg_jtag_esto,
    input  cgra_cfg_t                       cgra_cfg_pc_wsti,
    output cgra_cfg_t                       cgra_cfg_pc_esto,
    output cgra_cfg_t                       cgra_cfg_g2f
);

//============================================================================//
// Internal Logic
//============================================================================//
packet_t                strm_packet_r2c;
packet_t                strm_packet_c2r;
wr_packet_t             proc_wr_packet_r2c;
rdrq_packet_t           proc_rdrq_packet_r2c;
rdrs_packet_t           proc_rdrs_packet_c2r;

logic                   stream_f2g_done_pulse;
logic                   stream_g2f_done_pulse;
logic                   pc_done_pulse;
logic [3*NUM_TILES-1:0] interrupt_pulse_wsto_int;
logic [3*NUM_TILES-1:0] interrupt_pulse_wsto_int_d1;

logic                   cfg_store_dma_invalidate_pulse [QUEUE_DEPTH];
logic                   cfg_load_dma_invalidate_pulse [QUEUE_DEPTH];

cgra_cfg_t              cgra_cfg_c2sw;

//============================================================================//
// Configuration registers
//============================================================================//
logic                   cfg_tile_is_start;
logic                   cfg_tile_is_end;
logic                   cfg_store_dma_on;
logic                   cfg_store_dma_auto_on;
dma_st_header_t         cfg_store_dma_header [QUEUE_DEPTH];
logic                   cfg_load_dma_on;
logic                   cfg_load_dma_auto_on;
dma_ld_header_t         cfg_load_dma_header [QUEUE_DEPTH];
logic                   cfg_pc_dma_on;
dma_pc_header_t         cfg_pc_dma_header;

//============================================================================//
// Configuration Controller
//============================================================================//
glb_tile_cfg glb_tile_cfg (.*);

//============================================================================//
// Global Buffer Core
//============================================================================//
glb_core glb_core (
    .cfg_strm_start_pulse (cfg_strm_start_pulse_wsti[glb_tile_id]),
    .cfg_pc_start_pulse (cfg_pc_start_pulse_wsti[glb_tile_id]),
    .*);

//============================================================================//
// CGRA configuration switch
//============================================================================//
glb_tile_cgra_cfg_switch glb_tile_cgra_cfg_switch (.*);

//============================================================================//
// Trigger pulse
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cfg_strm_start_pulse_esto <= '0;
        cfg_pc_start_pulse_esto <= '0;
    end
    else if (clk_en) begin
        cfg_strm_start_pulse_esto <= cfg_strm_start_pulse_wsti;
        cfg_pc_start_pulse_esto <= cfg_pc_start_pulse_wsti;
    end
end

//============================================================================//
// Interrupt pulse
//============================================================================//
always_comb begin
    interrupt_pulse_wsto_int                            = interrupt_pulse_esti;
    interrupt_pulse_wsto_int[NUM_TILES*0 + glb_tile_id] = stream_f2g_done_pulse;
    interrupt_pulse_wsto_int[NUM_TILES*1 + glb_tile_id] = stream_g2f_done_pulse;
    interrupt_pulse_wsto_int[NUM_TILES*2 + glb_tile_id] = pc_done_pulse;
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        interrupt_pulse_wsto_int_d1 <= '0;
    end
    else if (clk_en) begin
        interrupt_pulse_wsto_int_d1 <= interrupt_pulse_wsto_int;
    end
end
assign interrupt_pulse_wsto = interrupt_pulse_wsto_int_d1;

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
