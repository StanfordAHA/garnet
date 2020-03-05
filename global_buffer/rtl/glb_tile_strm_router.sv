/*=============================================================================
** Module: glb_tile_strm_router.sv
** Description:
**              Global Buffer Tile Router
** Author: Taeyoung Kong
** Change history: 
**      01/20/2020
**          - Implement first version of global buffer tile router
**      02/25/2020
**          - Add read packet router
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile_strm_router (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // packet
    input  packet_t                         packet_wsti,
    output packet_t                         packet_wsto,
    input  packet_t                         packet_esti,
    output packet_t                         packet_esto,
    input  packet_t                         packet_c2r,
    output packet_t                         packet_r2c,

    // Configuration Registers
    input  logic                            cfg_tile_is_start,
    input  logic                            cfg_tile_is_end
);

//============================================================================//
// Internal Logic
//============================================================================//
// internal packet
packet_t packet_wsti_turned;
packet_t packet_wsto_int;
packet_t packet_esti_turned;
packet_t packet_esto_int;
packet_t packet_c2r_d1;
packet_t packet_r2c_int;

// is_even indicates If tile_id is even or not
// Warning: Tile id starts from 0
logic is_even;
assign is_even = (glb_tile_id[0] == 0);

//============================================================================//
// Start/End Tile Turn Around
//============================================================================//
assign packet_wsti_turned = cfg_tile_is_start ? packet_wsto_int : packet_wsti;
assign packet_esti_turned = cfg_tile_is_end ? packet_esto_int : packet_esti;

//============================================================================//
// packet core to router pipeline register
//============================================================================//
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        packet_c2r_d1 <= '0;
    end
    else if (clk_en) begin
        packet_c2r_d1 <= packet_c2r;
    end
end

//============================================================================//
// packet switch
//============================================================================//
assign packet_r2c_int = (is_even == 1'b1)
                      ? packet_wsti_turned : packet_esti_turned;
assign packet_esto_int = (is_even == 1'b1)
                       ? packet_c2r_d1 : packet_wsti_turned;
assign packet_wsto_int = (is_even == 1'b0)
                       ? packet_c2r_d1 : packet_esti_turned;

//============================================================================//
// Output assignment
//============================================================================//
assign packet_wsto = packet_wsto_int;
assign packet_esto = packet_esto_int;
assign packet_r2c  = packet_r2c_int;

endmodule
