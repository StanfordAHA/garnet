/*=============================================================================
** Module: glb_core_strm_mux.sv
** Description:
**              Global Buffer Core Stream Mux
** Author: Taeyoung Kong
** Change history: 
**      03/13/2020
**          - Implement first version of global buffer core stream data mux
**===========================================================================*/

module glb_core_strm_mux 
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                        clk,
    input  logic                        clk_en,
    input  logic                        reset,
    input  logic [CGRA_DATA_WIDTH-1:0]  stream_data_g2f_dma,
    input  logic                        stream_data_valid_g2f_dma,
    output logic [CGRA_DATA_WIDTH-1:0]  stream_data_g2f [CGRA_PER_GLB],
    output logic                        stream_data_valid_g2f [CGRA_PER_GLB],

    output logic [CGRA_DATA_WIDTH-1:0]  stream_data_f2g_dma,
    output logic                        stream_data_valid_f2g_dma,
    input  logic [CGRA_DATA_WIDTH-1:0]  stream_data_f2g [CGRA_PER_GLB],
    input  logic                        stream_data_valid_f2g [CGRA_PER_GLB],

    input logic                         cgra_soft_reset,

    // configuration
    input  logic [CGRA_PER_GLB-1:0]     cfg_strm_g2f_mux, //g2f config is one-hot encoding
    input  logic [CGRA_PER_GLB-1:0]     cfg_strm_f2g_mux, //f2g config is one-hot encoding
    input  logic [1:0]                  cfg_soft_reset_mux  //f2g config is one-hot encoding
);

logic cgra_soft_reset_d1;
logic [CGRA_DATA_WIDTH-1:0]  stream_data_g2f_int [CGRA_PER_GLB];
logic                        stream_data_valid_g2f_int [CGRA_PER_GLB];

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cgra_soft_reset_d1 <= 0;
    end
    else begin
        cgra_soft_reset_d1 <= cgra_soft_reset;
    end
end

always_comb begin
    for (int i=0; i < CGRA_PER_GLB; i=i+1) begin
        stream_data_g2f_int[i] = cfg_strm_g2f_mux[i] ? stream_data_g2f_dma : '0;
        stream_data_valid_g2f_int[i] = cfg_soft_reset_mux[i] ? cgra_soft_reset_d1 : (cfg_strm_g2f_mux[i] ? stream_data_valid_g2f_dma : 0);
    end
end

always_comb begin
    stream_data_f2g_dma = '0;
    stream_data_valid_f2g_dma = 0;
    for (int i=0; i < CGRA_PER_GLB; i=i+1) begin
        stream_data_f2g_dma = cfg_strm_f2g_mux[i] ? stream_data_f2g[i] : stream_data_f2g_dma;
        stream_data_valid_f2g_dma = cfg_strm_f2g_mux[i] ? stream_data_valid_f2g[i] : stream_data_valid_f2g_dma;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i < CGRA_PER_GLB; i=i+1) begin
            stream_data_g2f[i] <= '0;
            stream_data_valid_g2f[i] <= '0;
        end
    end
    else if (clk_en) begin
        for (int i=0; i < CGRA_PER_GLB; i=i+1) begin
            stream_data_g2f[i] <= stream_data_g2f_int[i];
            stream_data_valid_g2f[i] <= stream_data_valid_g2f_int[i];
        end
    end
end

endmodule
