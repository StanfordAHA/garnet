/*=============================================================================
** Module: glb_core_pc_dma.sv
** Description:
**              Global Buffer Core PC DMA
** Author: Taeyoung Kong
** Change history: 
**      03/08/2020
**          - Implement first version of global buffer core parallel config DMA
**===========================================================================*/
import  global_buffer_pkg::*;

module glb_core_pc_dma (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,

    // cgra streaming word
    output cgra_cfg_t                       cgra_cfg_c2sw,

    // read req packet
    output rdrq_packet_t                    rdrq_packet,

    // read res packet
    input  rdrs_packet_t                    rdrs_packet,

    // Configuration registers
    input  logic                            cfg_pc_dma_mode,
    input  dma_pc_header_t                  cfg_pc_dma_header,

    // interrupt pulse
    input  logic                            pc_start_pulse,
    output logic                            pc_done_pulse
);

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_packet <= '0;
    end
    else if (clk_en) begin
        rdrq_packet <= rdrs_packet;
    end
end

assign cgra_cfg_c2sw = '0;

//============================================================================//
// local parameter declaration
//============================================================================//
localparam integer BANK_DATA_BYTE = ((BANK_DATA_WIDTH + 8 - 1)/8); //8

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
    pc_run_next = 0;
    if (start_pulse_internal) begin
        pc_run_next = 1;
    end
    else if ((pc_run == 1) & (cfg_cnt_internal == 0)) begin
        pc_run_next = 0;
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
        cfg_cnt_next = num_cfg;
        addr_next = start_adr;
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
end
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

// TODO done pulse shift by NUM_GLB_TILES

endmodule
