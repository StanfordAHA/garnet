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
    input  logic                            cfg_pc_dma_on,
    input  dma_pc_header_t                  cfg_pc_dma_header,

    // interrupt pulse
    input  logic                            pc_start_pulse,
    output logic                            pc_done_pulse
);

endmodule
