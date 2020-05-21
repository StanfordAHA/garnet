/*=============================================================================
** Module: glb_dummy_start.sv
** Description:
**              Global Buffer Tile Dummy Start
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_dummy_start (
    input  logic                            clk,
    input  logic                            reset,

    // proc
    input  logic                            proc_wr_en,
    input  logic [BANK_DATA_WIDTH/8-1:0]    proc_wr_strb,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc_wr_addr,
    input  logic [BANK_DATA_WIDTH-1:0]      proc_wr_data,
    input  logic                            proc_rd_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc_rd_addr,
    output logic [BANK_DATA_WIDTH-1:0]      proc_rd_data,
    output logic                            proc_rd_data_valid,

    // configuration of glb from glc
    input  logic                            if_cfg_wr_en,
    input  logic                            if_cfg_wr_clk_en,
    input  logic [AXI_ADDR_WIDTH-1:0]       if_cfg_wr_addr,
    input  logic [AXI_DATA_WIDTH-1:0]       if_cfg_wr_data,
    input  logic                            if_cfg_rd_en,
    input  logic                            if_cfg_rd_clk_en,
    input  logic [AXI_ADDR_WIDTH-1:0]       if_cfg_rd_addr,
    output logic [AXI_DATA_WIDTH-1:0]       if_cfg_rd_data,
    output logic                            if_cfg_rd_data_valid,
    cfg_ifc.master                          if_cfg_est_m,

    // configuration of sram from glc
    input  logic                            if_sram_cfg_wr_en,
    input  logic                            if_sram_cfg_wr_clk_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       if_sram_cfg_wr_addr,
    input  logic [CGRA_CFG_DATA_WIDTH-1:0]  if_sram_cfg_wr_data,
    input  logic                            if_sram_cfg_rd_en,
    input  logic                            if_sram_cfg_rd_clk_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       if_sram_cfg_rd_addr,
    output logic [CGRA_CFG_DATA_WIDTH-1:0]  if_sram_cfg_rd_data,
    output logic                            if_sram_cfg_rd_data_valid,
    cfg_ifc.master                          if_sram_cfg_est_m,

    // processor packet
    input  packet_t                         proc_packet_e2w_esti,
    output packet_t                         proc_packet_w2e_esto,

    // strm packet dummy
    output packet_t                         strm_packet_w2e_esto,

    // oc packet dummy
    output rd_packet_t                      pc_packet_w2e_esto
);

//============================================================================//
// Packetize processor data
//============================================================================//
// assign proc_packet_w2e_esto.wr.packet_sel.packet_type = PSEL_PROC;
// assign proc_packet_w2e_esto.wr.packet_sel.src = '0;
// assign proc_packet_w2e_esto.rdrq.packet_sel.packet_type = PSEL_PROC;
// assign proc_packet_w2e_esto.rdrq.packet_sel.src = '0;
// just wire to 0
assign proc_packet_w2e_esto.rdrs = '0;
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        proc_packet_w2e_esto.wr.wr_en <= 0;
        proc_packet_w2e_esto.wr.wr_strb <= 0;
        proc_packet_w2e_esto.wr.wr_addr <= 0;
        proc_packet_w2e_esto.wr.wr_data <= 0;
        proc_packet_w2e_esto.rdrq.rd_en <= 0;
        proc_packet_w2e_esto.rdrq.rd_addr <= 0;
        proc_rd_data <= 0;
        proc_rd_data_valid <= 0;
    end
    else begin
        proc_packet_w2e_esto.wr.wr_en <= proc_wr_en;
        proc_packet_w2e_esto.wr.wr_strb <= proc_wr_strb;
        proc_packet_w2e_esto.wr.wr_addr <= proc_wr_addr;
        proc_packet_w2e_esto.wr.wr_data <= proc_wr_data;
        proc_packet_w2e_esto.rdrq.rd_en <= proc_rd_en;
        proc_packet_w2e_esto.rdrq.rd_addr <= proc_rd_addr;
        proc_rd_data <= proc_packet_e2w_esti.rdrs.rd_data;
        proc_rd_data_valid <= proc_packet_e2w_esti.rdrs.rd_data_valid;
    end
end

//============================================================================//
// Strm packet dummy
//============================================================================//
assign strm_packet_w2e_esto = '0;

//============================================================================//
// pc packet dummy
//============================================================================//
assign pc_packet_w2e_esto = '0;

//============================================================================//
// configuration connect
//============================================================================//
logic                      if_cfg_wr_en_internal_d1;
// logic                      if_cfg_wr_clk_en_internal_d1;
logic [AXI_ADDR_WIDTH-1:0] if_cfg_wr_addr_internal_d1;
logic [AXI_DATA_WIDTH-1:0] if_cfg_wr_data_internal_d1;
logic                      if_cfg_rd_en_internal_d1;
// logic                      if_cfg_rd_clk_en_internal_d1;
logic [AXI_ADDR_WIDTH-1:0] if_cfg_rd_addr_internal_d1;
logic [AXI_DATA_WIDTH-1:0] if_cfg_rd_data_internal_d1;
logic                      if_cfg_rd_data_valid_internal_d1;


always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_wr_en_internal_d1 <= 0;
        if_cfg_wr_addr_internal_d1 <= 0;
        if_cfg_wr_data_internal_d1 <= 0;
        if_cfg_rd_en_internal_d1 <= 0;
        if_cfg_rd_addr_internal_d1 <= 0;
        if_cfg_rd_data_internal_d1 <= 0;
        if_cfg_rd_data_valid_internal_d1 <= 0;
    end
    else begin
        if_cfg_wr_en_internal_d1 <= if_cfg_wr_en;
        if_cfg_wr_addr_internal_d1 <= if_cfg_wr_addr;
        if_cfg_wr_data_internal_d1 <= if_cfg_wr_data;
        if_cfg_rd_en_internal_d1 <= if_cfg_rd_en;
        if_cfg_rd_addr_internal_d1 <= if_cfg_rd_addr;
        if_cfg_rd_data_internal_d1 <= if_cfg_est_m.rd_data;
        if_cfg_rd_data_valid_internal_d1 <= if_cfg_est_m.rd_data_valid;
    end
end

// clk enable is negative edge sensitive
// always_ff @(negedge clk or posedge reset) begin
//     if (reset) begin
//         if_cfg_wr_clk_en_internal_d1 <= 0;
//         if_cfg_rd_clk_en_internal_d1 <= 0;
//     end
//     else begin
//         if_cfg_wr_clk_en_internal_d1 <= if_cfg_wr_clk_en;
//         if_cfg_rd_clk_en_internal_d1 <= if_cfg_rd_clk_en;
//     end
// end

assign if_cfg_est_m.wr_en       = if_cfg_wr_en_internal_d1;
assign if_cfg_est_m.wr_clk_en   = 1;
assign if_cfg_est_m.wr_addr     = if_cfg_wr_addr_internal_d1;
assign if_cfg_est_m.wr_data     = if_cfg_wr_data_internal_d1;
assign if_cfg_est_m.rd_en       = if_cfg_rd_en_internal_d1;
assign if_cfg_est_m.rd_clk_en   = 1;
assign if_cfg_est_m.rd_addr     = if_cfg_rd_addr_internal_d1;

assign if_cfg_rd_data           = if_cfg_rd_data_internal_d1;
assign if_cfg_rd_data_valid     = if_cfg_rd_data_valid_internal_d1;

//============================================================================//
// sram configuration connect
//============================================================================//
// configuration of sram from glc
logic                      if_sram_cfg_wr_en_internal_d1;
// logic                      if_sram_cfg_wr_clk_en_internal_d1;
logic [GLB_ADDR_WIDTH-1:0] if_sram_cfg_wr_addr_internal_d1;
logic [AXI_DATA_WIDTH-1:0] if_sram_cfg_wr_data_internal_d1;
logic                      if_sram_cfg_rd_en_internal_d1;
// logic                      if_sram_cfg_rd_clk_en_internal_d1;
logic [GLB_ADDR_WIDTH-1:0] if_sram_cfg_rd_addr_internal_d1;
logic [AXI_DATA_WIDTH-1:0] if_sram_cfg_rd_data_internal_d1;
logic                      if_sram_cfg_rd_data_valid_internal_d1;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_sram_cfg_wr_en_internal_d1 <= 0;
        if_sram_cfg_wr_addr_internal_d1 <= 0;
        if_sram_cfg_wr_data_internal_d1 <= 0;
        if_sram_cfg_rd_en_internal_d1 <= 0;
        if_sram_cfg_rd_addr_internal_d1 <= 0;
        if_sram_cfg_rd_data_internal_d1 <= 0;
        if_sram_cfg_rd_data_valid_internal_d1 <= 0;
    end
    else begin
        if_sram_cfg_wr_en_internal_d1 <= if_sram_cfg_wr_en;
        if_sram_cfg_wr_addr_internal_d1 <= if_sram_cfg_wr_addr;
        if_sram_cfg_wr_data_internal_d1 <= if_sram_cfg_wr_data;
        if_sram_cfg_rd_en_internal_d1 <= if_sram_cfg_rd_en;
        if_sram_cfg_rd_addr_internal_d1 <= if_sram_cfg_rd_addr;
        if_sram_cfg_rd_data_internal_d1 <= if_sram_cfg_est_m.rd_data;
        if_sram_cfg_rd_data_valid_internal_d1 <= if_sram_cfg_est_m.rd_data_valid;
    end
end

// clk enable is negative edge sensitive
// always_ff @(negedge clk or posedge reset) begin
//     if (reset) begin
//         if_sram_cfg_wr_clk_en_internal_d1 <= 0;
//         if_sram_cfg_rd_clk_en_internal_d1 <= 0;
//     end
//     else begin
//         if_sram_cfg_wr_clk_en_internal_d1 <= if_sram_cfg_wr_clk_en;
//         if_sram_cfg_rd_clk_en_internal_d1 <= if_sram_cfg_rd_clk_en;
//     end
// end

assign if_sram_cfg_est_m.wr_en       = if_sram_cfg_wr_en_internal_d1;
assign if_sram_cfg_est_m.wr_clk_en   = 1;
assign if_sram_cfg_est_m.wr_addr     = if_sram_cfg_wr_addr_internal_d1;
assign if_sram_cfg_est_m.wr_data     = if_sram_cfg_wr_data_internal_d1;
assign if_sram_cfg_est_m.rd_en       = if_sram_cfg_rd_en_internal_d1;
assign if_sram_cfg_est_m.rd_clk_en   = 1;
assign if_sram_cfg_est_m.rd_addr     = if_sram_cfg_rd_addr_internal_d1;

assign if_sram_cfg_rd_data           = if_sram_cfg_rd_data_internal_d1;
assign if_sram_cfg_rd_data_valid     = if_sram_cfg_rd_data_valid_internal_d1;

endmodule
