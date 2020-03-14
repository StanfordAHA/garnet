/*=============================================================================
** Module: glb_dummy_start.sv
** Description:
**              Global Buffer Tile Dummy Start
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_dummy_start (
    input  logic                            clk,
    input  logic                            reset,

    // proc
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

    input  logic [3*NUM_GLB_TILES-1:0]      interrupt_pulse_bundle,
    output logic                            interrupt
);

//============================================================================//
// Internal interface
//============================================================================//
cfg_ifc if_cfg_interrupt ();

//============================================================================//
// Packetize processor data
//============================================================================//
assign proc_packet_esto.wr.wr_en = proc2glb_wr_en;
assign proc_packet_esto.wr.wr_strb = proc2glb_wr_strb;
assign proc_packet_esto.wr.wr_addr = proc2glb_wr_addr;
assign proc_packet_esto.wr.wr_data = proc2glb_wr_data;
assign proc_packet_esto.rdrq.rd_en = proc2glb_rd_en;
assign proc_packet_esto.rdrq.rd_addr = proc2glb_rd_addr;
assign glb2proc_rd_data = proc_packet_esti.rdrs.rd_data;
// just wire to 0
assign proc_packet_esto.rdrs.rd_data = '0;

//============================================================================//
// Axi4-lite controller
//============================================================================//
glb_dummy_axil_s_ctrl axil_s_ctrl (
    .if_axil            (if_axil),
    .if_cfg_tile        (if_cfg_est_m),
    .if_cfg_interrupt   (if_cfg_interrupt),
    .*);

//============================================================================//
// Interrupt controller
//============================================================================//
glb_dummy_glc_reg intr_ctrl (
    .if_cfg         (if_cfg_interrupt),
    .*);

endmodule
