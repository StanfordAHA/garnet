/*=============================================================================
** Module: global_buffer.sv
** Description:
**              Global Buffer
** Author: Taeyoung Kong
** Change history: 02/01/2020 - Implement first version of global buffer
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module global_buffer (

    // LEFT
    input  logic                                                                clk,
    input  logic                                                                stall,
    input  logic                                                                reset,
    input  logic                                                                cgra_stall_in,

    // proc
    input  logic                                                                proc_wr_en,
    input  logic [BANK_DATA_WIDTH/8-1:0]                                        proc_wr_strb,
    input  logic [GLB_ADDR_WIDTH-1:0]                                           proc_wr_addr,
    input  logic [BANK_DATA_WIDTH-1:0]                                          proc_wr_data,
    input  logic                                                                proc_rd_en,
    input  logic [GLB_ADDR_WIDTH-1:0]                                           proc_rd_addr,
    output logic [BANK_DATA_WIDTH-1:0]                                          proc_rd_data,
    output logic                                                                proc_rd_data_valid,

    // configuration of glb from glc
    input  logic                                                                if_cfg_wr_en,
    input  logic                                                                if_cfg_wr_clk_en,
    input  logic [AXI_ADDR_WIDTH-1:0]                                           if_cfg_wr_addr,
    input  logic [AXI_DATA_WIDTH-1:0]                                           if_cfg_wr_data,
    input  logic                                                                if_cfg_rd_en,
    input  logic                                                                if_cfg_rd_clk_en,
    input  logic [AXI_ADDR_WIDTH-1:0]                                           if_cfg_rd_addr,
    output logic [AXI_DATA_WIDTH-1:0]                                           if_cfg_rd_data,
    output logic                                                                if_cfg_rd_data_valid,

    // configuration of sram from glc
    input  logic                                                                if_sram_cfg_wr_en,
    input  logic                                                                if_sram_cfg_wr_clk_en,
    input  logic [GLB_ADDR_WIDTH-1:0]                                           if_sram_cfg_wr_addr,
    input  logic [AXI_DATA_WIDTH-1:0]                                           if_sram_cfg_wr_data,
    input  logic                                                                if_sram_cfg_rd_en,
    input  logic                                                                if_sram_cfg_rd_clk_en,
    input  logic [GLB_ADDR_WIDTH-1:0]                                           if_sram_cfg_rd_addr,
    output logic [AXI_DATA_WIDTH-1:0]                                           if_sram_cfg_rd_data,
    output logic                                                                if_sram_cfg_rd_data_valid,

    // cgra configuration from global controller
    input  logic                                                                cgra_cfg_jtag_gc2glb_wr_en,
    input  logic                                                                cgra_cfg_jtag_gc2glb_rd_en,
    input  logic [CGRA_CFG_ADDR_WIDTH-1:0]                                      cgra_cfg_jtag_gc2glb_addr,
    input  logic [CGRA_CFG_DATA_WIDTH-1:0]                                      cgra_cfg_jtag_gc2glb_data,

    // control pulse
    input  logic [NUM_GLB_TILES-1:0]                                            strm_start_pulse,
    input  logic [NUM_GLB_TILES-1:0]                                            pc_start_pulse,
    output logic [NUM_GLB_TILES-1:0]                                            strm_g2f_interrupt_pulse,
    output logic [NUM_GLB_TILES-1:0]                                            strm_f2g_interrupt_pulse,
    output logic [NUM_GLB_TILES-1:0]                                            pcfg_g2f_interrupt_pulse,

    // soft reset
    input  logic                                                                cgra_soft_reset,

    // BOTTOM
    // cgra to glb streaming word
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0]     stream_data_f2g,
    input  logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          stream_data_valid_f2g,

    // glb to cgra streaming word
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0]     stream_data_g2f,
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          stream_data_valid_g2f,

    // cgra configuration to cgra
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_stall,
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_cfg_g2f_cfg_wr_en,
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          cgra_cfg_g2f_cfg_rd_en,
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_ADDR_WIDTH-1:0] cgra_cfg_g2f_cfg_addr,
    output logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0] cgra_cfg_g2f_cfg_data
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

// pc packet
rd_packet_t pc_packet_w2e_wsti_int [NUM_GLB_TILES];
rd_packet_t pc_packet_e2w_wsto_int [NUM_GLB_TILES];
rd_packet_t pc_packet_e2w_esti_int [NUM_GLB_TILES];
rd_packet_t pc_packet_w2e_esto_int [NUM_GLB_TILES];

// cfg from glc
cgra_cfg_t cgra_cfg_jtag_gc2glb;
cgra_cfg_t cgra_cfg_jtag_wsti_int [NUM_GLB_TILES];
cgra_cfg_t cgra_cfg_jtag_esto_int [NUM_GLB_TILES];
cgra_cfg_t cgra_cfg_pc_wsti_int [NUM_GLB_TILES];
cgra_cfg_t cgra_cfg_pc_esto_int [NUM_GLB_TILES];

// configuration interface
cfg_ifc #(.AWIDTH(AXI_ADDR_WIDTH), .DWIDTH(AXI_DATA_WIDTH)) if_cfg_t2t[NUM_GLB_TILES+1]();
cfg_ifc #(.AWIDTH(GLB_ADDR_WIDTH), .DWIDTH(CGRA_CFG_DATA_WIDTH)) if_sram_cfg_t2t[NUM_GLB_TILES+1]();

logic cfg_tile_connected_internal [NUM_GLB_TILES+1];
assign cfg_tile_connected_internal[0] = 0;
logic cfg_pc_tile_connected_internal [NUM_GLB_TILES+1];
assign cfg_pc_tile_connected_internal[0] = 0;

logic cgra_soft_reset_internal_d1;
logic [NUM_GLB_TILES-1:0] strm_start_pulse_internal_d1;
logic [NUM_GLB_TILES-1:0] pc_start_pulse_internal_d1;
logic [NUM_GLB_TILES-1:0] strm_g2f_interrupt_pulse_internal;
logic [NUM_GLB_TILES-1:0] strm_f2g_interrupt_pulse_internal;
logic [NUM_GLB_TILES-1:0] pcfg_g2f_interrupt_pulse_internal;

logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0]     stream_data_f2g_int;
logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          stream_data_valid_f2g_int;

logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0]     stream_data_g2f_int;
logic [NUM_GLB_TILES-1:0][CGRA_PER_GLB-1:0]                          stream_data_valid_g2f_int;

//============================================================================//
// register all input/output
//============================================================================//
// stream data
// these should be clock gated
logic stall_d1, clk_en;
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        stall_d1 <= 0;
    end
    else begin
        stall_d1 <= stall;
    end
end
assign clk_en = !stall_d1;

always_ff @(posedge reset or posedge clk) begin
    if (reset) begin
        stream_data_f2g_int <= '0;
        stream_data_valid_f2g_int <= '0;
    end
    else if (clk_en) begin
        stream_data_f2g_int <= stream_data_f2g;
        stream_data_valid_f2g_int <= stream_data_valid_f2g;
    end
end

always_ff @(posedge reset or posedge clk) begin
    if (reset) begin
        stream_data_g2f <= '0;
        stream_data_valid_g2f <= '0;
    end
    else if (clk_en) begin
        stream_data_g2f <= stream_data_g2f_int;
        stream_data_valid_g2f <= stream_data_valid_g2f_int;
    end
end

// soft reset register
always_ff @(posedge reset or posedge clk) begin
    if (reset) begin
        cgra_soft_reset_internal_d1 <= 0;
    end
    else begin
        cgra_soft_reset_internal_d1 <= cgra_soft_reset;
    end
end

// start pulse register
always_ff @(posedge reset or posedge clk) begin
    if (reset) begin
        strm_start_pulse_internal_d1 <= 0;
        pc_start_pulse_internal_d1 <= 0;
    end
    else begin
        strm_start_pulse_internal_d1 <= strm_start_pulse;
        pc_start_pulse_internal_d1 <= pc_start_pulse;
    end
end

// interrupt pulse register
always_ff @(posedge reset or posedge clk) begin
    if (reset) begin
        strm_g2f_interrupt_pulse <= 0;
        strm_f2g_interrupt_pulse <= 0;
        pcfg_g2f_interrupt_pulse <= 0;
    end
    else begin
        strm_g2f_interrupt_pulse <= strm_g2f_interrupt_pulse_internal;
        strm_f2g_interrupt_pulse <= strm_f2g_interrupt_pulse_internal;
        pcfg_g2f_interrupt_pulse <= pcfg_g2f_interrupt_pulse_internal;
    end
end

// cgra_cfg from jtag glc west to east connection
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cgra_cfg_jtag_gc2glb.cfg_wr_en <= 0;
        cgra_cfg_jtag_gc2glb.cfg_rd_en <= 0;
        cgra_cfg_jtag_gc2glb.cfg_addr <= 0;
        cgra_cfg_jtag_gc2glb.cfg_data <= 0;
    end
    else begin
        cgra_cfg_jtag_gc2glb.cfg_wr_en <= cgra_cfg_jtag_gc2glb_wr_en;
        cgra_cfg_jtag_gc2glb.cfg_rd_en <= cgra_cfg_jtag_gc2glb_rd_en;
        cgra_cfg_jtag_gc2glb.cfg_addr <= cgra_cfg_jtag_gc2glb_addr;
        cgra_cfg_jtag_gc2glb.cfg_data <= cgra_cfg_jtag_gc2glb_data;
    end
end

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
        pc_packet_e2w_esti_int[i] = pc_packet_e2w_wsto_int[i+1]; 
    end
end

// packet west to east connection
always_comb begin
    for (int i=1; i<NUM_GLB_TILES; i=i+1) begin
        proc_packet_w2e_wsti_int[i] = proc_packet_w2e_esto_int[i-1];
        strm_packet_w2e_wsti_int[i] = strm_packet_w2e_esto_int[i-1]; 
        pc_packet_w2e_wsti_int[i] = pc_packet_w2e_esto_int[i-1]; 
    end
end

always_comb begin
    for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
        if (i == 0) begin
            cgra_cfg_jtag_wsti_int[0] = cgra_cfg_jtag_gc2glb;
        end
        else begin
            cgra_cfg_jtag_wsti_int[i] = cgra_cfg_jtag_esto_int[i-1]; 
        end
    end
end

// cgra_cfg pc  west to east connection
always_comb begin
    for (int i=0; i<NUM_GLB_TILES; i=i+1) begin
        if (i == 0) begin
            cgra_cfg_pc_wsti_int[0] = '0;
        end
        else begin
            cgra_cfg_pc_wsti_int[i] = cgra_cfg_pc_esto_int[i-1]; 
        end
    end
end

//============================================================================//
// glb dummy tile start (left)
//============================================================================//
glb_dummy_start glb_dummy_start (
    .if_cfg_est_m           (if_cfg_t2t[0]),
    .if_sram_cfg_est_m      (if_sram_cfg_t2t[0]),
    .proc_packet_w2e_esto   (proc_packet_w2e_wsti_int[0]),
    .proc_packet_e2w_esti   (proc_packet_e2w_wsto_int[0]),
    .strm_packet_w2e_esto   (strm_packet_w2e_wsti_int[0]),
    .pc_packet_w2e_esto     (pc_packet_w2e_wsti_int[0]),
    .*);

//============================================================================//
// glb dummy tile end (right)
//============================================================================//
glb_dummy_end glb_dummy_end (
    .if_cfg_wst_s           (if_cfg_t2t[NUM_GLB_TILES]),
    .if_sram_cfg_wst_s      (if_sram_cfg_t2t[NUM_GLB_TILES]),
    .proc_packet_e2w_wsto   (proc_packet_e2w_esti_int[NUM_GLB_TILES-1]),
    .proc_packet_w2e_wsti   (proc_packet_w2e_esto_int[NUM_GLB_TILES-1]),
    .strm_packet_e2w_wsto   (strm_packet_e2w_esti_int[NUM_GLB_TILES-1]),
    .pc_packet_e2w_wsto     (pc_packet_e2w_esti_int[NUM_GLB_TILES-1]),
    .*);

//============================================================================//
// glb tiles
//============================================================================//
genvar i;
generate
for (i=0; i<NUM_GLB_TILES; i=i+1) begin: glb_tile_gen
    glb_tile glb_tile (
        // tile id
        .glb_tile_id                        (glb_tile_id[i]),

        // processor packet
        // .proc_wr_packet_sel_e2w_esti        (proc_packet_e2w_esti_int[i].wr.packet_sel),
        // .proc_rdrq_packet_sel_e2w_esti      (proc_packet_e2w_esti_int[i].rdrq.packet_sel),
        // .proc_rdrs_packet_sel_e2w_esti      (proc_packet_e2w_esti_int[i].rdrs.packet_sel),
        .proc_wr_en_e2w_esti                (proc_packet_e2w_esti_int[i].wr.wr_en),
        .proc_wr_strb_e2w_esti              (proc_packet_e2w_esti_int[i].wr.wr_strb),
        .proc_wr_addr_e2w_esti              (proc_packet_e2w_esti_int[i].wr.wr_addr),
        .proc_wr_data_e2w_esti              (proc_packet_e2w_esti_int[i].wr.wr_data),
        .proc_rd_en_e2w_esti                (proc_packet_e2w_esti_int[i].rdrq.rd_en),
        .proc_rd_addr_e2w_esti              (proc_packet_e2w_esti_int[i].rdrq.rd_addr),
        .proc_rd_data_e2w_esti              (proc_packet_e2w_esti_int[i].rdrs.rd_data),
        .proc_rd_data_valid_e2w_esti        (proc_packet_e2w_esti_int[i].rdrs.rd_data_valid),

        // .proc_wr_packet_sel_w2e_esto        (proc_packet_w2e_esto_int[i].wr.packet_sel),
        // .proc_rdrq_packet_sel_w2e_esto      (proc_packet_w2e_esto_int[i].rdrq.packet_sel),
        // .proc_rdrs_packet_sel_w2e_esto      (proc_packet_w2e_esto_int[i].rdrs.packet_sel),
        .proc_wr_en_w2e_esto                (proc_packet_w2e_esto_int[i].wr.wr_en),
        .proc_wr_strb_w2e_esto              (proc_packet_w2e_esto_int[i].wr.wr_strb),
        .proc_wr_addr_w2e_esto              (proc_packet_w2e_esto_int[i].wr.wr_addr),
        .proc_wr_data_w2e_esto              (proc_packet_w2e_esto_int[i].wr.wr_data),
        .proc_rd_en_w2e_esto                (proc_packet_w2e_esto_int[i].rdrq.rd_en),
        .proc_rd_addr_w2e_esto              (proc_packet_w2e_esto_int[i].rdrq.rd_addr),
        .proc_rd_data_w2e_esto              (proc_packet_w2e_esto_int[i].rdrs.rd_data),
        .proc_rd_data_valid_w2e_esto        (proc_packet_w2e_esto_int[i].rdrs.rd_data_valid),

        // .proc_wr_packet_sel_w2e_wsti        (proc_packet_w2e_wsti_int[i].wr.packet_sel),
        // .proc_rdrq_packet_sel_w2e_wsti      (proc_packet_w2e_wsti_int[i].rdrq.packet_sel),
        // .proc_rdrs_packet_sel_w2e_wsti      (proc_packet_w2e_wsti_int[i].rdrs.packet_sel),
        .proc_wr_en_w2e_wsti                (proc_packet_w2e_wsti_int[i].wr.wr_en),
        .proc_wr_strb_w2e_wsti              (proc_packet_w2e_wsti_int[i].wr.wr_strb),
        .proc_wr_addr_w2e_wsti              (proc_packet_w2e_wsti_int[i].wr.wr_addr),
        .proc_wr_data_w2e_wsti              (proc_packet_w2e_wsti_int[i].wr.wr_data),
        .proc_rd_en_w2e_wsti                (proc_packet_w2e_wsti_int[i].rdrq.rd_en),
        .proc_rd_addr_w2e_wsti              (proc_packet_w2e_wsti_int[i].rdrq.rd_addr),
        .proc_rd_data_w2e_wsti              (proc_packet_w2e_wsti_int[i].rdrs.rd_data),
        .proc_rd_data_valid_w2e_wsti        (proc_packet_w2e_wsti_int[i].rdrs.rd_data_valid),

        // .proc_wr_packet_sel_e2w_wsto        (proc_packet_e2w_wsto_int[i].wr.packet_sel),
        // .proc_rdrq_packet_sel_e2w_wsto      (proc_packet_e2w_wsto_int[i].rdrq.packet_sel),
        // .proc_rdrs_packet_sel_e2w_wsto      (proc_packet_e2w_wsto_int[i].rdrs.packet_sel),
        .proc_wr_en_e2w_wsto                (proc_packet_e2w_wsto_int[i].wr.wr_en),
        .proc_wr_strb_e2w_wsto              (proc_packet_e2w_wsto_int[i].wr.wr_strb),
        .proc_wr_addr_e2w_wsto              (proc_packet_e2w_wsto_int[i].wr.wr_addr),
        .proc_wr_data_e2w_wsto              (proc_packet_e2w_wsto_int[i].wr.wr_data),
        .proc_rd_en_e2w_wsto                (proc_packet_e2w_wsto_int[i].rdrq.rd_en),
        .proc_rd_addr_e2w_wsto              (proc_packet_e2w_wsto_int[i].rdrq.rd_addr),
        .proc_rd_data_e2w_wsto              (proc_packet_e2w_wsto_int[i].rdrs.rd_data),
        .proc_rd_data_valid_e2w_wsto        (proc_packet_e2w_wsto_int[i].rdrs.rd_data_valid),

        // stream packet
        // .strm_wr_packet_sel_e2w_esti        (strm_packet_e2w_esti_int[i].wr.packet_sel),
        // .strm_rdrq_packet_sel_e2w_esti      (strm_packet_e2w_esti_int[i].rdrq.packet_sel),
        // .strm_rdrs_packet_sel_e2w_esti      (strm_packet_e2w_esti_int[i].rdrs.packet_sel),
        .strm_wr_en_e2w_esti                (strm_packet_e2w_esti_int[i].wr.wr_en),
        .strm_wr_strb_e2w_esti              (strm_packet_e2w_esti_int[i].wr.wr_strb),
        .strm_wr_addr_e2w_esti              (strm_packet_e2w_esti_int[i].wr.wr_addr),
        .strm_wr_data_e2w_esti              (strm_packet_e2w_esti_int[i].wr.wr_data),
        .strm_rd_en_e2w_esti                (strm_packet_e2w_esti_int[i].rdrq.rd_en),
        .strm_rd_addr_e2w_esti              (strm_packet_e2w_esti_int[i].rdrq.rd_addr),
        .strm_rd_data_e2w_esti              (strm_packet_e2w_esti_int[i].rdrs.rd_data),
        .strm_rd_data_valid_e2w_esti        (strm_packet_e2w_esti_int[i].rdrs.rd_data_valid),

        // .strm_wr_packet_sel_w2e_esto        (strm_packet_w2e_esto_int[i].wr.packet_sel),
        // .strm_rdrq_packet_sel_w2e_esto      (strm_packet_w2e_esto_int[i].rdrq.packet_sel),
        // .strm_rdrs_packet_sel_w2e_esto      (strm_packet_w2e_esto_int[i].rdrs.packet_sel),
        .strm_wr_en_w2e_esto                (strm_packet_w2e_esto_int[i].wr.wr_en),
        .strm_wr_strb_w2e_esto              (strm_packet_w2e_esto_int[i].wr.wr_strb),
        .strm_wr_addr_w2e_esto              (strm_packet_w2e_esto_int[i].wr.wr_addr),
        .strm_wr_data_w2e_esto              (strm_packet_w2e_esto_int[i].wr.wr_data),
        .strm_rd_en_w2e_esto                (strm_packet_w2e_esto_int[i].rdrq.rd_en),
        .strm_rd_addr_w2e_esto              (strm_packet_w2e_esto_int[i].rdrq.rd_addr),
        .strm_rd_data_w2e_esto              (strm_packet_w2e_esto_int[i].rdrs.rd_data),
        .strm_rd_data_valid_w2e_esto        (strm_packet_w2e_esto_int[i].rdrs.rd_data_valid),

        // .strm_wr_packet_sel_w2e_wsti        (strm_packet_w2e_wsti_int[i].wr.packet_sel),
        // .strm_rdrq_packet_sel_w2e_wsti      (strm_packet_w2e_wsti_int[i].rdrq.packet_sel),
        // .strm_rdrs_packet_sel_w2e_wsti      (strm_packet_w2e_wsti_int[i].rdrs.packet_sel),
        .strm_wr_en_w2e_wsti                (strm_packet_w2e_wsti_int[i].wr.wr_en),
        .strm_wr_strb_w2e_wsti              (strm_packet_w2e_wsti_int[i].wr.wr_strb),
        .strm_wr_addr_w2e_wsti              (strm_packet_w2e_wsti_int[i].wr.wr_addr),
        .strm_wr_data_w2e_wsti              (strm_packet_w2e_wsti_int[i].wr.wr_data),
        .strm_rd_en_w2e_wsti                (strm_packet_w2e_wsti_int[i].rdrq.rd_en),
        .strm_rd_addr_w2e_wsti              (strm_packet_w2e_wsti_int[i].rdrq.rd_addr),
        .strm_rd_data_w2e_wsti              (strm_packet_w2e_wsti_int[i].rdrs.rd_data),
        .strm_rd_data_valid_w2e_wsti        (strm_packet_w2e_wsti_int[i].rdrs.rd_data_valid),

        // .strm_wr_packet_sel_e2w_wsto        (strm_packet_e2w_wsto_int[i].wr.packet_sel),
        // .strm_rdrq_packet_sel_e2w_wsto      (strm_packet_e2w_wsto_int[i].rdrq.packet_sel),
        // .strm_rdrs_packet_sel_e2w_wsto      (strm_packet_e2w_wsto_int[i].rdrs.packet_sel),
        .strm_wr_en_e2w_wsto                (strm_packet_e2w_wsto_int[i].wr.wr_en),
        .strm_wr_strb_e2w_wsto              (strm_packet_e2w_wsto_int[i].wr.wr_strb),
        .strm_wr_addr_e2w_wsto              (strm_packet_e2w_wsto_int[i].wr.wr_addr),
        .strm_wr_data_e2w_wsto              (strm_packet_e2w_wsto_int[i].wr.wr_data),
        .strm_rd_en_e2w_wsto                (strm_packet_e2w_wsto_int[i].rdrq.rd_en),
        .strm_rd_addr_e2w_wsto              (strm_packet_e2w_wsto_int[i].rdrq.rd_addr),
        .strm_rd_data_e2w_wsto              (strm_packet_e2w_wsto_int[i].rdrs.rd_data),
        .strm_rd_data_valid_e2w_wsto        (strm_packet_e2w_wsto_int[i].rdrs.rd_data_valid),
        
        // pc packet
        // .pc_rdrq_packet_sel_e2w_esti        (pc_packet_e2w_esti_int[i].rdrq.packet_sel),
        // .pc_rdrs_packet_sel_e2w_esti        (pc_packet_e2w_esti_int[i].rdrs.packet_sel),
        .pc_rd_en_e2w_esti                  (pc_packet_e2w_esti_int[i].rdrq.rd_en),
        .pc_rd_addr_e2w_esti                (pc_packet_e2w_esti_int[i].rdrq.rd_addr),
        .pc_rd_data_e2w_esti                (pc_packet_e2w_esti_int[i].rdrs.rd_data),
        .pc_rd_data_valid_e2w_esti          (pc_packet_e2w_esti_int[i].rdrs.rd_data_valid),

        // .pc_rdrq_packet_sel_w2e_esto        (pc_packet_w2e_esto_int[i].rdrq.packet_sel),
        // .pc_rdrs_packet_sel_w2e_esto        (pc_packet_w2e_esto_int[i].rdrs.packet_sel),
        .pc_rd_en_w2e_esto                  (pc_packet_w2e_esto_int[i].rdrq.rd_en),
        .pc_rd_addr_w2e_esto                (pc_packet_w2e_esto_int[i].rdrq.rd_addr),
        .pc_rd_data_w2e_esto                (pc_packet_w2e_esto_int[i].rdrs.rd_data),
        .pc_rd_data_valid_w2e_esto          (pc_packet_w2e_esto_int[i].rdrs.rd_data_valid),

        // .pc_rdrq_packet_sel_w2e_wsti        (pc_packet_w2e_wsti_int[i].rdrq.packet_sel),
        // .pc_rdrs_packet_sel_w2e_wsti        (pc_packet_w2e_wsti_int[i].rdrs.packet_sel),
        .pc_rd_en_w2e_wsti                  (pc_packet_w2e_wsti_int[i].rdrq.rd_en),
        .pc_rd_addr_w2e_wsti                (pc_packet_w2e_wsti_int[i].rdrq.rd_addr),
        .pc_rd_data_w2e_wsti                (pc_packet_w2e_wsti_int[i].rdrs.rd_data),
        .pc_rd_data_valid_w2e_wsti          (pc_packet_w2e_wsti_int[i].rdrs.rd_data_valid),

        // .pc_rdrq_packet_sel_e2w_wsto        (pc_packet_e2w_wsto_int[i].rdrq.packet_sel),
        // .pc_rdrs_packet_sel_e2w_wsto        (pc_packet_e2w_wsto_int[i].rdrs.packet_sel),
        .pc_rd_en_e2w_wsto                  (pc_packet_e2w_wsto_int[i].rdrq.rd_en),
        .pc_rd_addr_e2w_wsto                (pc_packet_e2w_wsto_int[i].rdrq.rd_addr),
        .pc_rd_data_e2w_wsto                (pc_packet_e2w_wsto_int[i].rdrs.rd_data),
        .pc_rd_data_valid_e2w_wsto          (pc_packet_e2w_wsto_int[i].rdrs.rd_data_valid),

        // stream data
        .stream_data_f2g                    (stream_data_f2g_int[i]),
        .stream_data_valid_f2g              (stream_data_valid_f2g_int[i]),
        .stream_data_g2f                    (stream_data_g2f_int[i]),
        .stream_data_valid_g2f              (stream_data_valid_g2f_int[i]),

        // trigger pulse
        .strm_start_pulse                   (strm_start_pulse_internal_d1[i]),
        .pc_start_pulse                     (pc_start_pulse_internal_d1[i]),

        // interrupt pulse
        .strm_f2g_interrupt_pulse           (strm_f2g_interrupt_pulse_internal[i]),
        .strm_g2f_interrupt_pulse           (strm_g2f_interrupt_pulse_internal[i]),
        .pcfg_g2f_interrupt_pulse           (pcfg_g2f_interrupt_pulse_internal[i]),
        .cgra_stall                         (cgra_stall[i]),

        // cgra cfg from glc
        .cgra_cfg_jtag_wsti_wr_en           (cgra_cfg_jtag_wsti_int[i].cfg_wr_en),
        .cgra_cfg_jtag_wsti_rd_en           (cgra_cfg_jtag_wsti_int[i].cfg_rd_en),
        .cgra_cfg_jtag_wsti_addr            (cgra_cfg_jtag_wsti_int[i].cfg_addr),
        .cgra_cfg_jtag_wsti_data            (cgra_cfg_jtag_wsti_int[i].cfg_data),

        .cgra_cfg_jtag_esto_wr_en           (cgra_cfg_jtag_esto_int[i].cfg_wr_en),
        .cgra_cfg_jtag_esto_rd_en           (cgra_cfg_jtag_esto_int[i].cfg_rd_en),
        .cgra_cfg_jtag_esto_addr            (cgra_cfg_jtag_esto_int[i].cfg_addr),
        .cgra_cfg_jtag_esto_data            (cgra_cfg_jtag_esto_int[i].cfg_data),

        .cgra_cfg_pc_wsti_wr_en             (cgra_cfg_pc_wsti_int[i].cfg_wr_en),
        .cgra_cfg_pc_wsti_rd_en             (cgra_cfg_pc_wsti_int[i].cfg_rd_en),
        .cgra_cfg_pc_wsti_addr              (cgra_cfg_pc_wsti_int[i].cfg_addr),
        .cgra_cfg_pc_wsti_data              (cgra_cfg_pc_wsti_int[i].cfg_data),

        .cgra_cfg_pc_esto_wr_en             (cgra_cfg_pc_esto_int[i].cfg_wr_en),
        .cgra_cfg_pc_esto_rd_en             (cgra_cfg_pc_esto_int[i].cfg_rd_en),
        .cgra_cfg_pc_esto_addr              (cgra_cfg_pc_esto_int[i].cfg_addr),
        .cgra_cfg_pc_esto_data              (cgra_cfg_pc_esto_int[i].cfg_data),

        // cgra cfg to fabric
        .cgra_cfg_g2f_cfg_wr_en             (cgra_cfg_g2f_cfg_wr_en[i]),
        .cgra_cfg_g2f_cfg_rd_en             (cgra_cfg_g2f_cfg_rd_en[i]),
        .cgra_cfg_g2f_cfg_addr              (cgra_cfg_g2f_cfg_addr[i]),
        .cgra_cfg_g2f_cfg_data              (cgra_cfg_g2f_cfg_data[i]),

        // glb cfg
        .if_cfg_est_m_wr_en                 (if_cfg_t2t[i+1].wr_en),
        .if_cfg_est_m_wr_clk_en             (if_cfg_t2t[i+1].wr_clk_en),
        .if_cfg_est_m_wr_addr               (if_cfg_t2t[i+1].wr_addr),
        .if_cfg_est_m_wr_data               (if_cfg_t2t[i+1].wr_data),
        .if_cfg_est_m_rd_en                 (if_cfg_t2t[i+1].rd_en),
        .if_cfg_est_m_rd_clk_en             (if_cfg_t2t[i+1].rd_clk_en),
        .if_cfg_est_m_rd_addr               (if_cfg_t2t[i+1].rd_addr),
        .if_cfg_est_m_rd_data               (if_cfg_t2t[i+1].rd_data),
        .if_cfg_est_m_rd_data_valid         (if_cfg_t2t[i+1].rd_data_valid),

        .if_cfg_wst_s_wr_en                 (if_cfg_t2t[i].wr_en),
        .if_cfg_wst_s_wr_clk_en             (if_cfg_t2t[i].wr_clk_en),
        .if_cfg_wst_s_wr_addr               (if_cfg_t2t[i].wr_addr),
        .if_cfg_wst_s_wr_data               (if_cfg_t2t[i].wr_data),
        .if_cfg_wst_s_rd_en                 (if_cfg_t2t[i].rd_en),
        .if_cfg_wst_s_rd_clk_en             (if_cfg_t2t[i].rd_clk_en),
        .if_cfg_wst_s_rd_addr               (if_cfg_t2t[i].rd_addr),
        .if_cfg_wst_s_rd_data               (if_cfg_t2t[i].rd_data),
        .if_cfg_wst_s_rd_data_valid         (if_cfg_t2t[i].rd_data_valid),

        .cfg_tile_connected_wsti            (cfg_tile_connected_internal[i]),
        .cfg_tile_connected_esto            (cfg_tile_connected_internal[i+1]),
        .cfg_pc_tile_connected_wsti         (cfg_pc_tile_connected_internal[i]),
        .cfg_pc_tile_connected_esto         (cfg_pc_tile_connected_internal[i+1]),

        // sram cfg
        .if_sram_cfg_est_m_wr_en            (if_sram_cfg_t2t[i+1].wr_en),
        .if_sram_cfg_est_m_wr_clk_en        (if_sram_cfg_t2t[i+1].wr_clk_en),
        .if_sram_cfg_est_m_wr_addr          (if_sram_cfg_t2t[i+1].wr_addr),
        .if_sram_cfg_est_m_wr_data          (if_sram_cfg_t2t[i+1].wr_data),
        .if_sram_cfg_est_m_rd_en            (if_sram_cfg_t2t[i+1].rd_en),
        .if_sram_cfg_est_m_rd_clk_en        (if_sram_cfg_t2t[i+1].rd_clk_en),
        .if_sram_cfg_est_m_rd_addr          (if_sram_cfg_t2t[i+1].rd_addr),
        .if_sram_cfg_est_m_rd_data          (if_sram_cfg_t2t[i+1].rd_data),
        .if_sram_cfg_est_m_rd_data_valid    (if_sram_cfg_t2t[i+1].rd_data_valid),

        .if_sram_cfg_wst_s_wr_en            (if_sram_cfg_t2t[i].wr_en),
        .if_sram_cfg_wst_s_wr_clk_en        (if_sram_cfg_t2t[i].wr_clk_en),
        .if_sram_cfg_wst_s_wr_addr          (if_sram_cfg_t2t[i].wr_addr),
        .if_sram_cfg_wst_s_wr_data          (if_sram_cfg_t2t[i].wr_data),
        .if_sram_cfg_wst_s_rd_en            (if_sram_cfg_t2t[i].rd_en),
        .if_sram_cfg_wst_s_rd_clk_en        (if_sram_cfg_t2t[i].rd_clk_en),
        .if_sram_cfg_wst_s_rd_addr          (if_sram_cfg_t2t[i].rd_addr),
        .if_sram_cfg_wst_s_rd_data          (if_sram_cfg_t2t[i].rd_data),
        .if_sram_cfg_wst_s_rd_data_valid    (if_sram_cfg_t2t[i].rd_data_valid),

        // soft reset
        .cgra_soft_reset                    (cgra_soft_reset_internal_d1),
        .*);
end: glb_tile_gen
endgenerate

endmodule
