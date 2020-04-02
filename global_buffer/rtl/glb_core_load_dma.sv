/*=============================================================================
** Module: glb_core_load_dma.sv
** Description:
**              Global Buffer Core Load DMA
** Author: Taeyoung Kong
** Change history: 
**      03/13/2020
**          - Implement first version of global buffer core load DMA
**===========================================================================*/
import  global_buffer_pkg::*;

module glb_core_load_dma (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,

    // cgra streaming word
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f,
    output logic                            stream_data_valid_g2f,

    // read req packet
    output rdrq_packet_t                    rdrq_packet,

    // read res packet
    input  rdrs_packet_t                    rdrs_packet,

    // Configuration registers
    input  logic [1:0]                      cfg_load_dma_mode,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  cfg_num_tiles_connected,
    input  dma_ld_header_t                  cfg_load_dma_header [QUEUE_DEPTH],

    // glb internal signal
    output logic                            cfg_load_dma_invalidate_pulse [QUEUE_DEPTH],

    // interrupt pulse
    input  logic                            strm_start_pulse,
    output logic                            stream_g2f_done_pulse
);

//============================================================================//
// Internal dma
//============================================================================//
always_comb begin
    for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
        dma_validate[i] = cfg_load_dma_header[i].valid;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
            dma_validate_d1[i] <= 0;
        end
    end
    else if (clk_en) begin
        for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
            dma_validate_d1[i] <= dma_validate[i];
        end
    end
end

always_comb begin
    for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
        dma_validate_pulse[i] = dma_validate[i] & !dma_validate_d1[i];
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
            dma_header_int[i] <= '0;
        end
    end
    else if (clk_en) begin
        for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
            if (dma_validate_pulse[i] == 1) begin
                dma_header_int[i] <= cfg_load_dma_header[i];
            end
            else if (dma_invalidate_pulse[i] == 1) begin
                dma_header_int[i].valid <= 0;
            end
        end
    end
end

//============================================================================//
// Internal logic
//============================================================================//

//============================================================================//
// Internal signals
//============================================================================//
logic bank_rdrq;
logic bank_addr_neq;
always_comb begin
    bank_addr_neq = bank_addr_cached != bank_addr_next;
    bank_rdrq = strm_start_pulse_d1 | (bank_addr_neq & strm_rdrq);
end

logic bank_rdrq_shift_arr [NUM_GLB_TILES];
glb_shift #(.DATA_WIDTH(1), .DEPTH(NUM_GLB_TILES)
) glb_shift (
    .data_in(bank_rdrq),
    .data_out(bank_rdrq_shift_arr),
    .*);
assign bank_rdrq_shift = bank_rdrq_shift[cfg_num_tiles_connected];

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        bank_addr_cached <= '0;
    end
    else if (clk_en) begin
        bank_addr_cached <= bank_addr;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
    end
    else if (clk_en) begin
        if (start_pulse_internal) begin
            start_addr_internal <= start_addr;
            for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
                iteration_internal <= dma_header_int[q_sel].iteration;
            end
        end
        else begin

        end
    end
end


logic [$clog2(QUEUE_DEPTH)-1:0] q_sel_next, q_sel_r;
always_comb begin
    casez(cfg_load_dma_mode)
    OFF, NORMAL, REPEAT: begin
        q_sel_next = '0;
    end
    AUTO_INCR: begin
        q_sel_next = (done_pulse_internal) ? q_sel_r + 1 : q_sel_r;
    end
    endcase
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        q_sel_r <= '0;
    end
    else if (clk_en) begin
        q_sel_r <= q_sel_next;
    end
end



// //============================================================================//
// // DMA output
// //============================================================================//
// // output wr_packet
// always_comb begin
//     if (state == DONE) begin
//         wr_packet.wr_en = 1'b1;
//         wr_packet.wr_strb = cache_strb;
//         wr_packet.wr_data = cache_data;
//         wr_packet.wr_addr = {cur_addr[GLB_ADDR_WIDTH-1:BANK_ADDR_BYTE_OFFSET], {BANK_ADDR_BYTE_OFFSET{1'b0}}};
//     end
//     else if (state == ACC4 && (num_cnt != '0)) begin
//         wr_packet.wr_en = 1'b1;
//         wr_packet.wr_strb = cache_strb;
//         wr_packet.wr_data = cache_data;
//         wr_packet.wr_addr = {cur_addr[GLB_ADDR_WIDTH-1:BANK_ADDR_BYTE_OFFSET], {BANK_ADDR_BYTE_OFFSET{1'b0}}};
//     end
//     else begin
//         wr_packet.wr_en = 1'b0;
//         wr_packet.wr_strb = '0;
//         wr_packet.wr_data = '0;
//         wr_packet.wr_addr = '0;
//     end
// end
// 
// //============================================================================//
// // stream glb to fabric done pulse
// //============================================================================//
// assign stream_g2f_done = (state == DONE);
// 
// always_ff @(posedge clk or posedge reset) begin
//     if (reset) begin
//         stream_g2f_done_d1 <= 1'b0;
//     end
//     else if (clk_en) begin
//         stream_g2f_done_d1 <= stream_g2f_done;
//     end
// end
// assign stream_g2f_done_pulse = stream_g2f_done & (!stream_g2f_done_d1);

endmodule
