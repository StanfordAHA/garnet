/*=============================================================================
** Module: glb_tile_proc_router.sv
** Description:
**              Global Buffer Core Processor Router
** Author: Taeyoung Kong
** Change history: 
**      01/20/2020
**          - Implement first version of global buffer tile router
**      02/25/2020
**          - Add read packet router
**===========================================================================*/

module glb_core_proc_router 
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // processor packet
    input  packet_t                         packet_w2e_wsti,
    output packet_t                         packet_e2w_wsto,
    input  packet_t                         packet_e2w_esti,
    output packet_t                         packet_w2e_esto,

    output wr_packet_t                      wr_packet_pr2sw,
    output rdrq_packet_t                    rdrq_packet_pr2sw,
    input  rdrs_packet_t                    rdrs_packet_sw2pr
);

//============================================================================//
// Internal Logic
//============================================================================//
// packet pipeline
packet_t packet_w2e_wsti_d1;
packet_t packet_e2w_esti_d1;

wr_packet_t wr_packet_pr2sw_filtered, wr_packet_pr2sw_muxed;
rdrq_packet_t rdrq_packet_pr2sw_filtered, rdrq_packet_pr2sw_muxed;
rdrs_packet_t rdrs_packet_sw2pr_d1; 

// is_even indicates If tile_id is even or not
// Warning: Tile id starts from 0
logic is_even;
assign is_even = (glb_tile_id[0] == 0);

//============================================================================//
// packet pipeline register
//============================================================================//
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        packet_w2e_wsti_d1 <= '0;
        packet_e2w_esti_d1 <= '0;
    end
    else begin
        packet_w2e_wsti_d1 <= packet_w2e_wsti;
        packet_e2w_esti_d1 <= packet_e2w_esti;
    end
end

// response
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        rdrs_packet_sw2pr_d1 <= '0;
    end
    else begin
        rdrs_packet_sw2pr_d1 <= rdrs_packet_sw2pr;
    end
end

//============================================================================//
// request packet
//============================================================================//
assign packet_w2e_esto.wr = packet_w2e_wsti_d1.wr;
assign packet_e2w_wsto.wr = packet_e2w_esti_d1.wr;

assign packet_w2e_esto.rdrq = packet_w2e_wsti_d1.rdrq;
assign packet_e2w_wsto.rdrq = packet_e2w_esti_d1.rdrq;

// packet router to core
assign wr_packet_pr2sw_muxed = (is_even == 1'b1)
                             ? packet_w2e_esto.wr : packet_e2w_wsto.wr;
assign rdrq_packet_pr2sw_muxed = (is_even == 1'b1)
                               ? packet_w2e_esto.rdrq : packet_e2w_wsto.rdrq;

assign wr_packet_pr2sw_filtered = (wr_packet_pr2sw_muxed.wr_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) ? wr_packet_pr2sw_muxed : 0;
assign rdrq_packet_pr2sw_filtered = (rdrq_packet_pr2sw_muxed.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) ? rdrq_packet_pr2sw_muxed : 0;

assign wr_packet_pr2sw = wr_packet_pr2sw_filtered;
assign rdrq_packet_pr2sw = rdrq_packet_pr2sw_filtered;


//============================================================================//
// response packet
//============================================================================//
// packet core to router switch
assign packet_w2e_esto.rdrs = (is_even == 1'b1)
                        ? (rdrs_packet_sw2pr_d1.rd_data_valid == 1)
                        ? rdrs_packet_sw2pr_d1 : packet_w2e_wsti_d1.rdrs
                        : packet_w2e_wsti_d1.rdrs;

assign packet_e2w_wsto.rdrs = (is_even == 1'b0)
                        ? (rdrs_packet_sw2pr_d1.rd_data_valid == 1)
                        ? rdrs_packet_sw2pr_d1 : packet_e2w_esti_d1.rdrs
                        : packet_e2w_esti_d1.rdrs;
endmodule
