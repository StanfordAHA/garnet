/*=============================================================================
** Module: glb_dummy_start.sv
** Description:
**              Global Buffer Tile Dummy Start
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_dummy_start (
    // proc
    input  logic                            proc2glb_wr_en,
    input  logic [BANK_DATA_WIDTH/8-1:0]    proc2glb_wr_strb,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc2glb_wr_addr,
    input  logic [BANK_DATA_WIDTH-1:0]      proc2glb_wr_data,
    input  logic                            proc2glb_rd_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       proc2glb_rd_addr,
    output logic [BANK_DATA_WIDTH-1:0]      glb2proc_rd_data,

    // configuration of glb from glc
    input  logic                            glb_cfg_wr_en,
    input  logic                            glb_cfg_wr_clk_en,
    input  logic [AXI_ADDR_WIDTH-1:0]       glb_cfg_wr_addr,
    input  logic [AXI_DATA_WIDTH-1:0]       glb_cfg_wr_data,
    input  logic                            glb_cfg_rd_en,
    input  logic                            glb_cfg_rd_clk_en,
    input  logic [AXI_ADDR_WIDTH-1:0]       glb_cfg_rd_addr,
    output logic [AXI_DATA_WIDTH-1:0]       glb_cfg_rd_data,
    output logic                            glb_cfg_rd_data_valid,
    cfg_ifc.master                          if_cfg_est_m,

    // configuration of sram from glc
    input  logic                            sram_cfg_wr_en,
    input  logic                            sram_cfg_wr_clk_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       sram_cfg_wr_addr,
    input  logic [CGRA_CFG_DATA_WIDTH-1:0]  sram_cfg_wr_data,
    input  logic                            sram_cfg_rd_en,
    input  logic                            sram_cfg_rd_clk_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       sram_cfg_rd_addr,
    output logic [CGRA_CFG_DATA_WIDTH-1:0]  sram_cfg_rd_data,
    output logic                            sram_cfg_rd_data_valid,
    cfg_ifc.master                          if_sram_cfg_est_m,

    // processor packet
    input  packet_t                         proc_packet_e2w_esti,
    output packet_t                         proc_packet_w2e_esto,

    // strm packet dummy
    output packet_t                         strm_packet_w2e_esto
);

//============================================================================//
// Packetize processor data
//============================================================================//
assign proc_packet_w2e_esto.wr.wr_en = proc2glb_wr_en;
assign proc_packet_w2e_esto.wr.wr_strb = proc2glb_wr_strb;
assign proc_packet_w2e_esto.wr.wr_addr = proc2glb_wr_addr;
assign proc_packet_w2e_esto.wr.wr_data = proc2glb_wr_data;
assign proc_packet_w2e_esto.rdrq.rd_en = proc2glb_rd_en;
assign proc_packet_w2e_esto.rdrq.rd_addr = proc2glb_rd_addr;
assign glb2proc_rd_data = proc_packet_e2w_esti.rdrs.rd_data;
// just wire to 0
assign proc_packet_w2e_esto.rdrs.rd_data = '0;

//============================================================================//
// Strm packet dummy
//============================================================================//
assign strm_packet_w2e_esto = '0;

//============================================================================//
// configuration connect
//============================================================================//
assign if_cfg_est_m.wr_en       = glb_cfg_wr_en;
assign if_cfg_est_m.wr_clk_en   = glb_cfg_wr_clk_en;
assign if_cfg_est_m.wr_addr     = glb_cfg_wr_addr;
assign if_cfg_est_m.wr_data     = glb_cfg_wr_data;
assign if_cfg_est_m.rd_en       = glb_cfg_rd_en;
assign if_cfg_est_m.rd_clk_en   = glb_cfg_rd_clk_en;
assign if_cfg_est_m.rd_addr     = glb_cfg_rd_addr;

assign glb_cfg_rd_data          = if_cfg_est_m.rd_data;
assign glb_cfg_rd_data_valid    = if_cfg_est_m.rd_data_valid;

//============================================================================//
// sram configuration connect
//============================================================================//
assign if_sram_cfg_est_m.wr_en      = sram_cfg_wr_en;
assign if_sram_cfg_est_m.wr_clk_en  = sram_cfg_wr_clk_en;
assign if_sram_cfg_est_m.wr_addr    = sram_cfg_wr_addr;
assign if_sram_cfg_est_m.wr_data    = sram_cfg_wr_data;
assign if_sram_cfg_est_m.rd_en      = sram_cfg_rd_en;
assign if_sram_cfg_est_m.rd_clk_en  = sram_cfg_rd_clk_en;
assign if_sram_cfg_est_m.rd_addr    = sram_cfg_rd_addr;

assign sram_cfg_rd_data             = if_sram_cfg_est_m.rd_data;
assign sram_cfg_rd_data_valid       = if_sram_cfg_est_m.rd_data_valid;

endmodule
