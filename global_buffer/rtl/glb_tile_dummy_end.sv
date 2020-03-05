/*=============================================================================
** Module: glb_tile_dummy_end.sv
** Description:
**              Global Buffer Tile Dummy End
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile_dummy_end (
    input  logic            clk,
    input  logic            reset,

    // processor packet
    input  proc_rq_packet_t proc_rq_packet_lr_wsti,
    output proc_rq_packet_t proc_rq_packet_rl_wsto,
    input  proc_rs_packet_t proc_rs_packet_lr_wsti,
    output proc_rs_packet_t proc_rs_packet_rl_wsto,
    
    // Config
    cfg_ifc.slave           if_cfg_wst_s
);

//============================================================================//
// Dummy function
//============================================================================//
// configuration is not ring interconnect
assign if_cfg_wst_s.rd_data = '0;
assign if_cfg_wst_s.rd_data_valid = 0;

// processor packet ring interrconect
assign proc_rq_packet_rl_wsto = proc_rq_packet_lr_wsti;
assign proc_rs_packet_rl_wsto = proc_rs_packet_lr_wsti;

endmodule
