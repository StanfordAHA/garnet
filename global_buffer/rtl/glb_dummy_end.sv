/*=============================================================================
** Module: glb_dummy_end.sv
** Description:
**              Global Buffer Tile Dummy End
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_dummy_end (
    input  logic            clk,
    input  logic            reset,

    // processor packet
    input  packet_t         proc_packet_wsti,
    output packet_t         proc_packet_wsto,
    
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
assign proc_packet_wsto = proc_packet_wsti;

endmodule
