/*=============================================================================
** Module: glb_core_switch.sv
** Description:
**              Global Buffer Core Channel Switch
** Author: Taeyoung Kong
** Change history: 01/27/2020
**      - Implement first version of global buffer core channel switch
**===========================================================================*/
import  global_buffer_pkg::*;

module glb_core_switch (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // wr packet
    input  wr_packet_t                      wr_packet_sr2sw,
    input  wr_packet_t                      wr_packet_pr2sw,
    output wr_packet_t                      wr_packet_sw2sr,
    input  wr_packet_t                      wr_packet_d2sw,
    output wr_packet_t                      wr_packet_sw2b,

    // rdrq packet
    input  rdrq_packet_t                    rdrq_packet_sr2sw,
    input  rdrq_packet_t                    rdrq_packet_pr2sw,
    output rdrq_packet_t                    rdrq_packet_sw2sr,
    input  rdrq_packet_t                    rdrq_packet_d2sw,
    output rdrq_packet_t                    rdrq_packet_sw2b,

    // rdrs packet
    input  rdrs_packet_t                    rdrs_packet_sr2sw,
    output rdrs_packet_t                    rdrs_packet_sw2pr,
    output rdrs_packet_t                    rdrs_packet_sw2sr,
    output rdrs_packet_t                    rdrs_packet_sw2d,
    input  rdrs_packet_t                    rdrs_packet_b2sw_arr [BANKS_PER_TILE],

    // Configuration registers
    input  logic                            cfg_store_dma_on,
    input  logic                            cfg_load_dma_on
);

//============================================================================//
// Internal packet wire
//============================================================================//
// wr
wr_packet_t     wr_packet_sw2b_muxed;
wr_packet_t     wr_packet_sw2b_filtered;
wr_packet_t     wr_packet_sw2b_filtered_d1;

// rdrq
rdrq_packet_t   rdrq_packet_sw2b_muxed;
rdrq_packet_t   rdrq_packet_sw2b_filtered;
rdrq_packet_t   rdrq_packet_sw2b_filtered_d1;
logic [BANK_SEL_ADDR_WIDTH-1:0] rdrq_bank_sel, rdrq_bank_sel_d1, rdrq_bank_sel_d2, rdrq_bank_sel_filtered, rdrq_bank_sel_filtered_d1;

