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

    // wr_packet
    input  wr_packet_t                      wr_packet_from_router,
    output wr_packet_t                      wr_packet_to_router,
    input  wr_packet_t                      wr_packet_from_dma,
    output wr_packet_t                      wr_packet_to_bank,

    // rdrq_packet
    input  rdrq_packet_t                    rdrq_packet_from_router,
    output rdrq_packet_t                    rdrq_packet_to_router,
    input  rdrq_packet_t                    rdrq_packet_from_dma,
    output rdrq_packet_t                    rdrq_packet_to_bank,

    // rdrs_packet
    input  rdrs_packet_t                    rdrs_packet_from_router,
    output rdrs_packet_t                    rdrs_packet_to_router,
    input  rdrs_packet_t                    rdrs_packet_from_bank,
    output rdrs_packet_t                    rdrs_packet_to_dma,

    // Configuration registers
    input  logic                            cfg_store_dma_on,
    input  logic                            cfg_load_dma_on
);

//============================================================================//
// Internal packet wire
//============================================================================//
wr_packet_t     wr_packet_to_bank_int;
wr_packet_t     wr_packet_to_bank_int_filtered;
wr_packet_t     wr_packet_to_bank_int_filtered_d1;
rdrq_packet_t   rdrq_packet_to_bank_int;
rdrq_packet_t   rdrq_packet_to_bank_int_filtered;
rdrq_packet_t   rdrq_packet_to_bank_int_filtered_d1;
rdrs_packet_t   rdrs_packet_from_bank_d1;
rdrs_packet_t   rdrs_packet_to_dma_int;
rdrs_packet_t   rdrs_packet_to_dma_int_filtered;

//============================================================================//
// Read res pipeilne register for timing
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrs_packet_from_bank_d1 <= '0;
    end
    else if (clk_en) begin
        rdrs_packet_from_bank_d1 <= rdrs_packet_from_bank;
    end
end

//============================================================================//
// To router
//============================================================================//
assign wr_packet_to_router = cfg_store_dma_on
                           ? wr_packet_from_dma : wr_packet_from_router;

assign rdrq_packet_to_router = cfg_load_dma_on
                             ? rdrq_packet_from_dma : rdrq_packet_from_router;

assign rdrs_packet_to_router = cfg_load_dma_on
                             ? rdrs_packet_from_bank_d1 : rdrs_packet_from_router;

//============================================================================//
// To bank
// Switch operation
//============================================================================//
assign wr_packet_to_bank_int = cfg_store_dma_on
                             ? wr_packet_from_dma : wr_packet_from_router;

assign rdrq_packet_to_bank_int = cfg_load_dma_on
                               ? rdrq_packet_from_dma : rdrq_packet_from_router;

assign rdrs_packet_to_dma_int = cfg_load_dma_on
                              ? rdrs_packet_from_bank_d1 : rdrs_packet_from_router;

always_comb begin
    if (wr_packet_to_bank_int.wr_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) begin
        wr_packet_to_bank_int_filtered = wr_packet_to_bank_int;
    end
    else begin
        wr_packet_to_bank_int_filtered = '0;
    end
end

always_comb begin
    if (rdrq_packet_to_bank_int.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id) begin
        rdrq_packet_to_bank_int_filtered = rdrq_packet_to_bank_int;
    end
    else begin
        rdrq_packet_to_bank_int_filtered = '0;
    end
end

always_comb begin
    if (rdrs_packet_to_dma_int.rd_src == glb_tile_id) begin
        rdrs_packet_to_dma_int_filtered = rdrs_packet_to_dma_int;
    end
    else begin
        rdrs_packet_to_dma_int_filtered = '0;
    end
end

//============================================================================//
// Write/Read req pipeilne register for timing
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        wr_packet_to_bank_int_filtered_d1 <= '0;
    end
    else if (clk_en) begin
        wr_packet_to_bank_int_filtered_d1 <= wr_packet_to_bank_int_filtered;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_packet_to_bank_int_filtered_d1 <= '0;
    end
    else if (clk_en) begin
        rdrq_packet_to_bank_int_filtered_d1 <= rdrq_packet_to_bank_int_filtered;
    end
end

//============================================================================//
// Output assignment
//============================================================================//
assign wr_packet_to_bank = wr_packet_to_bank_int_filtered_d1;
assign rdrq_packet_to_bank = rdrq_packet_to_bank_int_filtered_d1;
assign rdrs_packet_to_dma = rdrs_packet_to_dma_int_filtered;

endmodule
