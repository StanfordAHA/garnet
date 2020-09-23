/*=============================================================================
** Module: glb_tile_cfg.sv
** Description:
**              Global Buffer Tile Configuration Registers
** Author: Taeyoung Kong
** Change history: 02/06/2020 - Implement first version
**===========================================================================*/

module glb_tile_cfg 
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // Config
    cfg_ifc.slave                           if_cfg_wst_s,
    cfg_ifc.master                          if_cfg_est_m,

    // register clear
    input  logic                            cfg_store_dma_invalidate_pulse [QUEUE_DEPTH],
    input  logic                            cfg_load_dma_invalidate_pulse [QUEUE_DEPTH],

    // registers
    output logic                            cfg_tile_connected_next,
    output logic                            cfg_pc_tile_connected_next,
    output logic [1:0]                      cfg_strm_g2f_mux,
    output logic [1:0]                      cfg_strm_f2g_mux,
    output logic [1:0]                      cfg_ld_dma_mode,
    output logic [1:0]                      cfg_st_dma_mode,
    output logic                            cfg_pc_dma_mode,
    output logic [1:0]                      cfg_soft_reset_mux,
    output logic                            cfg_use_valid,
    output logic [LATENCY_WIDTH-1:0]        cfg_latency,
    output logic [LATENCY_WIDTH-1:0]        cfg_pc_latency,
    output dma_st_header_t                  cfg_st_dma_header [QUEUE_DEPTH],
    output dma_ld_header_t                  cfg_ld_dma_header [QUEUE_DEPTH],
    output dma_pc_header_t                  cfg_pc_dma_header
);

//============================================================================//
// Local Parameter
//============================================================================//
// TODO: This should be variable depending on the number of configuration registers
localparam int REG_ADDR_WIDTH = 6;

//============================================================================//
// Internal logic
//============================================================================//
logic [AXI_DATA_WIDTH-1:0]       h2d_pio_dec_write_data;
logic [REG_ADDR_WIDTH-1:0]       h2d_pio_dec_address;
logic                            h2d_pio_dec_read;
logic                            h2d_pio_dec_write;

logic [AXI_DATA_WIDTH-1:0]       d2h_dec_pio_read_data;
logic                            d2h_dec_pio_ack;
logic                            d2h_dec_pio_nack;

//============================================================================//
// Internal config registers
//============================================================================//
logic h2l_st_dma_header_0_validate_validate_hwclr;
logic h2l_st_dma_header_1_validate_validate_hwclr;
logic h2l_st_dma_header_2_validate_validate_hwclr;
logic h2l_st_dma_header_3_validate_validate_hwclr;
logic h2l_ld_dma_header_0_validate_validate_hwclr;
logic h2l_ld_dma_header_1_validate_validate_hwclr;
logic h2l_ld_dma_header_2_validate_validate_hwclr;
logic h2l_ld_dma_header_3_validate_validate_hwclr;

