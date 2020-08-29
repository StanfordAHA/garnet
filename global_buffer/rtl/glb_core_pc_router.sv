/*=============================================================================
** Module: glb_core_pc_router.sv
** Description:
**              Global Buffer Tile Parallel Configuration Packet Router
** Author: Taeyoung Kong
** Change history: 
**      04/06/2020
**          - Implement first version of global buffer parallel configuration 
**            tile router
**===========================================================================*/

module glb_core_pc_router 
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // packet
    input  rd_packet_t                      packet_w2e_wsti,
    output rd_packet_t                      packet_e2w_wsto,
    input  rd_packet_t                      packet_e2w_esti,
    output rd_packet_t                      packet_w2e_esto,
    input  rd_packet_t                      packet_sw2pcr,
    output rd_packet_t                      packet_pcr2sw,

    // Configuration Registers
    input  logic                            cfg_pc_tile_connected_prev,
    input  logic                            cfg_pc_tile_connected_next
);

//============================================================================//
// Internal Logic
//============================================================================//
// internal packet
rd_packet_t packet_w2e_wsti_turned, packet_w2e_wsti_turned_d1;
rd_packet_t packet_e2w_wsto_int;
rd_packet_t packet_e2w_esti_turned, packet_e2w_esti_turned_d1;
rd_packet_t packet_w2e_esto_int;
rd_packet_t packet_sw2pcr_d1;
rd_packet_t packet_pcr2sw_int;

// is_even indicates If tile_id is even or not
// Warning: Tile id starts from 0
logic is_even;
assign is_even = (glb_tile_id[0] == 0);

//============================================================================//
// Start/End Tile Turn Around
//============================================================================//
assign packet_w2e_wsti_turned = (~cfg_pc_tile_connected_prev) ? packet_e2w_wsto_int : packet_w2e_wsti;
assign packet_e2w_esti_turned = (~cfg_pc_tile_connected_next) ? packet_w2e_esto_int : packet_e2w_esti;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        packet_w2e_wsti_turned_d1 <= '0;
        packet_e2w_esti_turned_d1 <= '0;
    end
    else begin
        packet_w2e_wsti_turned_d1 <= packet_w2e_wsti_turned;
        packet_e2w_esti_turned_d1 <= packet_e2w_esti_turned;
    end
end

//============================================================================//
// packet core to router pipeline register
//============================================================================//
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        packet_sw2pcr_d1 <= '0;
    end
    else begin
        packet_sw2pcr_d1 <= packet_sw2pcr;
    end
end

//============================================================================//
// packet switch
//============================================================================//
assign packet_pcr2sw_int = (is_even == 1'b1)
                        ? packet_w2e_wsti_turned : packet_e2w_esti_turned;
assign packet_w2e_esto_int = (is_even == 1'b1)
                       ? packet_sw2pcr_d1 : packet_w2e_wsti_turned_d1;
assign packet_e2w_wsto_int = (is_even == 1'b0)
                       ? packet_sw2pcr_d1 : packet_e2w_esti_turned_d1;

//============================================================================//
// Output assignment
//============================================================================//
assign packet_e2w_wsto = packet_e2w_wsto_int;
assign packet_w2e_esto = packet_w2e_esto_int;
assign packet_pcr2sw  = packet_pcr2sw_int;

endmodule
