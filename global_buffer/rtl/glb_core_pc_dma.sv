/*=============================================================================
** Module: glb_core_pc_dma.sv
** Description:
**              Global Buffer Core PC DMA
** Author: Taeyoung Kong
** Change history: 
**      03/08/2020
**          - Implement first version of global buffer core parallel config DMA
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_core_pc_dma (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // cgra streaming word
    output cgra_cfg_t                       cgra_cfg_c2sw,

    // read req packet
    output rdrq_packet_t                    rdrq_packet,

    // read res packet
    input  rdrs_packet_t                    rdrs_packet,

    // Configuration registers
    input  logic                            cfg_pc_dma_mode,
    input  dma_pc_header_t                  cfg_pc_dma_header,
    input  logic [LATENCY_WIDTH-1:0]        cfg_pc_latency,     

    // interrupt pulse
    input  logic                            pc_start_pulse,
    output logic                            pc_done_pulse
);
//============================================================================//
// local parameter declaration
//============================================================================//
localparam int BANK_DATA_BYTE = ((BANK_DATA_WIDTH + 8 - 1)/8); //8
localparam int FIXED_LATENCY = 8;
localparam int INTERRUPT_PULSE = 4;

//============================================================================//
// Internal logic
//============================================================================//
logic start_pulse_next, start_pulse_internal;
logic done_pulse_next, done_pulse_internal;
logic done_pulse_internal_d_arr [3*NUM_GLB_TILES + FIXED_LATENCY + INTERRUPT_PULSE];
logic pc_run_next, pc_run;
logic [MAX_NUM_CFGS_WIDTH-1:0] cfg_cnt_next, cfg_cnt_internal;
logic [GLB_ADDR_WIDTH-1:0] addr_next, addr_internal;
logic rd_en_next, rd_en_internal;
logic [GLB_ADDR_WIDTH-1:0] rd_addr_next, rd_addr_internal;
logic [BANK_DATA_WIDTH-1:0] rd_data_next, rd_data_internal;
logic rd_data_valid_next, rd_data_valid_internal;

//============================================================================//
// assigns
//============================================================================//
always_comb begin
    pc_done_pulse = 0;
    for (int i=0; i < INTERRUPT_PULSE; i=i+1) begin
        pc_done_pulse = pc_done_pulse | done_pulse_internal_d_arr[FIXED_LATENCY +cfg_pc_latency+i + NUM_GLB_TILES];
    end
end
assign rdrq_packet.rd_en = rd_en_internal;
assign rdrq_packet.rd_addr = rd_addr_internal;
// assign rdrq_packet.packet_sel.packet_type = PSEL_PCFG;
// assign rdrq_packet.packet_sel.src = glb_tile_id;
assign cgra_cfg_c2sw.cfg_rd_en = 0;
assign cgra_cfg_c2sw.cfg_wr_en = rd_data_valid_internal;
assign cgra_cfg_c2sw.cfg_addr = rd_data_internal[CGRA_CFG_DATA_WIDTH +: CGRA_CFG_ADDR_WIDTH]; 
assign cgra_cfg_c2sw.cfg_data = rd_data_internal[0 +: CGRA_CFG_DATA_WIDTH]; 

//============================================================================//
// Control logic
//============================================================================//
// start pulse
always_comb begin
    start_pulse_next = 0;
    if ((cfg_pc_dma_mode == 1) & ~pc_run & pc_start_pulse) begin
        start_pulse_next = 1;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        start_pulse_internal = 0;
    end
    else begin
        start_pulse_internal = start_pulse_next;
    end
end

// done pulse
always_comb begin
    done_pulse_next = 0;
    if ((pc_run == 1) & (cfg_cnt_internal == 0)) begin
        done_pulse_next = 1;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        done_pulse_internal <= 0;
    end
    else begin
        done_pulse_internal <= done_pulse_next;
    end
end

// parallel configuration is running
always_comb begin
    if (start_pulse_internal) begin
        pc_run_next = 1;
    end
    else if ((pc_run == 1) & (cfg_cnt_internal == 0)) begin
        pc_run_next = 0;
    end
    else begin
        pc_run_next = pc_run;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        pc_run <= 0;
    end
    else begin
        pc_run <= pc_run_next;
    end
end

// internal counter and address
always_comb begin
    cfg_cnt_next = 0;
    addr_next = 0;
    if (start_pulse_internal) begin
        cfg_cnt_next = cfg_pc_dma_header.num_cfgs;
        addr_next = cfg_pc_dma_header.start_addr;
    end
    else if(pc_run & (cfg_cnt_internal > 0)) begin
        cfg_cnt_next = cfg_cnt_internal - 1;
        addr_next = addr_internal + BANK_DATA_BYTE;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cfg_cnt_internal <= '0;
        addr_internal <= '0;
    end
    else begin
        cfg_cnt_internal <= cfg_cnt_next;
        addr_internal <= addr_next;
    end
end

// internal rdrq packet
always_comb begin
    rd_en_next = 0;
    rd_addr_next = '0;
    if (pc_run & (cfg_cnt_internal > 0)) begin
        rd_en_next = 1;
        rd_addr_next = addr_internal;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rd_en_internal <= 0;
        rd_addr_internal <= '0;
    end
    else begin
        rd_en_internal <= rd_en_next;
        rd_addr_internal <= rd_addr_next;
    end
end

// internal rdrs packet
always_comb begin
    rd_data_next = '0;
    rd_data_valid_next = 0;
    if (rdrs_packet.rd_data_valid) begin
        rd_data_next = rdrs_packet.rd_data;
        rd_data_valid_next = 1;
    end
end

// Instead of counting fixed latency, I used rdrs_data_valid assuming only one dma is on.
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rd_data_internal <= '0;
        rd_data_valid_internal <= 0;
    end
    else begin
        rd_data_internal <= rd_data_next;
        rd_data_valid_internal <= rd_data_valid_next;
    end
end

// done pulse pipeline
// parallel configuration is not stalled
glb_shift #(.DATA_WIDTH(1), .DEPTH(3*NUM_GLB_TILES+FIXED_LATENCY+INTERRUPT_PULSE)
) glb_shift_done_pulse (
    .data_in(done_pulse_internal),
    .data_out(done_pulse_internal_d_arr),
    .clk_en(1'b1),
    .*);

endmodule