logic l2h_tile_ctrl_tile_connected_r;
logic l2h_tile_ctrl_pc_tile_connected_r;
logic  [1:0] l2h_tile_ctrl_strm_g2f_mux_r;
logic  [1:0] l2h_tile_ctrl_strm_f2g_mux_r;
logic  [1:0] l2h_tile_ctrl_ld_dma_mode_r;
logic  [1:0] l2h_tile_ctrl_st_dma_mode_r;
logic l2h_tile_ctrl_pc_dma_mode_r;
logic  [LATENCY_WIDTH-1:0] l2h_latency_strm_latency_r;
logic  [1:0] l2h_tile_ctrl_soft_reset_mux_r;
logic  l2h_tile_ctrl_use_valid_r;
logic  [LATENCY_WIDTH-1:0] l2h_latency_pc_latency_r;
logic l2h_st_dma_header_0_validate_validate_r;
logic  [21:0] l2h_st_dma_header_0_start_addr_start_addr_r;
logic  [20:0] l2h_st_dma_header_0_num_words_num_words_r;
logic l2h_st_dma_header_1_validate_validate_r;
logic  [21:0] l2h_st_dma_header_1_start_addr_start_addr_r;
logic  [20:0] l2h_st_dma_header_1_num_words_num_words_r;
logic l2h_st_dma_header_2_validate_validate_r;
logic  [21:0] l2h_st_dma_header_2_start_addr_start_addr_r;
logic  [20:0] l2h_st_dma_header_2_num_words_num_words_r;
logic l2h_st_dma_header_3_validate_validate_r;
logic  [21:0] l2h_st_dma_header_3_start_addr_start_addr_r;
logic  [20:0] l2h_st_dma_header_3_num_words_num_words_r;
logic l2h_ld_dma_header_0_validate_validate_r;
logic  [21:0] l2h_ld_dma_header_0_start_addr_start_addr_r;
logic  [15:0] l2h_ld_dma_header_0_active_ctrl_num_active_words_r;
logic  [15:0] l2h_ld_dma_header_0_active_ctrl_num_inactive_words_r;
logic  [20:0] l2h_ld_dma_header_0_iter_ctrl_0_range_r;
logic  [10:0] l2h_ld_dma_header_0_iter_ctrl_0_stride_r;
logic  [20:0] l2h_ld_dma_header_0_iter_ctrl_1_range_r;
logic  [10:0] l2h_ld_dma_header_0_iter_ctrl_1_stride_r;
logic  [20:0] l2h_ld_dma_header_0_iter_ctrl_2_range_r;
logic  [10:0] l2h_ld_dma_header_0_iter_ctrl_2_stride_r;
logic  [20:0] l2h_ld_dma_header_0_iter_ctrl_3_range_r;
logic  [10:0] l2h_ld_dma_header_0_iter_ctrl_3_stride_r;
logic l2h_ld_dma_header_1_validate_validate_r;
logic  [21:0] l2h_ld_dma_header_1_start_addr_start_addr_r;
logic  [15:0] l2h_ld_dma_header_1_active_ctrl_num_active_words_r;
logic  [15:0] l2h_ld_dma_header_1_active_ctrl_num_inactive_words_r;
logic  [20:0] l2h_ld_dma_header_1_iter_ctrl_0_range_r;
logic  [10:0] l2h_ld_dma_header_1_iter_ctrl_0_stride_r;
logic  [20:0] l2h_ld_dma_header_1_iter_ctrl_1_range_r;
logic  [10:0] l2h_ld_dma_header_1_iter_ctrl_1_stride_r;
logic  [20:0] l2h_ld_dma_header_1_iter_ctrl_2_range_r;
logic  [10:0] l2h_ld_dma_header_1_iter_ctrl_2_stride_r;
logic  [20:0] l2h_ld_dma_header_1_iter_ctrl_3_range_r;
logic  [10:0] l2h_ld_dma_header_1_iter_ctrl_3_stride_r;
logic l2h_ld_dma_header_2_validate_validate_r;
logic  [21:0] l2h_ld_dma_header_2_start_addr_start_addr_r;
logic  [15:0] l2h_ld_dma_header_2_active_ctrl_num_active_words_r;
logic  [15:0] l2h_ld_dma_header_2_active_ctrl_num_inactive_words_r;
logic  [20:0] l2h_ld_dma_header_2_iter_ctrl_0_range_r;
logic  [10:0] l2h_ld_dma_header_2_iter_ctrl_0_stride_r;
logic  [20:0] l2h_ld_dma_header_2_iter_ctrl_1_range_r;
logic  [10:0] l2h_ld_dma_header_2_iter_ctrl_1_stride_r;
logic  [20:0] l2h_ld_dma_header_2_iter_ctrl_2_range_r;
logic  [10:0] l2h_ld_dma_header_2_iter_ctrl_2_stride_r;
logic  [20:0] l2h_ld_dma_header_2_iter_ctrl_3_range_r;
logic  [10:0] l2h_ld_dma_header_2_iter_ctrl_3_stride_r;
logic l2h_ld_dma_header_3_validate_validate_r;
logic  [21:0] l2h_ld_dma_header_3_start_addr_start_addr_r;
logic  [15:0] l2h_ld_dma_header_3_active_ctrl_num_active_words_r;
logic  [15:0] l2h_ld_dma_header_3_active_ctrl_num_inactive_words_r;
logic  [20:0] l2h_ld_dma_header_3_iter_ctrl_0_range_r;
logic  [10:0] l2h_ld_dma_header_3_iter_ctrl_0_stride_r;
logic  [20:0] l2h_ld_dma_header_3_iter_ctrl_1_range_r;
logic  [10:0] l2h_ld_dma_header_3_iter_ctrl_1_stride_r;
logic  [20:0] l2h_ld_dma_header_3_iter_ctrl_2_range_r;
logic  [10:0] l2h_ld_dma_header_3_iter_ctrl_2_stride_r;
logic  [20:0] l2h_ld_dma_header_3_iter_ctrl_3_range_r;
logic  [10:0] l2h_ld_dma_header_3_iter_ctrl_3_stride_r;
logic l2h_pc_dma_header_validate_validate_r;
logic  [21:0] l2h_pc_dma_header_start_addr_start_addr_r;
logic  [18:0] l2h_pc_dma_header_num_cfg_num_cfgs_r;

