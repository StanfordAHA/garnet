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
// Internal signals
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        start_addr_internal <= '0;
        for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
            iteration_internal <= '0;
        end
    end
    else if (clk_en) begin
        if (start_pulse_internal) begin
            start_addr_internal <= dma_header_int[q_sel_r].start_addr;
            for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
                iteration_internal <= dma_header_int[q_sel_r].iteration;
            end
        end
    end
end

always_comb begin
    if (start_pulse_internal) begin
        strm_run_next =  1;
    end
    else if (done_pulse_internal) begin
        strm_run_next = 0;
    end
    else begin
        strm_run_next =  strm_run;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        strm_run <= 0;
    end
    else if (clk_en) begin
        strm_run <= strm_run_next;
    end
end

// active signal generator
always_comb begin
    strm_active_cnt_next = '0;
    strm_inactive_cnt_next = '0;
    strm_active_next = 0;
    if (strm_run_next) begin
        if (start_pulse_internal) begin
            strm_active_cnt_next = num_active_words;
            strm_inactive_cnt_next = num_inactive_words;
            strm_active_next = 1;
        end
        else if (num_inactive_words == '0) begin
            strm_active_next = 1;
        end
        else begin
            if (strm_active) begin
                strm_active_cnt_next = (strm_active_cnt > 0) ? strm_active_cnt-1 : 0;
                strm_active_next = ~(strm_active_cnt_next == 0);
                strm_inactive_cnt_next = (strm_active_next == 0) ? num_inactive_words : strm_inactive_cnt;
            end
            else begin
                strm_inactive_cnt_next = (strm_active_next == 0) ? strm_inactive_cnt-1 : 0;
                strm_active_next = ~(strm_inactive_cnt_next == 0);
                strm_active_cnt_next = (strm_active_cnt > 0) ? strm_active_cnt_next-1 : 0;
            end
        end
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        strm_active <= 0;
        strm_active_cnt <= '0;
        strm_inactive_cnt <= '0;
    end
    else if (clk_en) begin
        strm_active <= strm_active_next;
        strm_active_cnt <= strm_active_cnt_next;
        strm_inactive_cnt <= strm_inactive_cnt_next;
    end
end

// And reduction to check last stream
always_comb begin
    last_strm = 1;
    for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
        last_strm = last_strm & ((range[i] == 0) | (itr[i] == range[i] - 1));
    end
    last_strm = last_strm & (strm_inactive_cnt_next == '0);
end

// done pulse internal
always_comb begin
    done_pulse_internal = last_strm & strm_run;
end

//============================================================================//
// bank packet control
//============================================================================//
glb_shift #(.DATA_WIDTH(1), .DEPTH(2)
) glb_shift_start_pulse (
    .data_in(start_pulse_internal),
    .data_out(start_pulse_internal_d_arr),
    .*);
always_comb begin
     start_pulse_internal_d1 = start_pulse_internal_d_arr[1];
end

// strm_Rdrq
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        strm_rdrq_internal <= '0;
    end
    else if (clk_en) begin
        if (strm_active) begin
            strm_rdrq_internal.rd_en <= 1;
            strm_rdrq_internal.rd_addr <= strm_addr_internal;
        end
        else begin
            strm_rdrq_internal.rd_en <= 0;
        end
    end
end

glb_shift #(.DATA_WIDTH($bits(rdrq_packet_t)), .DEPTH(1)
) glb_shift_strm_rdrq (
    .data_in(strm_rdrq_internal),
    .data_out(strm_rdrq_internal_d1),
    .*);

always_comb begin
    bank_addr_eq = strm_rdrq_internal.rd_addr[GLB_ADDR_WIDTH-1:3] == strm_rdrq_internal_d1[0].rd_addr[GLB_ADDR_WIDTH-1:3];
    bank_rdrq_internal.rd_en = start_pulse_internal_d1 | (strm_rdrq_internal.rd_en & ~bank_addr_eq);
    bank_rdrq_internal.rd_addr = strm_rdrq_internal.rd_addr;
end

assign rdrq_packet = bank_rdrq_internal; 

always_comb begin
end

always_ff @(posedge clk or posedge reset) begin
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

//============================================================================//
// Strided access pattern iteration control
//============================================================================//
always_comb begin
    for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
        itr_incr[i] = 0;
        itr_next[i] = '0;
    end
    if (strm_run) begin
        for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
            if (i==0) begin
                itr_incr[i] = strm_active;
                itr_next[i] = itr_incr[i] ? ((itr[i] == range[i]-1) ? 0 : itr[i]+1) : itr[i];
            end
            else begin
                itr_incr[i] = intr_incr[i-1] & (itr_next[i-1] == 0); 
                itr_next[i] = itr_incr[i] ? ((itr[i] == range[i]-1) ? 0 : itr[i]+1) : itr[i];
            end
        end
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
            itr[i] <= '0;
        end
    end
    else if (clk_en) begin
        for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
            itr[i] <= itr_next[i];
        end
    end
end

always_comb begin
    strm_addr_internal = start_addr_internal;
    for (int i=0; i<LOOP_LEVEL-1; i=i+1) begin
        strm_addr_internal = strm_addr_internal + itr[i]*stride[i];
    end
end

//============================================================================//
// Queue selection register
//============================================================================//
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

//============================================================================//
// stream glb to fabric done pulse
//============================================================================//
assign stream_g2f_done = (state == DONE);

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        stream_g2f_done_d1 <= 1'b0;
    end
    else if (clk_en) begin
        stream_g2f_done_d1 <= stream_g2f_done;
    end
end

// TODO(kongty) Check whether stream_f2g_done_pulse is correctly generated after
// it actually writes to a bank
logic stream_g2f_done_pulse_shift_arr [NUM_GLB_TILES];
always_comb begin
    stream_g2f_done_pulse_int = stream_g2f_done & (!stream_g2f_done_d1);
end

glb_shift #(.DATA_WIDTH(1), .DEPTH(NUM_GLB_TILES)
) glb_shift_done_pulse (
    .data_in(stream_g2f_done_pulse_int),
    .data_out(stream_g2f_done_pulse_shift_arr),
    .*);
assign stream_g2f_done_pulse = stream_g2f_done_pulse_arr[cfg_num_tiles_connected];

endmodule
