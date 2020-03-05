/*=============================================================================
** Module: glb_tile_cgra_cfg_ctrl.sv
** Description:
**              Global Buffer Tile Configuration Controller
** Author: Taeyoung Kong
** Change history: 03/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile_cgra_cfg_ctrl (
    input  logic                            clk,
    input  logic                            reset,

    // parallel config ctrl on
    input  logic                            pc_ctrl_on,

    // parallel configuration
    // input  cgra_cfg_t                       cgra_cfg_from_memory,
    // input  cgra_cfg_t                       cgra_cfg_jtag_wsti,
    // output cgra_cfg_t                       cgra_cfg_jtag_esto,
    // input  cgra_cfg_t                       cgra_cfg_pc_wsti,
    // output cgra_cfg_t                       cgra_cfg_pc_esto,
    output cgra_cfg_t                       cgra_cfg_g2f
);

// //============================================================================//
// // Simple router
// //============================================================================//
// cgra_cfg_t cgra_cfg_pc_switched;
// assign cgra_cfg_pc_switched = pc_ctrl_on ? cgra_cfg_from_memory : cgra_cfg_pc_wsti;
// 
// //============================================================================//
// // pipeline registers
// //============================================================================//
// always_ff @ (posedge clk or posedge reset) begin
//     if (reset) begin
//         cgra_cfg_jtag_esto <= '0;
//         cgra_cfg_pc_esto <= '0;
//     end
//     else begin
//         cgra_cfg_jtag_esto <= cgra_cfg_jtag_wsti;
//         cgra_cfg_pc_esto <= cgra_cfg_pc_switched;
//     end
// end
// 
// //============================================================================//
// // output assignment
// //============================================================================//
// // Just ORing works
// assign cgra_cfg_g2f = cgra_cfg_jtag_esto | cgra_cfg_pc_esto;
// TODO
assign cgra_cfg_g2f = '0;

endmodule