//============================================================================//
// assigns
//============================================================================//
assign h2l_st_dma_header_0_validate_validate_hwclr  = cfg_store_dma_invalidate_pulse[0];
assign h2l_st_dma_header_1_validate_validate_hwclr  = cfg_store_dma_invalidate_pulse[1];
assign h2l_st_dma_header_2_validate_validate_hwclr  = cfg_store_dma_invalidate_pulse[2];
assign h2l_st_dma_header_3_validate_validate_hwclr  = cfg_store_dma_invalidate_pulse[3];
assign h2l_ld_dma_header_0_validate_validate_hwclr  = cfg_load_dma_invalidate_pulse[0];
assign h2l_ld_dma_header_1_validate_validate_hwclr  = cfg_load_dma_invalidate_pulse[1];
assign h2l_ld_dma_header_2_validate_validate_hwclr  = cfg_load_dma_invalidate_pulse[2];
assign h2l_ld_dma_header_3_validate_validate_hwclr  = cfg_load_dma_invalidate_pulse[3];

assign cfg_tile_connected_next                  = l2h_tile_ctrl_tile_connected_r;
assign cfg_pc_tile_connected_next               = l2h_tile_ctrl_pc_tile_connected_r;
assign cfg_strm_g2f_mux                         = l2h_tile_ctrl_strm_g2f_mux_r;
assign cfg_strm_f2g_mux                         = l2h_tile_ctrl_strm_f2g_mux_r;
assign cfg_ld_dma_mode                          = l2h_tile_ctrl_ld_dma_mode_r;
assign cfg_st_dma_mode                          = l2h_tile_ctrl_st_dma_mode_r;
assign cfg_pc_dma_mode                          = l2h_tile_ctrl_pc_dma_mode_r;

assign cfg_soft_reset_mux                       = l2h_tile_ctrl_soft_reset_mux_r;
assign cfg_use_valid                            = l2h_tile_ctrl_use_valid_r;
assign cfg_latency                              = l2h_latency_strm_latency_r;
assign cfg_pc_latency                           = l2h_latency_pc_latency_r;

