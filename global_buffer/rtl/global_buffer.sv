/*=============================================================================
** Module: global_buffer.sv
** Description:
**              Global Buffer
** Author: Taeyoung Kong
** Change history: 02/01/2020 - Implement first version of global buffer
**===========================================================================*/
import global_buffer_pkg::*;

module global_buffer (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,

    // proc
    input  logic                            proc2glb_wr_en,
    input  logic [BANK_DATA_WIDTH/8-1:0]    proc2glb_wr_strb,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc2glb_wr_addr,
    input  logic [BANK_DATA_WIDTH-1:0]      proc2glb_wr_data,
    input  logic                            proc2glb_rd_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc2glb_rd_addr,
    output logic [BANK_DATA_WIDTH-1:0]      glb2proc_rd_data,

    // configuration from glc
    cfg_ifc.slave                           if_cfg,

    // cgra to glb streaming word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g [NUM_GLB_TILES][CGRA_PER_GLB],
    input  logic                            stream_data_valid_f2g [NUM_GLB_TILES][CGRA_PER_GLB],

    // glb to cgra streaming word
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f [NUM_GLB_TILES][CGRA_PER_GLB],
    output logic                            stream_data_valid_g2f [NUM_GLB_TILES][CGRA_PER_GLB],

    // cgra configuration from global controller
    input  cgra_cfg_t                       cgra_cfg_gc2glb,

    // cgra configuration to cgra
    output cgra_cfg_t                       cgra_cfg_g2f [NUM_GLB_TILES][CGRA_PER_GLB],

    input  logic [NUM_GLB_TILES-1:0]        strm_start_pulse,
    input  logic [NUM_GLB_TILES-1:0]        pc_start_pulse,
    output logic [3*NUM_GLB_TILES-1:0]      interrupt_pulse_bundle
);

//============================================================================//
// internal signal declaration
//============================================================================//
// tile id
logic [TILE_SEL_ADDR_WIDTH-1:0] glb_tile_id [NUM_GLB_TILES];

// proc packet
packet_t    proc_packet_w2e_wsti_int [NUM_GLB_TILES];
packet_t    proc_packet_e2w_wsto_int [NUM_GLB_TILES];
packet_t    proc_packet_e2w_esti_int [NUM_GLB_TILES];
packet_t    proc_packet_w2e_esto_int [NUM_GLB_TILES];

// stream packet
packet_t    strm_packet_w2e_wsti_int [NUM_GLB_TILES];
packet_t    strm_packet_e2w_wsto_int [NUM_GLB_TILES];
packet_t    strm_packet_e2w_esti_int [NUM_GLB_TILES];
packet_t    strm_packet_w2e_esto_int [NUM_GLB_TILES];

// cfg from glc
cgra_cfg_t cgra_cfg_wsti_int [NUM_GLB_TILES];
cgra_cfg_t cgra_cfg_esto_int [NUM_GLB_TILES];

// trigger
logic [NUM_GLB_TILES-1:0] strm_start_pulse_wsti_int [NUM_GLB_TILES];
logic [NUM_GLB_TILES-1:0] strm_start_pulse_esto_int [NUM_GLB_TILES];
logic [NUM_GLB_TILES-1:0] pc_start_pulse_wsti_int [NUM_GLB_TILES];
logic [NUM_GLB_TILES-1:0] pc_start_pulse_esto_int [NUM_GLB_TILES];

// interrupt pulse
logic [3*NUM_GLB_TILES-1:0] interrupt_pulse_esti_int [NUM_GLB_TILES];
logic [3*NUM_GLB_TILES-1:0] interrupt_pulse_wsto_int [NUM_GLB_TILES];

// configuration interface
cfg_ifc if_cfg_t2t[NUM_GLB_TILES+1]();

//============================================================================//
// internal signal connection
//============================================================================//
// glb_tile_id
always_comb begin
    for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
        glb_tile_id[i] = i;
    end
end

// packet east to west connection
always_comb begin
    for (int i=NUM_GLB_TILES-2; i>=0; i=i-1) begin
        proc_packet_e2w_esti_int[i] = proc_packet_e2w_wsto_int[i+1]; 
        strm_packet_e2w_esti_int[i] = strm_packet_e2w_wsto_int[i+1]; 
    end
end

// packet west to east connection
always_comb begin
    for (int i=1; i<NUM_GLB_TILES; i=i+1) begin
        proc_packet_w2e_wsti_int[i] = proc_packet_w2e_esto_int[i-1];
        strm_packet_w2e_wsti_int[i] = strm_packet_w2e_esto_int[i-1]; 
    end
end

// cgra_cfg from glc west to east connection
always_comb begin
    for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
        if (i == 0) begin
            cgra_cfg_wsti_int[0] = cgra_cfg_gc2glb;
        end
        else begin
            cgra_cfg_wsti_int[i] = cgra_cfg_esto_int[i-1]; 
        end
    end
