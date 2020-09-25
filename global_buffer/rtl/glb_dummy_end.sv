/*=============================================================================
** Module: glb_dummy_end.sv
** Description:
**              Global Buffer Tile Dummy End
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/

module glb_dummy_end 
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    // processor packet
    input  packet_t         proc_packet_w2e_wsti,
    output packet_t         proc_packet_e2w_wsto,

    // stream packet
    output packet_t         strm_packet_e2w_wsto,
    
    // pc packet
    output rd_packet_t      pc_packet_e2w_wsto,
    
    // Config
    cfg_ifc.slave           if_cfg_wst_s,
    cfg_ifc.slave           if_sram_cfg_wst_s
);

//============================================================================//
// Dummy function
//============================================================================//
// configuration is not ring interconnect
assign if_cfg_wst_s.rd_data = '0;
assign if_cfg_wst_s.rd_data_valid = 0;
assign if_sram_cfg_wst_s.rd_data = '0;
assign if_sram_cfg_wst_s.rd_data_valid = 0;

// processor packet ring interrconect
assign proc_packet_e2w_wsto = proc_packet_w2e_wsti;

// strm packet assign to 0
assign strm_packet_e2w_wsto = '0;

// pc packet assign to 0
assign pc_packet_e2w_wsto = '0;

endmodule