assign cfg_st_dma_header[0].valid               = l2h_st_dma_header_0_validate_validate_r;
assign cfg_st_dma_header[0].start_addr          = l2h_st_dma_header_0_start_addr_start_addr_r;
assign cfg_st_dma_header[0].num_words           = l2h_st_dma_header_0_num_words_num_words_r;
assign cfg_st_dma_header[1].valid               = l2h_st_dma_header_1_validate_validate_r;
assign cfg_st_dma_header[1].start_addr          = l2h_st_dma_header_1_start_addr_start_addr_r;
assign cfg_st_dma_header[1].num_words           = l2h_st_dma_header_1_num_words_num_words_r;
assign cfg_st_dma_header[2].valid               = l2h_st_dma_header_2_validate_validate_r;
assign cfg_st_dma_header[2].start_addr          = l2h_st_dma_header_2_start_addr_start_addr_r;
assign cfg_st_dma_header[2].num_words           = l2h_st_dma_header_2_num_words_num_words_r;
assign cfg_st_dma_header[3].valid               = l2h_st_dma_header_3_validate_validate_r;
assign cfg_st_dma_header[3].start_addr          = l2h_st_dma_header_3_start_addr_start_addr_r;
assign cfg_st_dma_header[3].num_words           = l2h_st_dma_header_3_num_words_num_words_r;

