/*=============================================================================
** Module: glb_tile_dummy_l.sv
** Description:
**              Global Buffer Tile Dummy Left
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile_dummy_l (
    input  logic    clk,
    input  logic    reset,

    // Config
    cfg_ifc.slave   if_cfg_est_s
);

//============================================================================//
// Dummy function
//============================================================================//
assign if_cfg_est_s.rd_data = '0;
assign if_cfg_est_s.rd_data_valid = 0;

endmodule
