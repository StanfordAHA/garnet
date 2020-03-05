/*=============================================================================
** Module: glb_tile_proc_router.sv
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

module glb_tile_proc_router (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // request packet
    input  proc_rq_packet_t                 proc_rq_packet_lr_wsti,
    output proc_rq_packet_t                 proc_rq_packet_rl_wsto,
    input  proc_rq_packet_t                 proc_rq_packet_rl_esti,
    output proc_rq_packet_t                 proc_rq_packet_lr_esto,
    // TODO
    // output proc_rq_packet_t                 proc_rq_packet_r2c,

    // response packet
    input  proc_rs_packet_t                 proc_rs_packet_lr_wsti,
    output proc_rs_packet_t                 proc_rs_packet_rl_wsto,
    input  proc_rs_packet_t                 proc_rs_packet_rl_esti,
    output proc_rs_packet_t                 proc_rs_packet_lr_esto
    // input  proc_rs_packet_t                 proc_rs_packet_c2r
);

//============================================================================//
// Internal Logic
//============================================================================//
// req packet
proc_rq_packet_t proc_rq_packet_lr_wsti_d1;
proc_rq_packet_t proc_rq_packet_rl_esti_d1;

// res packet
proc_rs_packet_t proc_rs_packet_lr_wsti_d1;
proc_rs_packet_t proc_rs_packet_rl_esti_d1;
proc_rs_packet_t proc_rs_packet_c2r_d1;

// is_even indicates If tile_id is even or not
// Warning: Tile id starts from 0
logic is_even;
assign is_even = (glb_tile_id[0] == 0);

//============================================================================//
// packet pipeline register
//============================================================================//
// request
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        proc_rq_packet_lr_wsti_d1 <= '0;
        proc_rq_packet_rl_esti_d1 <= '0;
    end
    else if (clk_en) begin
        proc_rq_packet_lr_wsti_d1 <= proc_rq_packet_lr_wsti;
        proc_rq_packet_rl_esti_d1 <= proc_rq_packet_rl_esti;
    end
end

// response
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        proc_rs_packet_c2r_d1 <= '0;
    end
    else if (clk_en) begin
        proc_rs_packet_c2r_d1 <= '0;
//        proc_rs_packet_c2r_d1 <= proc_rs_packet_c2r;
    end
end

//============================================================================//
// request packet
//============================================================================//
// packet_lr_esto
assign proc_rq_packet_lr_esto = (is_even == 1'b1)
                           ? proc_rq_packet_lr_wsti_d1 : proc_rq_packet_lr_wsti;
// packet_rl_wsto
assign proc_rq_packet_rl_wsto = (is_even == 1'b0)
                           ? proc_rq_packet_rl_esti_d1 : proc_rq_packet_rl_esti;
// TODO
// // packet router to core
// assign proc_rq_packet_r2c = (is_even == 1'b1)
//                           ? proc_rq_packet_lr_esto : proc_rq_packet_rl_wsto;

//============================================================================//
// response packet
//============================================================================//
// packet core to router switch
assign proc_rs_packet_lr_esto = (is_even == 1'b1)
                           ? (proc_rs_packet_c2r_d1.rd_data_valid == 1) 
                           ? proc_rs_packet_c2r_d1 : proc_rs_packet_lr_wsti_d1
                           : proc_rs_packet_lr_wsti;

assign proc_rs_packet_rl_wsto = (is_even == 1'b0)
                           ? (proc_rs_packet_c2r_d1.rd_data_valid == 1) 
                           ? proc_rs_packet_c2r_d1 : proc_rs_packet_rl_esti_d1
                           : proc_rs_packet_rl_esti;

endmodule