assign cfg_ld_dma_header[0].valid               = l2h_ld_dma_header_0_validate_validate_r;
assign cfg_ld_dma_header[0].start_addr          = l2h_ld_dma_header_0_start_addr_start_addr_r;
assign cfg_ld_dma_header[0].num_active_words    = l2h_ld_dma_header_0_active_ctrl_num_active_words_r;
assign cfg_ld_dma_header[0].num_inactive_words  = l2h_ld_dma_header_0_active_ctrl_num_inactive_words_r;
assign cfg_ld_dma_header[0].iteration[0].range  = l2h_ld_dma_header_0_iter_ctrl_0_range_r;
assign cfg_ld_dma_header[0].iteration[0].stride = l2h_ld_dma_header_0_iter_ctrl_0_stride_r;
assign cfg_ld_dma_header[0].iteration[1].range  = l2h_ld_dma_header_0_iter_ctrl_1_range_r;
assign cfg_ld_dma_header[0].iteration[1].stride = l2h_ld_dma_header_0_iter_ctrl_1_stride_r;
assign cfg_ld_dma_header[0].iteration[2].range  = l2h_ld_dma_header_0_iter_ctrl_2_range_r;
assign cfg_ld_dma_header[0].iteration[2].stride = l2h_ld_dma_header_0_iter_ctrl_2_stride_r;
assign cfg_ld_dma_header[0].iteration[3].range  = l2h_ld_dma_header_0_iter_ctrl_3_range_r;
assign cfg_ld_dma_header[0].iteration[3].stride = l2h_ld_dma_header_0_iter_ctrl_3_stride_r;
assign cfg_ld_dma_header[1].valid               = l2h_ld_dma_header_1_validate_validate_r;
assign cfg_ld_dma_header[1].start_addr          = l2h_ld_dma_header_1_start_addr_start_addr_r;
assign cfg_ld_dma_header[1].num_active_words    = l2h_ld_dma_header_1_active_ctrl_num_active_words_r;
assign cfg_ld_dma_header[1].num_inactive_words  = l2h_ld_dma_header_1_active_ctrl_num_inactive_words_r;
assign cfg_ld_dma_header[1].iteration[0].range  = l2h_ld_dma_header_1_iter_ctrl_0_range_r;
assign cfg_ld_dma_header[1].iteration[0].stride = l2h_ld_dma_header_1_iter_ctrl_0_stride_r;
assign cfg_ld_dma_header[1].iteration[1].range  = l2h_ld_dma_header_1_iter_ctrl_1_range_r;
assign cfg_ld_dma_header[1].iteration[1].stride = l2h_ld_dma_header_1_iter_ctrl_1_stride_r;
assign cfg_ld_dma_header[1].iteration[2].range  = l2h_ld_dma_header_1_iter_ctrl_2_range_r;
assign cfg_ld_dma_header[1].iteration[2].stride = l2h_ld_dma_header_1_iter_ctrl_2_stride_r;
assign cfg_ld_dma_header[1].iteration[3].range  = l2h_ld_dma_header_1_iter_ctrl_3_range_r;
assign cfg_ld_dma_header[1].iteration[3].stride = l2h_ld_dma_header_1_iter_ctrl_3_stride_r;
assign cfg_ld_dma_header[2].valid               = l2h_ld_dma_header_2_validate_validate_r;
assign cfg_ld_dma_header[2].start_addr          = l2h_ld_dma_header_2_start_addr_start_addr_r;
assign cfg_ld_dma_header[2].num_active_words    = l2h_ld_dma_header_2_active_ctrl_num_active_words_r;
assign cfg_ld_dma_header[2].num_inactive_words  = l2h_ld_dma_header_2_active_ctrl_num_inactive_words_r;
assign cfg_ld_dma_header[2].iteration[0].range  = l2h_ld_dma_header_2_iter_ctrl_0_range_r;
assign cfg_ld_dma_header[2].iteration[0].stride = l2h_ld_dma_header_2_iter_ctrl_0_stride_r;
assign cfg_ld_dma_header[2].iteration[1].range  = l2h_ld_dma_header_2_iter_ctrl_1_range_r;
assign cfg_ld_dma_header[2].iteration[1].stride = l2h_ld_dma_header_2_iter_ctrl_1_stride_r;
assign cfg_ld_dma_header[2].iteration[2].range  = l2h_ld_dma_header_2_iter_ctrl_2_range_r;
assign cfg_ld_dma_header[2].iteration[2].stride = l2h_ld_dma_header_2_iter_ctrl_2_stride_r;
assign cfg_ld_dma_header[2].iteration[3].range  = l2h_ld_dma_header_2_iter_ctrl_3_range_r;
assign cfg_ld_dma_header[2].iteration[3].stride = l2h_ld_dma_header_2_iter_ctrl_3_stride_r;
assign cfg_ld_dma_header[3].valid               = l2h_ld_dma_header_3_validate_validate_r;
assign cfg_ld_dma_header[3].start_addr          = l2h_ld_dma_header_3_start_addr_start_addr_r;
assign cfg_ld_dma_header[3].num_active_words    = l2h_ld_dma_header_3_active_ctrl_num_active_words_r;
assign cfg_ld_dma_header[3].num_inactive_words  = l2h_ld_dma_header_3_active_ctrl_num_inactive_words_r;
assign cfg_ld_dma_header[3].iteration[0].range  = l2h_ld_dma_header_3_iter_ctrl_0_range_r;
assign cfg_ld_dma_header[3].iteration[0].stride = l2h_ld_dma_header_3_iter_ctrl_0_stride_r;
assign cfg_ld_dma_header[3].iteration[1].range  = l2h_ld_dma_header_3_iter_ctrl_1_range_r;
assign cfg_ld_dma_header[3].iteration[1].stride = l2h_ld_dma_header_3_iter_ctrl_1_stride_r;
assign cfg_ld_dma_header[3].iteration[2].range  = l2h_ld_dma_header_3_iter_ctrl_2_range_r;
assign cfg_ld_dma_header[3].iteration[2].stride = l2h_ld_dma_header_3_iter_ctrl_2_stride_r;
assign cfg_ld_dma_header[3].iteration[3].range  = l2h_ld_dma_header_3_iter_ctrl_3_range_r;
assign cfg_ld_dma_header[3].iteration[3].stride = l2h_ld_dma_header_3_iter_ctrl_3_stride_r;

assign cfg_pc_dma_header.start_addr             = l2h_pc_dma_header_start_addr_start_addr_r;
assign cfg_pc_dma_header.num_cfgs               = l2h_pc_dma_header_num_cfg_num_cfgs_r;

//============================================================================//
// Instantiation
//============================================================================//

glb_tile_cfg_ctrl #(.REG_ADDR_WIDTH(REG_ADDR_WIDTH)) glb_tile_cfg_ctrl (.*);

glb_pio glb_pio (.*);


endmodule
