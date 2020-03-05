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

    // axi
    // TODO
    input  logic                            proc2glb_wr_en,
    input  logic [BANK_DATA_WIDTH/8-1:0]    proc2glb_wr_strb,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc2glb_wr_addr,
    input  logic [BANK_DATA_WIDTH-1:0]      proc2glb_wr_data,
    input  logic                            proc2glb_rd_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc2glb_rd_addr,
    output logic [BANK_DATA_WIDTH-1:0]      glb2proc_rd_data,

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

// proc packet
proc_rq_packet_t proc_rq_packet_lr_wsti_int [NUM_TILES];
proc_rq_packet_t proc_rq_packet_rl_wsto_int [NUM_TILES];
proc_rq_packet_t proc_rq_packet_rl_esti_int [NUM_TILES];
proc_rq_packet_t proc_rq_packet_lr_esto_int [NUM_TILES];

proc_rs_packet_t proc_rs_packet_lr_wsti_int [NUM_TILES];
proc_rs_packet_t proc_rs_packet_rl_wsto_int [NUM_TILES];
proc_rs_packet_t proc_rs_packet_rl_esti_int [NUM_TILES];
proc_rs_packet_t proc_rs_packet_lr_esto_int [NUM_TILES];

// wr packet
wr_packet_t wr_packet_lr_wsti_int [NUM_TILES];
wr_packet_t wr_packet_rl_wsto_int [NUM_TILES];
wr_packet_t wr_packet_rl_esti_int [NUM_TILES];
wr_packet_t wr_packet_lr_esto_int [NUM_TILES];

// rdrq packet
rdrq_packet_t rdrq_packet_lr_wsti_int [NUM_TILES];
rdrq_packet_t rdrq_packet_rl_wsto_int [NUM_TILES];
rdrq_packet_t rdrq_packet_rl_esti_int [NUM_TILES];
rdrq_packet_t rdrq_packet_lr_esto_int [NUM_TILES];

// rdrs packet
rdrs_packet_t rdrs_packet_lr_wsti_int [NUM_TILES];
rdrs_packet_t rdrs_packet_rl_wsto_int [NUM_TILES];
rdrs_packet_t rdrs_packet_rl_esti_int [NUM_TILES];
rdrs_packet_t rdrs_packet_lr_esto_int [NUM_TILES];

// cfg from glc
cgra_cfg_t cgra_cfg_wsti_int [NUM_TILES];
cgra_cfg_t cgra_cfg_esto_int [NUM_TILES];

// interrupt pulse
logic [2*NUM_TILES-1:0] interrupt_pulse_wsti_int [NUM_TILES];
logic [2*NUM_TILES-1:0] interrupt_pulse_esto_int [NUM_TILES];
logic [2*NUM_TILES-1:0] interrupt_pulse_bundle;

// configuration interface
cfg_ifc if_cfg_t2t[NUM_TILES+1]();

//============================================================================//
// internal signal connection
//============================================================================//
// glb_tile_id
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        glb_tile_id[i] = i;
    end
end

// packet east to west connection
always_comb begin
    for (int i=NUM_TILES-1; i>=0; i=i-1) begin
        if (i == (NUM_TILES-1)) begin
            wr_packet_rl_esti_int[NUM_TILES-1] = '0;
            rdrq_packet_rl_esti_int[NUM_TILES-1] = '0;
            rdrs_packet_rl_esti_int[NUM_TILES-1] = '0;
        end
        else begin
            proc_rq_packet_rl_esti_int[i] = proc_rq_packet_rl_wsto_int[i+1]; 
            proc_rs_packet_rl_esti_int[i] = proc_rs_packet_rl_wsto_int[i+1]; 
            wr_packet_rl_esti_int[i] = wr_packet_rl_wsto_int[i+1]; 
            rdrq_packet_rl_esti_int[i] = rdrq_packet_rl_wsto_int[i+1]; 
            rdrs_packet_rl_esti_int[i] = rdrs_packet_rl_wsto_int[i+1]; 
        end
    end
end

// packet west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i == 0) begin
            wr_packet_lr_wsti_int[0] = '0;
            rdrq_packet_lr_wsti_int[0] = '0;
            rdrs_packet_lr_wsti_int[0] = '0;
        end
        else begin
            proc_rq_packet_lr_wsti_int[i] = proc_rq_packet_lr_esto_int[i-1];
            proc_rs_packet_lr_wsti_int[i] = proc_rs_packet_lr_esto_int[i-1];
            wr_packet_lr_wsti_int[i] = wr_packet_lr_esto_int[i-1]; 
            rdrq_packet_lr_wsti_int[i] = rdrq_packet_lr_esto_int[i-1]; 
            rdrs_packet_lr_wsti_int[i] = rdrs_packet_lr_esto_int[i-1]; 
        end
    end
