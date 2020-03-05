/*=============================================================================
** Module: glb_tile_dummy_r.sv
** Description:
**              Global Buffer Tile Dummy Right
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile_dummy_r (
    input  logic                    clk,
    input  logic                    reset,

    axil_ifc.slave                  if_axil,
    cfg_ifc.master                  if_cfg_wst_m,

    input  logic [2*NUM_TILES-1:0]  interrupt_pulse_bundle,
    output logic                    interrupt
);

//============================================================================//
// Internal interface
//============================================================================//
cfg_ifc if_cfg_interrupt ();

//============================================================================//
// Axi4-lite controller
//============================================================================//
glb_tile_dummy_axil_s_ctrl axil_s_ctrl (
    .if_axil            (if_axil),
    .if_cfg_tile        (if_cfg_wst_m),
    .if_cfg_interrupt   (if_cfg_interrupt),
    .*);

//============================================================================//
// Interrupt controller
//============================================================================//
glb_tile_dummy_intr_ctrl intr_ctrl (
    .if_cfg         (if_cfg_interrupt),
    .*);

endmodule
