/*=============================================================================
** Module: glb_tile_dummy_start.sv
** Description:
**              Global Buffer Tile Dummy Start
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile_dummy_start (
    input  logic                            clk,
    input  logic                            reset,

    // axi_ifc.slave                   if_axi,
    // TODO
    input  logic                            proc2glb_wr_en,
    input  logic [BANK_DATA_WIDTH/8-1:0]    proc2glb_wr_strb,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc2glb_wr_addr,
    input  logic [BANK_DATA_WIDTH-1:0]      proc2glb_wr_data,
    input  logic                            proc2glb_rd_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc2glb_rd_addr,
    output logic [BANK_DATA_WIDTH-1:0]      glb2proc_rd_data,

    axil_ifc.slave                          if_axil,
    cfg_ifc.master                          if_cfg_est_m,

    // processor packet
    input  packet_t                         proc_packet_esti,
    output packet_t                         proc_packet_esto,

    input  logic [3*NUM_TILES-1:0]          interrupt_pulse_bundle,
    output logic                            interrupt
);

//============================================================================//
// Internal interface
//============================================================================//
cfg_ifc if_cfg_interrupt ();

//============================================================================//
// Axi4 controller
//============================================================================//
glb_tile_dummy_axi_s_ctrl axi_s_ctrl (
    // .if_axi            (if_axi),
    .*);

//============================================================================//
// Axi4-lite controller
//============================================================================//
glb_tile_dummy_axil_s_ctrl axil_s_ctrl (
    .if_axil            (if_axil),
    .if_cfg_tile        (if_cfg_est_m),
    .if_cfg_interrupt   (if_cfg_interrupt),
    .*);

//============================================================================//
// Interrupt controller
//============================================================================//
glb_tile_dummy_intr_ctrl intr_ctrl (
    .if_cfg         (if_cfg_interrupt),
    .*);

endmodule