end

// start pulse from west to east connection
always_comb begin
    for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
        if (i == 0) begin
            strm_start_pulse_wsti_int[0] = strm_start_pulse;
            pc_start_pulse_wsti_int[0] = pc_start_pulse;
        end
        else begin
            strm_start_pulse_wsti_int[i] = strm_start_pulse_esto_int[i-1]; 
            pc_start_pulse_wsti_int[i] = pc_start_pulse_esto_int[i-1]; 
        end
    end
end

// interrupt east to west
always_comb begin
    for (int i=NUM_GLB_TILES-1; i>=0; i=i-1) begin
        if (i == (NUM_GLB_TILES-1)) begin
            interrupt_pulse_esti_int[NUM_GLB_TILES-1] = '0;
        end
        else begin
            interrupt_pulse_esti_int[i] = interrupt_pulse_wsto_int[i+1]; 
        end
    end
end
assign interrupt_pulse_bundle = interrupt_pulse_wsto_int[0];

//============================================================================//
// glb dummy tile start (left)
//============================================================================//
glb_dummy_start glb_dummy_start (
    .if_cfg_est_m       (if_cfg_t2t[0]),
    .proc_packet_w2e_esto   (proc_packet_w2e_wsti_int[0]),
    .proc_packet_e2w_esti   (proc_packet_e2w_wsto_int[0]),
    .strm_packet_w2e_esto   (strm_packet_w2e_wsti_int[0]),
    .*);

//============================================================================//
// glb dummy tile end (right)
//============================================================================//
glb_dummy_end glb_dummy_end (
    .if_cfg_wst_s       (if_cfg_t2t[NUM_GLB_TILES]),
    .proc_packet_e2w_wsto   (proc_packet_e2w_esti_int[NUM_GLB_TILES-1]),
    .proc_packet_w2e_wsti   (proc_packet_w2e_esto_int[NUM_GLB_TILES-1]),
    .strm_packet_e2w_wsto   (strm_packet_e2w_esti_int[NUM_GLB_TILES-1]),
    .*);

//============================================================================//
// glb tiles
//============================================================================//
genvar i;
generate
for (i=0; i<NUM_GLB_TILES; i=i+1) begin: glb_tile_gen
    glb_tile glb_tile (
        // tile id
        .glb_tile_id                (glb_tile_id[i]),

        // processor packet
        .proc_packet_w2e_wsti           (proc_packet_w2e_wsti_int[i]),
        .proc_packet_e2w_wsto           (proc_packet_e2w_wsto_int[i]),
        .proc_packet_e2w_esti           (proc_packet_e2w_esti_int[i]),
        .proc_packet_w2e_esto           (proc_packet_w2e_esto_int[i]),
        
        // stream packet
        .strm_packet_w2e_wsti           (strm_packet_w2e_wsti_int[i]),
        .strm_packet_e2w_wsto           (strm_packet_e2w_wsto_int[i]),
        .strm_packet_e2w_esti           (strm_packet_e2w_esti_int[i]),
        .strm_packet_w2e_esto           (strm_packet_w2e_esto_int[i]),
        
        // stream data f2g
        .stream_data_f2g            (stream_data_f2g[i]),
        .stream_data_valid_f2g      (stream_data_valid_f2g[i]),
        
        // stream data g2f
        .stream_data_g2f            (stream_data_g2f[i]),
        .stream_data_valid_g2f      (stream_data_valid_g2f[i]),

        // trigger pulse
        .strm_start_pulse_wsti      (strm_start_pulse_wsti_int[i]),
        .strm_start_pulse_esto      (strm_start_pulse_esto_int[i]),
        .pc_start_pulse_wsti        (pc_start_pulse_wsti_int[i]),
        .pc_start_pulse_esto        (pc_start_pulse_esto_int[i]),

        // cgra cfg from glc
        .cgra_cfg_jtag_wsti         (cgra_cfg_wsti_int[i]),
        .cgra_cfg_jtag_esto         (cgra_cfg_esto_int[i]),
        .cgra_cfg_pc_wsti           (cgra_cfg_wsti_int[i]),
        .cgra_cfg_pc_esto           (cgra_cfg_esto_int[i]),
        // cgra cfg to fabric
        .cgra_cfg_g2f               (cgra_cfg_g2f[i]),

        // interrupt pulse
        .interrupt_pulse_esti       (interrupt_pulse_esti_int[i]),
        .interrupt_pulse_wsto       (interrupt_pulse_wsto_int[i]),

        // glb cfg
        .if_cfg_est_m               (if_cfg_t2t[i+1]),
        .if_cfg_wst_s               (if_cfg_t2t[i]),
        .*);
end: glb_tile_gen
endgenerate

endmodule
