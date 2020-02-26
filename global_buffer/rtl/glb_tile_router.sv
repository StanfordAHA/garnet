/*=============================================================================
** Module: glb_tile_router.sv
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

module glb_tile_router (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // write packet
    input  wr_packet_t                      wr_packet_wsti,
    output wr_packet_t                      wr_packet_wsto,
    input  wr_packet_t                      wr_packet_esti,
    output wr_packet_t                      wr_packet_esto,
    input  wr_packet_t                      wr_packet_c2r,
    output wr_packet_t                      wr_packet_r2c,

    // read req packet
    input  rdrq_packet_t                    rdrq_packet_wsti,
    output rdrq_packet_t                    rdrq_packet_wsto,
    input  rdrq_packet_t                    rdrq_packet_esti,
    output rdrq_packet_t                    rdrq_packet_esto,
    input  rdrq_packet_t                    rdrq_packet_c2r,
    output rdrq_packet_t                    rdrq_packet_r2c,

    // read res packet
    input  rdrs_packet_t                    rdrs_packet_wsti,
    output rdrs_packet_t                    rdrs_packet_wsto,
    input  rdrs_packet_t                    rdrs_packet_esti,
    output rdrs_packet_t                    rdrs_packet_esto,
    input  rdrs_packet_t                    rdrs_packet_c2r,
    output rdrs_packet_t                    rdrs_packet_r2c,

    // Configuration Registers
    input  logic                            cfg_tile_is_start,
    input  logic                            cfg_tile_is_end
);

//============================================================================//
// Internal Logic
//============================================================================//
// write packet
wr_packet_t wr_packet_wsti_turned;
wr_packet_t wr_packet_wsto_int;
wr_packet_t wr_packet_esti_turned;
wr_packet_t wr_packet_esto_int;
wr_packet_t wr_packet_c2r_d1;
wr_packet_t wr_packet_r2c_int;

// read req packet
rdrq_packet_t rdrq_packet_wsti_turned;
rdrq_packet_t rdrq_packet_wsto_int;
rdrq_packet_t rdrq_packet_esti_turned;
rdrq_packet_t rdrq_packet_esto_int;
rdrq_packet_t rdrq_packet_c2r_d1;
rdrq_packet_t rdrq_packet_r2c_int;

// read res packet
rdrs_packet_t rdrs_packet_wsti_turned;
rdrs_packet_t rdrs_packet_wsto_int;
rdrs_packet_t rdrs_packet_esti_turned;
rdrs_packet_t rdrs_packet_esto_int;
rdrs_packet_t rdrs_packet_c2r_d1;
rdrs_packet_t rdrs_packet_r2c_int;

// is_even indicates If tile_id is even or not
// Warning: Tile id starts from 0
logic is_even;
assign is_even = (glb_tile_id[0] == 0);

//============================================================================//
// Start/End Tile Turn Around
//============================================================================//
assign wr_packet_wsti_turned    = cfg_tile_is_start ? wr_packet_wsto_int : wr_packet_wsti;
assign rdrq_packet_wsti_turned  = cfg_tile_is_start ? rdrq_packet_wsto_int : rdrq_packet_wsti;
assign rdrs_packet_wsti_turned  = cfg_tile_is_start ? rdrs_packet_wsto_int : rdrs_packet_wsti;
assign wr_packet_esti_turned    = cfg_tile_is_end ? wr_packet_esto_int : wr_packet_esti;
assign rdrq_packet_esti_turned  = cfg_tile_is_end ? rdrq_packet_esto_int : rdrq_packet_esti;
assign rdrs_packet_esti_turned  = cfg_tile_is_end ? rdrs_packet_esto_int : rdrs_packet_esti;

//============================================================================//
// packet core to router pipeline register
//============================================================================//
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        wr_packet_c2r_d1 <= '0;
        rdrq_packet_c2r_d1 <= '0;
        rdrs_packet_c2r_d1 <= '0;
    end
    else if (clk_en) begin
        wr_packet_c2r_d1 <= wr_packet_c2r;
        rdrq_packet_c2r_d1 <= rdrq_packet_c2r;
        rdrs_packet_c2r_d1 <= rdrs_packet_c2r;
    end
end

//============================================================================//
// packet router to core
//============================================================================//
assign wr_packet_r2c_int = (is_even == 1'b1)
                         ? wr_packet_wsti_turned : wr_packet_esti_turned;
assign rdrq_packet_r2c_int = (is_even == 1'b1)
                           ? rdrq_packet_wsti_turned : rdrq_packet_esti_turned;
assign rdrs_packet_r2c_int = (is_even == 1'b1)
                           ? rdrs_packet_wsti_turned : rdrs_packet_esti_turned;

//============================================================================//
// packet_esto
//============================================================================//
assign wr_packet_esto_int = (is_even == 1'b1)
                          ? wr_packet_c2r_d1 : wr_packet_wsti_turned;
assign rdrq_packet_esto_int = (is_even == 1'b1)
                            ? rdrq_packet_c2r_d1 : rdrq_packet_wsti_turned;
assign rdrs_packet_esto_int = (is_even == 1'b1)
                            ? rdrs_packet_c2r_d1 : rdrs_packet_wsti_turned;

//============================================================================//
// packet_wsto
//============================================================================//
assign wr_packet_wsto_int = (is_even == 1'b0)
                          ? wr_packet_c2r_d1 : wr_packet_esti_turned;
assign rdrq_packet_wsto_int = (is_even == 1'b0)
                            ? rdrq_packet_c2r_d1 : rdrq_packet_esti_turned;
assign rdrs_packet_wsto_int = (is_even == 1'b0)
                            ? rdrs_packet_c2r_d1 : rdrs_packet_esti_turned;

//============================================================================//
// Output assignment
//============================================================================//
assign wr_packet_wsto   = wr_packet_wsto_int;
assign wr_packet_esto   = wr_packet_esto_int;
assign wr_packet_r2c    = wr_packet_r2c_int;
assign rdrq_packet_wsto = rdrq_packet_wsto_int;
assign rdrq_packet_esto = rdrq_packet_esto_int;
assign rdrq_packet_r2c  = rdrq_packet_r2c_int;
assign rdrs_packet_wsto = rdrs_packet_wsto_int;
assign rdrs_packet_esto = rdrs_packet_esto_int;
assign rdrs_packet_r2c  = rdrs_packet_r2c_int;

endmodule