typedef enum logic[2:0] {NONE=3'b001, PROC=3'b010, STRM=3'b100} rdrq_sel_t; 
rdrq_sel_t rdrq_sel_muxed, rdrq_sel_filtered, rdrq_sel_filtered_d1, rdrq_sel, rdrq_sel_d1, rdrq_sel_d2;

// rdrs
rdrs_packet_t rdrs_packet_b2sw_arr_d1 [BANKS_PER_TILE];

//============================================================================//
// Switch operation
// Write packet
//============================================================================//
always_comb begin
    if (wr_packet_pr2sw.wr_en) begin
        wr_packet_sw2b_muxed = wr_packet_pr2sw;
    end
    else if (cfg_store_dma_on) begin
        wr_packet_sw2b_muxed = wr_packet_d2sw;
    end
    else begin
        wr_packet_sw2b_muxed = wr_packet_sr2sw;
    end
end

always_comb begin
    if (wr_packet_sw2b_muxed.wr_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) begin
        wr_packet_sw2b_filtered = wr_packet_sw2b_muxed;
    end
    else begin
        wr_packet_sw2b_filtered = '0;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        wr_packet_sw2b_filtered_d1 <= '0;
    end
    else if (clk_en) begin
        wr_packet_sw2b_filtered_d1 <= wr_packet_sw2b_filtered;
    end
end

assign wr_packet_sw2b = wr_packet_sw2b_filtered_d1;

assign wr_packet_sw2sr = cfg_store_dma_on
                       ? wr_packet_d2sw : wr_packet_sr2sw;

//============================================================================//
// Switch operation
// rdrq packet
//============================================================================//

always_comb begin
    if (rdrq_packet_pr2sw.rd_en == 1) begin
        rdrq_packet_sw2b_muxed = rdrq_packet_pr2sw;
        rdrq_sel_muxed = PROC;
    end
    else if (cfg_load_dma_on == 1) begin
        rdrq_packet_sw2b_muxed = rdrq_packet_d2sw;
        rdrq_sel_muxed = STRM;
    end
    else begin
        rdrq_packet_sw2b_muxed = rdrq_packet_sr2sw;
        rdrq_sel_muxed = STRM;
    end
end

always_comb begin
    if ((rdrq_packet_sw2b_muxed.rd_en == 1) && 
        (rdrq_packet_sw2b_muxed.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id)) begin
        rdrq_packet_sw2b_filtered = rdrq_packet_sw2b_muxed;
        rdrq_sel_filtered = rdrq_sel_muxed;
        rdrq_bank_sel_filtered = rdrq_packet_sw2b_muxed.rd_addr[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH];
    end
    else begin
        rdrq_packet_sw2b_filtered = '0;
        rdrq_sel_filtered = NONE;
        rdrq_bank_sel_filtered = '0;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_packet_sw2b_filtered_d1 <= '0;
        rdrq_sel_filtered_d1 <= NONE;
        rdrq_bank_sel_filtered_d1 <= '0;
    end
    else if (clk_en) begin
        rdrq_packet_sw2b_filtered_d1 <= rdrq_packet_sw2b_filtered;
        rdrq_sel_filtered_d1 <= rdrq_sel_filtered;
        rdrq_bank_sel_filtered_d1 <= rdrq_bank_sel_filtered;
    end
end
assign rdrq_sel = rdrq_sel_filtered_d1;
assign rdrq_bank_sel = rdrq_bank_sel_filtered_d1;

assign rdrq_packet_sw2b = rdrq_packet_sw2b_filtered_d1;

assign rdrq_packet_sw2sr = cfg_load_dma_on
                         ? rdrq_packet_d2sw : rdrq_packet_sr2sw;

//============================================================================//
// Switch operation
// rdrs packet
//============================================================================//
// Read res pipeilne register for timing
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
            rdrs_packet_b2sw_arr_d1[i] <= '0;
        end
    end
    else if (clk_en) begin
        for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
            rdrs_packet_b2sw_arr_d1[i] <= rdrs_packet_b2sw_arr[i];
        end
    end
end

// rdrq pipeline register for synchonization
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_sel_d1 <= NONE;
        rdrq_sel_d2 <= NONE;
        rdrq_bank_sel_d1 <= '0;
        rdrq_bank_sel_d2 <= '0;
    end
    else if (clk_en) begin
        rdrq_sel_d1 <= rdrq_sel;
        rdrq_sel_d2 <= rdrq_sel_d1;
        rdrq_bank_sel_d1 <= rdrq_bank_sel;
        rdrq_bank_sel_d2 <= rdrq_bank_sel_d1;
    end
end

// sw2d
always_comb begin
    if (cfg_load_dma_on == 1) begin
        rdrs_packet_sw2d = rdrs_packet_sr2sw;
    end
    else begin
        rdrs_packet_sw2d = '0;
    end
end

// sw2sr
always_comb begin
    if (rdrq_sel_d2 == STRM) begin
        rdrs_packet_sw2sr = rdrs_packet_b2sw_arr_d1[rdrq_bank_sel_d2];
    end
    else begin
        rdrs_packet_sw2sr = rdrs_packet_sr2sw;
    end
end

// sw2pr
always_comb begin
    if (rdrq_sel_d2 == PROC) begin
        rdrs_packet_sw2pr = rdrs_packet_b2sw_arr_d1[rdrq_bank_sel_d2];
    end
    else begin
        rdrs_packet_sw2pr = '0;
    end
end

endmodule
