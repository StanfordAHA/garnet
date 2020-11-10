/*=============================================================================
** Module: glb_core_strm_router.sv
** Description:
**              Global Buffer Tile Router
** Author: Taeyoung Kong
** Change history: 
**      01/20/2020
**          - Implement first version of global buffer tile router
**      02/25/2020
**          - Add read packet router
**      03/05/2020
**          - Packetize everything into struct
**===========================================================================*/

module glb_core_strm_router 
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // packet
    input  packet_t                         packet_w2e_wsti_d1,
    output packet_t                         packet_e2w_wsto,
    input  packet_t                         packet_e2w_esti_d1,
    output packet_t                         packet_w2e_esto,
    input  packet_t                         packet_sw2sr,
    output packet_t                         packet_sr2sw,

    // Configuration Registers
    input  logic                            cfg_tile_connected_prev,
    input  logic                            cfg_tile_connected_next
);

//============================================================================//
// Internal Logic
//============================================================================//
// packet
// internal packet
packet_t packet_w2e_wsti_turned, packet_w2e_wsti_turned_d1;
packet_t packet_e2w_wsto_int, packet_e2w_wsto_int_d1;
packet_t packet_e2w_esti_turned, packet_e2w_esti_turned_d1;
packet_t packet_w2e_esto_int, packet_w2e_esto_int_d1;
packet_t packet_sw2sr_d1, packet_sw2sr_d1_next;
packet_t packet_sr2sw_int;

// is_even indicates If tile_id is even or not
// Warning: Tile id starts from 0
logic is_even;
assign is_even = (glb_tile_id[0] == 0);

//============================================================================//
// Start/End Tile Turn Around
//============================================================================//
assign packet_w2e_wsti_turned = (~cfg_tile_connected_prev) ? packet_e2w_wsto_int_d1 : packet_w2e_wsti_d1;
assign packet_e2w_esti_turned = (~cfg_tile_connected_next) ? packet_w2e_esto_int_d1 : packet_e2w_esti_d1;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        packet_w2e_wsti_turned_d1 <= '0;
        packet_e2w_esti_turned_d1 <= '0;
    end
    else if (clk_en) begin
        packet_w2e_wsti_turned_d1 <= packet_w2e_wsti_turned;
        packet_e2w_esti_turned_d1 <= packet_e2w_esti_turned;
    end
end

//============================================================================//
// packet core to router pipeline register
//============================================================================//
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        packet_sw2sr_d1 <= '0;
    end
    else if (clk_en) begin
        packet_sw2sr_d1 <= packet_sw2sr;
    end
end

//============================================================================//
// packet switch
//============================================================================//
assign packet_sr2sw_int = (is_even == 1'b1)
                        ? packet_w2e_wsti_turned : packet_e2w_esti_turned;
assign packet_w2e_esto_int = (is_even == 1'b1)
                           ? packet_sw2sr : packet_w2e_wsti_turned;
assign packet_e2w_wsto_int = (is_even == 1'b0)
                           ? packet_sw2sr : packet_e2w_esti_turned;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        packet_e2w_wsto_int_d1 <= 0;
        packet_w2e_esto_int_d1 <= 0;
    end
    else if (clk_en) begin
        packet_e2w_wsto_int_d1 <= packet_e2w_wsto_int;
        packet_w2e_esto_int_d1 <= packet_w2e_esto_int;
    end
end

//============================================================================//
// Output assignment
//============================================================================//
assign packet_e2w_wsto = packet_e2w_wsto_int_d1;
assign packet_w2e_esto = packet_w2e_esto_int_d1;
assign packet_sr2sw  = packet_sr2sw_int;

endmodule
