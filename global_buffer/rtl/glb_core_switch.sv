/*=============================================================================
** Module: glb_core_switch.sv
** Description:
**              Global Buffer Core Channel Switch
** Author: Taeyoung Kong
** Change history: 01/27/2020
**      - Implement first version of global buffer core channel switch
**===========================================================================*/
import  global_buffer_pkg::*;
import global_buffer_param::*;

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
    output wr_packet_t                      wr_packet_sw2b_arr [BANKS_PER_TILE],

    // rdrq packet
    input  rdrq_packet_t                    rdrq_packet_pr2sw,
    input  rdrq_packet_t                    rdrq_packet_sr2sw,
    output rdrq_packet_t                    rdrq_packet_sw2sr,
    input  rdrq_packet_t                    rdrq_packet_d2sw,
    input  rdrq_packet_t                    rdrq_packet_pcr2sw,
    output rdrq_packet_t                    rdrq_packet_sw2pcr,
    input  rdrq_packet_t                    rdrq_packet_pcd2sw,
    output rdrq_packet_t                    rdrq_packet_sw2b_arr [BANKS_PER_TILE],

    // rdrs packet
    output rdrs_packet_t                    rdrs_packet_sw2pr,
    input  rdrs_packet_t                    rdrs_packet_sr2sw,
    output rdrs_packet_t                    rdrs_packet_sw2sr,
    output rdrs_packet_t                    rdrs_packet_sw2d,
    input  rdrs_packet_t                    rdrs_packet_pcr2sw,
    output rdrs_packet_t                    rdrs_packet_sw2pcr,
    output rdrs_packet_t                    rdrs_packet_sw2pcd,
    input  rdrs_packet_t                    rdrs_packet_b2sw_arr [BANKS_PER_TILE],

    // Configuration registers
    input  logic [1:0]                      cfg_st_dma_mode,
    input  logic [1:0]                      cfg_ld_dma_mode,
    input  logic                            cfg_pc_dma_mode
);

//============================================================================//
// Internal wire
//============================================================================//
// wr
wr_packet_t     wr_packet_sr2sw_d1;
wr_packet_t     wr_packet_pr2sw_d1;
wr_packet_t     wr_packet_d2sw_d1;
wr_packet_t     wr_packet_sw2b_muxed;
wr_packet_t     wr_packet_sw2b_filtered;

// rdrq
rdrq_packet_t   rdrq_packet_pr2sw_d1;
rdrq_packet_t   rdrq_packet_sr2sw_d1;
rdrq_packet_t   rdrq_packet_d2sw_d1;
rdrq_packet_t   rdrq_packet_pcr2sw_d1;
rdrq_packet_t   rdrq_packet_pcd2sw_d1;
rdrq_packet_t   rdrq_packet_sw2b_muxed;

// rdrs
rdrs_packet_t   rdrs_packet_pcr2sw_d1;
rdrs_packet_t   rdrs_packet_sr2sw_d1;

logic [BANK_SEL_ADDR_WIDTH-1:0] rdrq_bank_sel, rdrq_bank_sel_d1, rdrq_bank_sel_d2, rdrq_bank_sel_d3, rdrq_bank_sel_d4, rdrq_bank_sel_d1_ns, rdrq_bank_sel_d2_ns, rdrq_bank_sel_d3_ns, rdrq_bank_sel_d4_ns, rdrq_bank_sel_muxed;
logic [BANK_SEL_ADDR_WIDTH-1:0] wr_bank_sel;

typedef enum logic[2:0] {NONE=3'd0, PROC=3'd1, STRM_DMA=3'd2, STRM_RTR=3'd3, PC_DMA=3'd4, PC_RTR=3'd5} rdrq_sel_t; 
rdrq_sel_t rdrq_sel_muxed, rdrq_sel, rdrq_sel_d1, rdrq_sel_d2, rdrq_sel_d3, rdrq_sel_d4, rdrq_sel_d1_ns, rdrq_sel_d2_ns, rdrq_sel_d3_ns, rdrq_sel_d4_ns;

