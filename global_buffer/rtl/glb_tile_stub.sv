import global_buffer_pkg::*;

module glb_tile (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // processor packet
    input  proc_rq_packet_t                 proc_rq_packet_lr_wsti,
    output proc_rq_packet_t                 proc_rq_packet_rl_wsto,
    input  proc_rq_packet_t                 proc_rq_packet_rl_esti,
    output proc_rq_packet_t                 proc_rq_packet_lr_esto,

    input  proc_rs_packet_t                 proc_rs_packet_lr_wsti,
    output proc_rs_packet_t                 proc_rs_packet_rl_wsto,
    input  proc_rs_packet_t                 proc_rs_packet_rl_esti,
    output proc_rs_packet_t                 proc_rs_packet_lr_esto,

    // write packet
    input  wr_packet_t                      wr_packet_lr_wsti,
    output wr_packet_t                      wr_packet_rl_wsto,
    input  wr_packet_t                      wr_packet_rl_esti,
    output wr_packet_t                      wr_packet_lr_esto,

    // read req packet
    input  rdrq_packet_t                    rdrq_packet_lr_wsti,
    output rdrq_packet_t                    rdrq_packet_rl_wsto,
    input  rdrq_packet_t                    rdrq_packet_rl_esti,
    output rdrq_packet_t                    rdrq_packet_lr_esto,

    // read res packet
    input  rdrs_packet_t                    rdrs_packet_lr_wsti,
    output rdrs_packet_t                    rdrs_packet_rl_wsto,
    input  rdrs_packet_t                    rdrs_packet_rl_esti,
    output rdrs_packet_t                    rdrs_packet_lr_esto,

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
endmodule
