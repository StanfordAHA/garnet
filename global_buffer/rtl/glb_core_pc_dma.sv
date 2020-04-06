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

//============================================================================//
// Dummy logic
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        pc_done_pulse <= 0;
    end
    else begin
        pc_done_pulse <= pc_start_pulse;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rdrq_packet <= '0;
    end
    else if (clk_en) begin
        rdrq_packet <= rdrs_packet;
    end
end

assign cgra_cfg_c2sw = '0;

endmodule