// rdrs
rdrs_packet_t rdrs_packet_b2sw_sr_arr_d1 [BANKS_PER_TILE];
rdrs_packet_t rdrs_packet_b2sw_pr_arr_d1 [BANKS_PER_TILE];
rdrs_packet_t rdrs_packet_b2sw_pcr_arr_d1 [BANKS_PER_TILE];

// dma_on
logic cfg_st_dma_on;
logic cfg_ld_dma_on;
logic cfg_pc_dma_on;
assign cfg_st_dma_on = (cfg_st_dma_mode != 2'b00);
assign cfg_ld_dma_on = (cfg_ld_dma_mode != 2'b00);
assign cfg_pc_dma_on = (cfg_pc_dma_mode == 1);

//============================================================================//
// Switch operation
// Write packet
//============================================================================//
// not stalled
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        wr_packet_pr2sw_d1 <= '0;
    end
    else begin
        wr_packet_pr2sw_d1 <= wr_packet_pr2sw;
    end
end

// can be stalled
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        wr_packet_d2sw_d1 <= '0;
        wr_packet_sr2sw_d1 <= '0;
    end
    else if (clk_en) begin
        wr_packet_d2sw_d1 <= wr_packet_d2sw;
        wr_packet_sr2sw_d1 <= wr_packet_sr2sw;
    end
end

always_comb begin
    if (wr_packet_pr2sw_d1.wr_en) begin
        wr_packet_sw2b_muxed = wr_packet_pr2sw_d1;
    end
    else if (cfg_st_dma_on) begin
        wr_packet_sw2b_muxed = wr_packet_d2sw_d1;
    end
    else begin
        wr_packet_sw2b_muxed = wr_packet_sr2sw_d1;
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

assign wr_bank_sel = wr_packet_sw2b_filtered.wr_addr[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH];
always_comb begin
    for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
        if (wr_bank_sel == i) begin
            wr_packet_sw2b_arr[i] = wr_packet_sw2b_filtered;
        end
        else begin
            wr_packet_sw2b_arr[i] = 0;
        end
    end
end

assign wr_packet_sw2sr = cfg_st_dma_on
                       ? wr_packet_d2sw : wr_packet_sr2sw;

//============================================================================//
// Switch operation
// rdrq packet
//============================================================================//
// not stalled
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_packet_pr2sw_d1 <= '0;
        rdrq_packet_pcr2sw_d1 <= '0;
        rdrq_packet_pcd2sw_d1 <= '0;
    end
    else begin
        rdrq_packet_pr2sw_d1 <= rdrq_packet_pr2sw;
        rdrq_packet_pcr2sw_d1 <= rdrq_packet_pcr2sw;
        rdrq_packet_pcd2sw_d1 <= rdrq_packet_pcd2sw;
    end
end

// can be stalled
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_packet_d2sw_d1 <= '0;
        rdrq_packet_sr2sw_d1 <= '0;
    end
    else if (clk_en) begin
        rdrq_packet_d2sw_d1 <= rdrq_packet_d2sw;
        rdrq_packet_sr2sw_d1 <= rdrq_packet_sr2sw;
    end
end

always_comb begin
    if ((rdrq_packet_pr2sw_d1.rd_en == 1) &&
        (rdrq_packet_pr2sw_d1.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id)) begin
        rdrq_sel_muxed = PROC;
    end
    else if ((cfg_pc_dma_on == 1) &&
             (rdrq_packet_pcd2sw_d1.rd_en == 1) &&
             (rdrq_packet_pcd2sw_d1.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id)) begin
        rdrq_sel_muxed = PC_DMA;
    end
    else if ((cfg_pc_dma_on == 0) &&
             (rdrq_packet_pcr2sw_d1.rd_en == 1) &&
             (rdrq_packet_pcr2sw_d1.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id)) begin
        rdrq_sel_muxed = PC_RTR;
    end
    else if ((cfg_ld_dma_on == 1) &&
             (rdrq_packet_d2sw_d1.rd_en == 1) &&
             (rdrq_packet_d2sw_d1.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id)) begin
        rdrq_sel_muxed = STRM_DMA;
    end
    else if ((cfg_ld_dma_on == 0) &&
             (rdrq_packet_sr2sw_d1.rd_en == 1) &&
             (rdrq_packet_sr2sw_d1.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id)) begin
        rdrq_sel_muxed = STRM_RTR;
    end
    else begin
        rdrq_sel_muxed = NONE;
    end
end

always_comb begin
    if (rdrq_sel_muxed == PROC) begin
        rdrq_packet_sw2b_muxed = rdrq_packet_pr2sw_d1;
    end
    else if (rdrq_sel_muxed == PC_DMA) begin
        rdrq_packet_sw2b_muxed = rdrq_packet_pcd2sw_d1;
    end
    else if (rdrq_sel_muxed == PC_RTR) begin
        rdrq_packet_sw2b_muxed = rdrq_packet_pcr2sw_d1;
    end
    else if (rdrq_sel_muxed == STRM_DMA) begin
        rdrq_packet_sw2b_muxed = rdrq_packet_d2sw_d1;
    end
    else if (rdrq_sel_muxed == STRM_RTR) begin
        rdrq_packet_sw2b_muxed = rdrq_packet_sr2sw_d1;
    end
    else begin
        rdrq_packet_sw2b_muxed = '0;
    end
end
assign rdrq_bank_sel_muxed = rdrq_packet_sw2b_muxed.rd_addr[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH];

assign rdrq_sel = rdrq_sel_muxed;
assign rdrq_bank_sel = rdrq_bank_sel_muxed;

always_comb begin
    for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
        if (rdrq_bank_sel == i) begin
            rdrq_packet_sw2b_arr[i] = rdrq_packet_sw2b_muxed;
        end
        else begin
            rdrq_packet_sw2b_arr[i] = 0;
        end
    end
end

assign rdrq_packet_sw2sr = cfg_ld_dma_on
                         ? rdrq_packet_d2sw : rdrq_packet_sr2sw;

assign rdrq_packet_sw2pcr = cfg_pc_dma_on
                          ? rdrq_packet_pcd2sw : rdrq_packet_pcr2sw;

//============================================================================//
// Switch operation
// rdrs packet
//============================================================================//
// not stalled
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
            rdrs_packet_b2sw_pr_arr_d1[i] <= '0;
            rdrs_packet_b2sw_pcr_arr_d1[i] <= '0;
        end
    end
    else begin
        for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
            rdrs_packet_b2sw_pr_arr_d1[i] <= rdrs_packet_b2sw_arr[i];
            rdrs_packet_b2sw_pcr_arr_d1[i] <= rdrs_packet_b2sw_arr[i];
        end
    end
end

// can be stalled
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
            rdrs_packet_b2sw_sr_arr_d1[i] <= '0;
        end
    end
    else begin
        for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
            if (clk_en) begin
                rdrs_packet_b2sw_sr_arr_d1[i] <= rdrs_packet_b2sw_arr[i];
            end
        end
    end
end

// not stalled
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_sel_d1_ns <= NONE;
        rdrq_bank_sel_d1_ns <= '0;
        rdrq_sel_d2_ns <= NONE;
        rdrq_bank_sel_d2_ns <= '0;
        rdrq_sel_d3_ns <= NONE;
        rdrq_bank_sel_d3_ns <= '0;
        rdrq_sel_d4_ns <= NONE;
        rdrq_bank_sel_d4_ns <= '0;
    end
    else begin
        rdrq_sel_d1_ns <= rdrq_sel;
        rdrq_bank_sel_d1_ns <= rdrq_bank_sel;
        rdrq_sel_d2_ns <= rdrq_sel_d1_ns;
        rdrq_bank_sel_d2_ns <= rdrq_bank_sel_d1_ns;
        rdrq_sel_d3_ns <= rdrq_sel_d2_ns;
        rdrq_bank_sel_d3_ns <= rdrq_bank_sel_d2_ns;
        rdrq_sel_d4_ns <= rdrq_sel_d3_ns;
        rdrq_bank_sel_d4_ns <= rdrq_bank_sel_d3_ns;
    end
end

// can be stalled
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_sel_d1 <= NONE;
        rdrq_bank_sel_d1 <= '0;
        rdrq_sel_d2 <= NONE;
        rdrq_bank_sel_d2 <= '0;
        rdrq_sel_d3 <= NONE;
        rdrq_bank_sel_d3 <= '0;
        rdrq_sel_d4 <= NONE;
        rdrq_bank_sel_d4 <= '0;
    end
    else if (clk_en) begin
        rdrq_sel_d1 <= rdrq_sel;
        rdrq_bank_sel_d1 <= rdrq_bank_sel;
        rdrq_sel_d2 <= rdrq_sel_d1;
        rdrq_bank_sel_d2 <= rdrq_bank_sel_d1;
        rdrq_sel_d3 <= rdrq_sel_d2;
        rdrq_bank_sel_d3 <= rdrq_bank_sel_d2;
        rdrq_sel_d4 <= rdrq_sel_d3;
        rdrq_bank_sel_d4 <= rdrq_bank_sel_d3;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrs_packet_sr2sw_d1 <= '0;
    end
    else if (clk_en) begin
        rdrs_packet_sr2sw_d1 <= rdrs_packet_sr2sw;
    end
end

// sw2d
always_comb begin
    if (cfg_ld_dma_on == 1) begin
        rdrs_packet_sw2d = rdrs_packet_sr2sw_d1;
    end
    else begin
        rdrs_packet_sw2d = '0;
    end
end

// sw2sr
always_comb begin
    if (rdrq_sel_d4 == STRM_RTR || rdrq_sel_d4 == STRM_DMA) begin
        rdrs_packet_sw2sr = rdrs_packet_b2sw_sr_arr_d1[rdrq_bank_sel_d4];
    end
    else begin
        if (cfg_ld_dma_on == 1) begin
            rdrs_packet_sw2sr = 0;
        end
        else begin
            rdrs_packet_sw2sr = rdrs_packet_sr2sw;
        end
    end
end

// sw2pr
always_comb begin
    if (rdrq_sel_d4_ns == PROC) begin
        rdrs_packet_sw2pr = rdrs_packet_b2sw_pr_arr_d1[rdrq_bank_sel_d4_ns];
    end
    else begin
        rdrs_packet_sw2pr = '0;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrs_packet_pcr2sw_d1 <= '0;
    end
    else begin
        rdrs_packet_pcr2sw_d1 <= rdrs_packet_pcr2sw;
    end
end

// sw2pcd
always_comb begin
    if (cfg_pc_dma_on == 1) begin
        rdrs_packet_sw2pcd = rdrs_packet_pcr2sw_d1;
    end
    else begin
        rdrs_packet_sw2pcd = '0;
    end
end

// sw2pcr
always_comb begin
    if (rdrq_sel_d4_ns == PC_RTR || rdrq_sel_d4_ns == PC_DMA) begin
        rdrs_packet_sw2pcr = rdrs_packet_b2sw_pcr_arr_d1[rdrq_bank_sel_d4_ns];
    end
    else begin
        if (cfg_pc_dma_on == 1) begin
            rdrs_packet_sw2pcr = 0;
        end
        else begin
            rdrs_packet_sw2pcr = rdrs_packet_pcr2sw;
        end
    end
end

endmodule
