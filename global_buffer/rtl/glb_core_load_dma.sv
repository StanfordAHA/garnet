/*=============================================================================
** Module: glb_core_load_dma.sv
** Description:
**              Global Buffer Core Load DMA
** Author: Taeyoung Kong
** Change history: 
**      03/13/2020
**          - Implement first version of global buffer core load DMA
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_core_load_dma (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // cgra streaming word
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f,
    output logic                            stream_data_valid_g2f,

    // read req packet
    output rdrq_packet_t                    rdrq_packet,

    // read res packet
    input  rdrs_packet_t                    rdrs_packet,

    // Configuration registers
    input  logic [1:0]                      cfg_ld_dma_mode,
    input  logic [LATENCY_WIDTH-1:0]        cfg_latency,
    input  dma_ld_header_t                  cfg_ld_dma_header [QUEUE_DEPTH],

    // glb internal signal
    output logic                            cfg_load_dma_invalidate_pulse [QUEUE_DEPTH],

    // interrupt pulse
    input  logic                            strm_start_pulse,
    output logic                            stream_g2f_done_pulse
);

//============================================================================//
// local parameter
//============================================================================//
localparam int START_PULSE_SHIFT_DEPTH = 2;
localparam int FIXED_LATENCY = 8;
localparam int INTERRUPT_PULSE = 4;

//============================================================================//
// Internal logic defines
//============================================================================//
dma_ld_header_t dma_header_int [QUEUE_DEPTH];
logic dma_validate [QUEUE_DEPTH];
logic dma_validate_d1 [QUEUE_DEPTH];
logic dma_validate_pulse [QUEUE_DEPTH];
logic dma_invalidate_pulse [QUEUE_DEPTH];
logic dma_active, dma_active_next;
logic start_pulse_internal, start_pulse_next, start_pulse_internal_d2;
logic start_pulse_internal_d_arr [START_PULSE_SHIFT_DEPTH];
logic strm_run, strm_run_next;
logic [MAX_NUM_WORDS_WIDTH-1:0] strm_active_cnt, strm_active_cnt_next;
logic [MAX_NUM_WORDS_WIDTH-1:0] strm_inactive_cnt, strm_inactive_cnt_next;
logic strm_active, strm_active_next;
logic itr_incr [LOOP_LEVEL];
logic [GLB_ADDR_WIDTH-1:0] strm_addr_internal;
logic [CGRA_DATA_WIDTH-1:0] strm_data, strm_data_d1;
logic strm_data_valid, strm_data_valid_d1;
logic [BANK_BYTE_OFFSET-CGRA_BYTE_OFFSET-1:0] strm_data_sel;
logic [GLB_ADDR_WIDTH-1:0] strm_rdrq_addr_d_arr [2*NUM_GLB_TILES+FIXED_LATENCY];
rdrq_packet_t strm_rdrq_internal;
logic last_strm;
logic [GLB_ADDR_WIDTH-1:0] start_addr_internal;
loop_ctrl_t iter_internal [LOOP_LEVEL];
logic [MAX_NUM_WORDS_WIDTH-1:0] itr [LOOP_LEVEL];
logic [MAX_NUM_WORDS_WIDTH-1:0] itr_next [LOOP_LEVEL];
logic done_pulse_internal, done_pulse_internal_d1;
logic bank_addr_eq;
rdrq_packet_t bank_rdrq_internal;
logic bank_rdrq_internal_rd_en_d_arr [NUM_GLB_TILES];
logic [BANK_DATA_WIDTH-1:0] bank_rdrs_data, bank_rdrs_data_cache;
logic bank_rdrs_data_valid;
logic [$clog2(QUEUE_DEPTH)-1:0] q_sel_next, q_sel;
logic done_pulse_internal_d_arr [2*NUM_GLB_TILES+FIXED_LATENCY+INTERRUPT_PULSE];
logic strm_rdrq_rd_en_d_arr [2*NUM_GLB_TILES+FIXED_LATENCY];
logic [MAX_NUM_WORDS_WIDTH-1:0] num_active_words_internal;
logic [MAX_NUM_WORDS_WIDTH-1:0] num_inactive_words_internal;

//============================================================================//
// pipeline registers
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        strm_data_d1 <= '0;
        strm_data_valid_d1 <= '0;
    end
    else if (clk_en) begin
        strm_data_d1 <= strm_data;
        strm_data_valid_d1 <= strm_data_valid;
    end
end

//============================================================================//
// assigns
//============================================================================//
// assign bank_rdrq_internal.packet_sel.packet_type = PSEL_STRM;
// assign bank_rdrq_internal.packet_sel.src = glb_tile_id;
assign rdrq_packet = bank_rdrq_internal; 
assign bank_rdrs_data_valid = rdrs_packet.rd_data_valid;
assign bank_rdrs_data = rdrs_packet.rd_data;
assign stream_data_g2f = strm_data_d1;
assign stream_data_valid_g2f = strm_data_valid_d1;

always_comb begin
    stream_g2f_done_pulse = 0;
    for (int i=0; i < INTERRUPT_PULSE; i=i+1) begin
        stream_g2f_done_pulse = stream_g2f_done_pulse | done_pulse_internal_d_arr[FIXED_LATENCY+cfg_latency+i];
    end
end

//============================================================================//
// Internal dma
//============================================================================//
always_comb begin
    for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
        dma_validate[i] = cfg_ld_dma_header[i].valid;
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
                dma_header_int[i] <= cfg_ld_dma_header[i];
            end
            else if (dma_invalidate_pulse[i] == 1) begin
                dma_header_int[i].valid <= 0;
            end
        end
    end
end

// once corresponding dma header is used to stream data, it invalidates
always_comb begin
    for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
        dma_invalidate_pulse[i] = (q_sel == i) & start_pulse_internal; 
    end
end

always_comb begin
    for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
        cfg_load_dma_invalidate_pulse[i] = dma_invalidate_pulse[i];
    end
end

// dma active indicates whether dma is activated by strm_start_pulse
always_comb begin
    casez (cfg_ld_dma_mode)
    OFF: begin
        dma_active_next = 0;
    end
    NORMAL, REPEAT, AUTO_INCR: begin
        dma_active_next = strm_start_pulse;
    end
    default: begin
        dma_active_next = 0;
    end
    endcase
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        dma_active <= 0;
    end
    else if (clk_en) begin
        dma_active <= dma_active_next;
    end
end

// Internal_start_pulse
always_comb begin
    casez (cfg_ld_dma_mode)
    OFF: begin
        start_pulse_next = 0;
    end
    NORMAL: begin
        start_pulse_next = (~strm_run & strm_start_pulse);
    end
    REPEAT, AUTO_INCR: begin
        start_pulse_next = (~dma_active & strm_start_pulse) | (dma_active & dma_header_int[q_sel].valid & ~strm_run);
    end
    default: begin
        start_pulse_next = 0;
    end
    endcase
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        start_pulse_internal <= 1'b0;
    end
    else if (clk_en) begin
        start_pulse_internal <= start_pulse_internal ? 0 : start_pulse_next;
    end
end

//============================================================================//
// Internal streaming control
//============================================================================//
// strm is running or not
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

always_comb begin
    num_active_words_internal = dma_header_int[q_sel].num_active_words;
    num_inactive_words_internal = dma_header_int[q_sel].num_inactive_words;
end

// current cycle strm is active or not
always_comb begin
    strm_active_cnt_next = '0;
    strm_inactive_cnt_next = '0;
    strm_active_next = 0;
    if (strm_run | start_pulse_internal) begin
        if (start_pulse_internal) begin
            strm_active_cnt_next = num_active_words_internal;
            strm_inactive_cnt_next = num_inactive_words_internal;
            strm_active_next = 1;
        end
        else if (num_inactive_words_internal == '0) begin
            if (last_strm) begin
                strm_active_next = 0;
            end
            else begin
                strm_active_next = 1;
            end
        end
        else begin
            if (strm_active) begin
                strm_active_cnt_next = (strm_active_cnt > 0) ? strm_active_cnt-1 : '0;
                strm_active_next = ~(strm_active_cnt_next == 0);
                strm_inactive_cnt_next = (strm_active_next == 0) ? num_inactive_words_internal : strm_inactive_cnt;
            end
            else begin
                strm_inactive_cnt_next = (strm_inactive_cnt > 0) ? strm_inactive_cnt - 1 : '0;
                strm_active_next = (strm_inactive_cnt_next == 0);
                strm_active_cnt_next = (strm_active_next == 1) ? num_active_words_internal : strm_active_cnt;
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

//============================================================================//
// Strided access pattern iteration control
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        start_addr_internal <= '0;
        for (int i=0; i<LOOP_LEVEL; i=i+1) begin
            iter_internal[i] <= '0;
        end
    end
    else if (clk_en) begin
        if (start_pulse_internal) begin
            start_addr_internal <= dma_header_int[q_sel].start_addr;
            for (int i=0; i<LOOP_LEVEL; i=i+1) begin
                iter_internal[i] <= dma_header_int[q_sel].iteration[i];
            end
        end
    end
end

always_comb begin
    for (int i=0; i<LOOP_LEVEL; i=i+1) begin
        itr_incr[i] = 0;
        itr_next[i] = '0;
    end
    if (strm_run) begin
        for (int i=0; i<LOOP_LEVEL; i=i+1) begin
            if (i==0) begin
                itr_incr[i] = strm_active;
                itr_next[i] = itr_incr[i] ? ((itr[i] == iter_internal[i].range-1) ? 0 : itr[i]+1) : itr[i];
            end
            else begin
                itr_incr[i] = itr_incr[i-1] & (itr_next[i-1] == 0); 
                itr_next[i] = itr_incr[i] ? ((itr[i] == iter_internal[i].range-1) ? 0 : itr[i]+1) : itr[i];
            end
        end
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<LOOP_LEVEL; i=i+1) begin
            itr[i] <= '0;
        end
    end
    else if (clk_en) begin
        for (int i=0; i<LOOP_LEVEL; i=i+1) begin
            itr[i] <= itr_next[i];
        end
    end
end

// calculate internal address
always_comb begin
    strm_addr_internal = start_addr_internal;
    for (int i=0; i<LOOP_LEVEL; i=i+1) begin
        strm_addr_internal = strm_addr_internal + itr[i]*iter_internal[i].stride*(CGRA_BYTE_OFFSET+1);
    end
end

// AND reduction to check last stream
always_comb begin
    last_strm = 1;
    for (int i=0; i<LOOP_LEVEL; i=i+1) begin
        last_strm = last_strm & ((iter_internal[i].range == 0) | (itr[i] == iter_internal[i].range - 1));
    end
end

// done pulse internal
always_comb begin
    done_pulse_internal = last_strm & strm_run;
end

//============================================================================//
// bank packet control
//============================================================================//
glb_shift #(.DATA_WIDTH(1), .DEPTH(START_PULSE_SHIFT_DEPTH)
) glb_shift_start_pulse (
    .data_in(start_pulse_internal),
    .data_out(start_pulse_internal_d_arr),
    .*);
always_comb begin
     start_pulse_internal_d2 = start_pulse_internal_d_arr[1];
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

// request read when only it is needed (e.g. cur_rd_addr is different from prev_rd_addr)
always_comb begin
    // addr[2:0] does not affect a row in a bank
    bank_addr_eq = (strm_rdrq_internal.rd_addr[GLB_ADDR_WIDTH-1:3] == strm_rdrq_addr_d_arr[0][GLB_ADDR_WIDTH-1:3]);
    bank_rdrq_internal.rd_en = strm_rdrq_internal.rd_en & (start_pulse_internal_d2 | ~bank_addr_eq);
    bank_rdrq_internal.rd_addr = strm_rdrq_internal.rd_addr;
end

glb_shift #(.DATA_WIDTH(1), .DEPTH(NUM_GLB_TILES)
) glb_shift_bank_rd_en (
    .data_in(bank_rdrq_internal.rd_en),
    .data_out(bank_rdrq_internal_rd_en_d_arr),
    .*);

// Instead of counting fixed latency, I used rdrs_data_valid assuming only one dma is on.
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        bank_rdrs_data_cache <= '0;
    end
    else if (clk_en) begin
        if (bank_rdrs_data_valid) begin
            bank_rdrs_data_cache <= bank_rdrs_data;
        end
    end
end

glb_shift #(.DATA_WIDTH(GLB_ADDR_WIDTH), .DEPTH(2*NUM_GLB_TILES+FIXED_LATENCY)
) glb_shift_strm_rd_addr (
    .data_in(strm_rdrq_internal.rd_addr),
    .data_out(strm_rdrq_addr_d_arr),
    .*);

glb_shift #(.DATA_WIDTH(1), .DEPTH(2*NUM_GLB_TILES+FIXED_LATENCY)
) glb_shift_strm_rd_en (
    .data_in(strm_rdrq_internal.rd_en),
    .data_out(strm_rdrq_rd_en_d_arr),
    .*);

always_comb begin
    strm_data_valid = strm_rdrq_rd_en_d_arr[cfg_latency+FIXED_LATENCY];
    strm_data_sel = strm_rdrq_addr_d_arr[cfg_latency+FIXED_LATENCY][BANK_BYTE_OFFSET-1:CGRA_BYTE_OFFSET];
    strm_data = bank_rdrs_data_cache[strm_data_sel*CGRA_DATA_WIDTH +: CGRA_DATA_WIDTH];
end

//============================================================================//
// Queue selection register
//============================================================================//
always_comb begin
    casez(cfg_ld_dma_mode)
    OFF, NORMAL, REPEAT: begin
        q_sel_next = '0;
    end
    AUTO_INCR: begin
        q_sel_next = (done_pulse_internal) ? q_sel + 1 : q_sel;
    end
    default: begin
        q_sel_next = '0;
    end
    endcase
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        q_sel <= '0;
    end
    else if (clk_en) begin
        q_sel <= q_sel_next;
    end
end

//============================================================================//
// stream glb to fabric done pulse
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        done_pulse_internal_d1 <= 0;
    end
    else if (clk_en) begin
        done_pulse_internal_d1 <= done_pulse_internal;
    end
end

glb_shift #(.DATA_WIDTH(1), .DEPTH(2*NUM_GLB_TILES+FIXED_LATENCY+INTERRUPT_PULSE)
) glb_shift_done_pulse (
    .data_in(done_pulse_internal_d1),
    .data_out(done_pulse_internal_d_arr),
    .*);

endmodule
