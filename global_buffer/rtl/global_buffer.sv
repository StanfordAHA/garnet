/*=============================================================================
** Module: global_buffer.sv
** Description:
**              Global Buffer
** Author: Taeyoung Kong
** Change history: 02/01/2020 - Implement first version of global buffer
**===========================================================================*/
`include "axil_ifc.sv"
`include "cfg_ifc.sv"
import global_buffer_pkg::*;

module global_buffer (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,

    // axi lite
    axil_ifc.slave                          if_axil,

    // cgra to glb streaming word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g [NUM_TILES],
    input  logic                            stream_data_valid_f2g [NUM_TILES],

    // glb to cgra streaming word
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f [NUM_TILES],
    output logic                            stream_data_valid_g2f [NUM_TILES],

    // cgra configuration from global controller
    input  cgra_cfg_t                       cgra_cfg_gc2glb,

    // cgra configuration to cgra
    output cgra_cfg_t                       cgra_cfg_g2f [NUM_TILES],

    output logic                            interrupt
);

//============================================================================//
// internal signal declaration
//============================================================================//
// tile id
logic [TILE_SEL_ADDR_WIDTH-1:0] glb_tile_id [NUM_TILES];

// wr packet
wr_packet_t wr_packet_wsti_int [NUM_TILES];
wr_packet_t wr_packet_wsto_int [NUM_TILES];
wr_packet_t wr_packet_esti_int [NUM_TILES];
wr_packet_t wr_packet_esto_int [NUM_TILES];

// cfg from glc
cgra_cfg_t cgra_cfg_esti_int [NUM_TILES];
cgra_cfg_t cgra_cfg_wsto_int [NUM_TILES];

// interrupt pulse
logic [2*NUM_TILES-1:0] interrupt_pulse_wsti_int [NUM_TILES];
logic [2*NUM_TILES-1:0] interrupt_pulse_esto_int [NUM_TILES];
logic [2*NUM_TILES-1:0] interrupt_pulse_bundle;

// configuration interface
cfg_ifc if_cfg_t2t[NUM_TILES+1]();

// configuration clock gating
logic cfg_wr_clk_en [NUM_TILES+1];
logic cfg_rd_clk_en [NUM_TILES+1];

//============================================================================//
// internal signal connection
//============================================================================//
// glb_tile_id
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        glb_tile_id[i] = i;
    end
end

// wr_packet east to west connection
always_comb begin
    for (int i=NUM_TILES-1; i>=0; i=i-1) begin
        if (i == (NUM_TILES-1)) begin
            wr_packet_esti_int[NUM_TILES-1] = '0;
        end
        else begin
            wr_packet_esti_int[i] = wr_packet_wsto_int[i+1]; 
        end
    end
end

// wr_packet west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i == 0) begin
            wr_packet_wsti_int[0] = '0;
        end
        else begin
            wr_packet_wsti_int[i] = wr_packet_esto_int[i-1]; 
        end
    end
end

// cgra_cfg from glc east to west connection
always_comb begin
    for (int i=NUM_TILES-1; i>=0; i=i-1) begin
        if (i == (NUM_TILES-1)) begin
            cgra_cfg_esti_int[NUM_TILES-1] = cgra_cfg_gc2glb;
        end
        else begin
            cgra_cfg_esti_int[i] = cgra_cfg_wsto_int[i+1]; 
        end
    end
end

// interrupt west to east
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i == 0) begin
            interrupt_pulse_wsti_int[0] = '0;
        end
        else begin
            interrupt_pulse_wsti_int[i] = interrupt_pulse_esto_int[i-1]; 
        end
    end
end
assign interrupt_pulse_bundle = interrupt_pulse_esto_int[NUM_TILES-1];

//============================================================================//
// glb dummy tile right
//============================================================================//
glb_tile_dummy_r glb_tile_dummy_r (
    .if_cfg_wst_m       (if_cfg_t2t[NUM_TILES]),
    .cfg_wr_tile_clk_en (cfg_wr_clk_en[NUM_TILES]),
    .cfg_rd_tile_clk_en (cfg_rd_clk_en[NUM_TILES]),
    .*);

//============================================================================//
// glb dummy tile left
//============================================================================//
glb_tile_dummy_l glb_tile_dummy_l (
    .if_cfg_est_s (if_cfg_t2t[0]),
    .*);

//============================================================================//
// glb tiles
//============================================================================//
genvar i;
generate
for (i=0; i<NUM_TILES; i=i+1) begin: glb_tile_gen
    glb_tile glb_tile (
        // tile id
        .glb_tile_id            (glb_tile_id[i]),

        // wr_packet
        .wr_packet_wsti         (wr_packet_wsti_int[i]),
        .wr_packet_wsto         (wr_packet_wsto_int[i]),
        .wr_packet_esti         (wr_packet_esti_int[i]),
        .wr_packet_esto         (wr_packet_esto_int[i]),

        // stream data f2g
        .stream_data_f2g        (stream_data_f2g[i]),
        .stream_data_valid_f2g  (stream_data_valid_f2g[i]),
        
        // stream data g2f
        .stream_data_g2f        (stream_data_g2f[i]),
        .stream_data_valid_g2f  (stream_data_valid_g2f[i]),

        // cgra cfg from glc
        .cgra_cfg_esti          (cgra_cfg_esti_int[i]),
        .cgra_cfg_wsto          (cgra_cfg_wsto_int[i]),

        // cgra cfg to fabric
        .cgra_cfg_g2f           (cgra_cfg_g2f[i]),

        // interrupt pulse
        .interrupt_pulse_wsti   (interrupt_pulse_wsti_int[i]),
        .interrupt_pulse_esto   (interrupt_pulse_esto_int[i]),

        // glb cfg
        .if_cfg_est_s           (if_cfg_t2t[i+1]),
        .if_cfg_wst_m           (if_cfg_t2t[i]),

        // glb cfg clk gating
        .cfg_wr_clk_en_esti     (cfg_wr_clk_en[i+1]),
        .cfg_wr_clk_en_wsto     (cfg_wr_clk_en[i]),
        .cfg_rd_clk_en_esti     (cfg_rd_clk_en[i+1]),
        .cfg_rd_clk_en_wsto     (cfg_rd_clk_en[i]),
        .*);
end: glb_tile_gen
endgenerate

endmodule