end

// cgra_cfg from glc west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i == 0) begin
            cgra_cfg_wsti_int[0] = cgra_cfg_gc2glb;
        end
        else begin
            cgra_cfg_wsti_int[i] = cgra_cfg_esto_int[i-1]; 
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
// glb dummy tile start (left)
//============================================================================//
glb_tile_dummy_start glb_tile_dummy_start (
    .if_cfg_est_m       	(if_cfg_t2t[0]),
    .proc_rq_packet_lr_esto	(proc_rq_packet_lr_wsti_int[0]),
    .proc_rq_packet_rl_esti   	(proc_rq_packet_rl_wsto_int[0]),
    .proc_rs_packet_lr_esto   	(proc_rs_packet_lr_wsti_int[0]),
    .proc_rs_packet_rl_esti  	(proc_rs_packet_rl_wsto_int[0]),
    .*);

//============================================================================//
// glb dummy tile end (right)
//============================================================================//
glb_tile_dummy_end glb_tile_dummy_end (
    .if_cfg_wst_s       	(if_cfg_t2t[NUM_TILES]),
    .proc_rq_packet_rl_wsto	(proc_rq_packet_rl_esti_int[NUM_TILES-1]),
    .proc_rq_packet_lr_wsti   	(proc_rq_packet_lr_esto_int[NUM_TILES-1]),
    .proc_rs_packet_rl_wsto	(proc_rs_packet_rl_esti_int[NUM_TILES-1]),
    .proc_rs_packet_lr_wsti   	(proc_rs_packet_lr_esto_int[NUM_TILES-1]),
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

        // processor_packet
        .proc_rq_packet_lr_wsti    (proc_rq_packet_lr_wsti_int[i]),
        .proc_rq_packet_rl_wsto    (proc_rq_packet_rl_wsto_int[i]),
        .proc_rq_packet_rl_esti    (proc_rq_packet_rl_esti_int[i]),
        .proc_rq_packet_lr_esto    (proc_rq_packet_lr_esto_int[i]),
        .proc_rs_packet_lr_wsti    (proc_rs_packet_lr_wsti_int[i]),
        .proc_rs_packet_rl_wsto    (proc_rs_packet_rl_wsto_int[i]),
        .proc_rs_packet_rl_esti    (proc_rs_packet_rl_esti_int[i]),
        .proc_rs_packet_lr_esto    (proc_rs_packet_lr_esto_int[i]),
        
        // wr_packet
        .wr_packet_lr_wsti         (wr_packet_lr_wsti_int[i]),
        .wr_packet_rl_wsto         (wr_packet_rl_wsto_int[i]),
        .wr_packet_rl_esti         (wr_packet_rl_esti_int[i]),
        .wr_packet_lr_esto         (wr_packet_lr_esto_int[i]),
        
        // rdrq_packet
        .rdrq_packet_lr_wsti       (rdrq_packet_lr_wsti_int[i]),
        .rdrq_packet_rl_wsto       (rdrq_packet_rl_wsto_int[i]),
        .rdrq_packet_rl_esti       (rdrq_packet_rl_esti_int[i]),
        .rdrq_packet_lr_esto       (rdrq_packet_lr_esto_int[i]),

        // rdrs_packet
        .rdrs_packet_lr_wsti       (rdrs_packet_lr_wsti_int[i]),
        .rdrs_packet_rl_wsto       (rdrs_packet_rl_wsto_int[i]),
        .rdrs_packet_rl_esti       (rdrs_packet_rl_esti_int[i]),
        .rdrs_packet_lr_esto       (rdrs_packet_lr_esto_int[i]),

        // stream data f2g
        .stream_data_f2g        (stream_data_f2g[i]),
        .stream_data_valid_f2g  (stream_data_valid_f2g[i]),
        
        // stream data g2f
        .stream_data_g2f        (stream_data_g2f[i]),
        .stream_data_valid_g2f  (stream_data_valid_g2f[i]),

        // cgra cfg from glc
        .cgra_cfg_wsti          (cgra_cfg_wsti_int[i]),
        .cgra_cfg_esto          (cgra_cfg_esto_int[i]),

        // cgra cfg to fabric
        .cgra_cfg_g2f           (cgra_cfg_g2f[i]),

        // interrupt pulse
        .interrupt_pulse_wsti   (interrupt_pulse_wsti_int[i]),
        .interrupt_pulse_esto   (interrupt_pulse_esto_int[i]),

        // glb cfg
        .if_cfg_est_m           (if_cfg_t2t[i+1]),
        .if_cfg_wst_s           (if_cfg_t2t[i]),
        .*);
end: glb_tile_gen
endgenerate

endmodule
