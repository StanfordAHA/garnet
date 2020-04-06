/*=============================================================================
** Module: glb_tile_cfg_ctrl.sv
** Description:
**              Global Buffer Tile Config and Pio Interface
** Author: Taeyoung Kong
** Change history: 04/05/2020
**  - Implement first version of control logic
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile_cfg_ctrl (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // Config
    cfg_ifc.slave                           if_cfg_wst_s,
    cfg_ifc.master                          if_cfg_est_m,

    output logic [AXI_DATA_WIDTH-1:0]       leaf_dec_wr_data,
    output logic [AXI_ADDR_WIDTH-1:0]       leaf_dec_addr,
    output logic                            leaf_dec_block_sel,
    output logic                            leaf_dec_valid,
    output logic                            leaf_dec_wr_dvld,
    output logic [1:0]                      leaf_dec_cycle,
    output logic [2:0]                      leaf_dec_wr_width, //unused

    input  logic [AXI_DATA_WIDTH-1:0]       dec_leaf_rd_data,
    input  logic                            dec_leaf_ack,
    input  logic                            dec_leaf_nack,
    input  logic                            dec_leaf_accept, //unused
    input  logic                            dec_leaf_reject, //unused
    input  logic                            dec_leaf_retry_atomic, //unused
    input  logic [2:0]                      dec_leaf_data_width //unused
);

//============================================================================//
// Internal logic defines
//============================================================================//
logic [AXI_DATA_WIDTH-1:0] wr_data_internal;
logic [AXI_ADDR_WIDTH-1:0] addr_internal;
logic block_sel_internal;
logic valid_internal;
logic wr_dvld_internal;
logic [1:0] cycle_internal;
logic rd_en_d1, rd_en_d2;
logic [AXI_DATA_WIDTH-1:0] rd_data_internal, rd_data_next;
logic rd_data_valid, rd_data_valid_next;
logic wr_tile_id_match;
logic rd_tile_id_match;

//============================================================================//
// assigns
//============================================================================//
assign leaf_dec_wr_data = wr_data_internal;
assign leaf_dec_addr = addr_internal;
assign leaf_dec_block_sel = block_sel_internal;
assign leaf_dec_valid = valid_internal;
assign leaf_dec_wr_dvld = wr_dvld_internal;
assign leaf_dec_cycle = cycle_internal;
assign leaf_dec_wr_width = '0;

//============================================================================//
// combinational logic
//============================================================================//
always_comb begin
    wr_tile_id_match = if_cfg_wst_s.wr_en & (glb_tile_id == if_cfg_wst_s.wr_addr[8 +: TILE_SEL_ADDR_WIDTH]);
    rd_tile_id_match = if_cfg_wst_s.rd_en & (glb_tile_id == if_cfg_wst_s.rd_addr[8 +: TILE_SEL_ADDR_WIDTH]);
end

always_comb begin
    wr_data_internal = '0;
    addr_internal = '0;
    block_sel_internal = 0;
    valid_internal = 0;
    wr_dvld_internal = 0;
    cycle_internal = 2'b00;
    if (if_cfg_wst_s.rd_en) begin
        wr_data_internal = '0;
        addr_internal = if_cfg_wst_s.rd_addr;
        block_sel_internal = (if_cfg_wst_s.rd_addr[8 +: TILE_SEL_ADDR_WIDTH] == glb_tile_id);
        valid_internal = 1;
        wr_dvld_internal = 0;
        cycle_internal = 2'b10;
    end
    else if (if_cfg_wst_s.wr_en) begin
        wr_data_internal = if_cfg_wst_s.wr_data;
        addr_internal = if_cfg_wst_s.wr_addr;
        block_sel_internal = (if_cfg_wst_s.wr_addr[8 +: TILE_SEL_ADDR_WIDTH] == glb_tile_id);
        valid_internal = 1;
        wr_dvld_internal = 1;
        cycle_internal = 2'b00;
    end
end

//============================================================================//
// control logic
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rd_en_d1 <= 0;
        rd_en_d2 <= 0;
    end
    else begin
        rd_en_d1 <= if_cfg_wst_s.rd_en;
        rd_en_d2 <= rd_en_d1;
    end
end

always_comb begin
    rd_data_valid_next = 0;
    rd_data_next = '0;
    if (rd_en_d2 & (dec_leaf_ack | dec_leaf_nack)) begin
        rd_data_valid_next = 1;
        rd_data_next = dec_leaf_rd_data;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rd_data_valid_internal <= 0;
        rd_data_internal <= '0;
    end
    else begin
        rd_data_valid_internal <= rd_data_valid_next;
        rd_data_internal <= rd_data_next;
    end
end

//============================================================================//
// Configuration Router and Pipeline
//============================================================================//
// west to east - wr
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_est_m.wr_en <= 0;
        if_cfg_est_m.wr_clk_en <= 0;
        if_cfg_est_m.wr_addr <= '0;
        if_cfg_est_m.wr_data <= '0;
    end
    // optional
    else if (if_cfg_wst_s.wr_clk_en)  begin
        if (if_cfg_wst_s.wr_en == 1'b1 && !wr_tile_id_match) begin
            if_cfg_est_m.wr_en <= if_cfg_wst_s.wr_en;
            if_cfg_est_m.wr_clk_en <= if_cfg_wst_s.wr_clk_en;
            if_cfg_est_m.wr_addr <= if_cfg_wst_s.wr_addr;
            if_cfg_est_m.wr_data <= if_cfg_wst_s.wr_data;
        end
        else begin
            if_cfg_est_m.wr_en <= 0;
            if_cfg_est_m.wr_clk_en <= 0;
            if_cfg_est_m.wr_addr <= '0;
            if_cfg_est_m.wr_data <= '0;
        end
    end
end

// west to east - rd
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_est_m.rd_en <= 0;
        if_cfg_est_m.rd_clk_en <= 0;
        if_cfg_est_m.rd_addr <= '0;
    end
    // optional
    else if (if_cfg_wst_s.rd_clk_en)  begin
        if (if_cfg_wst_s.rd_en == 1'b1 && !cfg_rd_tile_id_match) begin
            if_cfg_est_m.rd_en <= if_cfg_wst_s.rd_en;
            if_cfg_est_m.rd_clk_en <= if_cfg_wst_s.rd_clk_en;
            if_cfg_est_m.rd_addr <= if_cfg_wst_s.rd_addr;
        end
        else begin
            if_cfg_est_m.rd_en <= 0;
            if_cfg_est_m.rd_clk_en <= 0;
            if_cfg_est_m.rd_addr <= '0;
        end
    end
end

// east to west
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_wst_s.rd_data <= '0;
        if_cfg_wst_s.rd_data_valid <= 0;
    end
    else if (if_cfg_wst_s.rd_clk_en) begin
        if (rd_data_valid_internal) begin
            if_cfg_wst_s.rd_data <= rd_data_internal;
            if_cfg_wst_s.rd_data_valid <= rd_data_valid_internal;
        end
        else begin
            if_cfg_wst_s.rd_data <= if_cfg_est_m.rd_data;
            if_cfg_wst_s.rd_data_valid <= if_cfg_est_m.rd_data_valid;
        end
    end
end

endmodule
