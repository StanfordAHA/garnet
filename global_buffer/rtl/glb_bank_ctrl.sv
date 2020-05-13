/*=============================================================================
** Module: glb_bank_ctrl.sv
** Description:
**              bank controller coordinates host-cgra read/write.
**              host read/write has priority
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of bank controller
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_bank_ctrl  (
    input  logic                        clk,
    input  logic                        reset,

    // packet interface
    input  logic                        packet_wr_en,
    input  logic  [BANK_ADDR_WIDTH-1:0] packet_wr_addr,
    input  logic  [BANK_DATA_WIDTH-1:0] packet_wr_data,
    input  logic  [BANK_DATA_WIDTH-1:0] packet_wr_data_bit_sel,

    // input  packet_sel_t                 packet_rdrq_packet_sel,
    input  logic                        packet_rd_en,
    input  logic  [BANK_ADDR_WIDTH-1:0] packet_rd_addr,
    output logic  [BANK_DATA_WIDTH-1:0] packet_rd_data,
    output logic                        packet_rd_data_valid,
    // output packet_sel_t                 packet_rdrs_packet_sel,

    // interface with memory
    output logic                        mem_rd_en,
    output logic                        mem_wr_en,
    output logic  [BANK_ADDR_WIDTH-1:0] mem_addr,
    output logic  [BANK_DATA_WIDTH-1:0] mem_data_in,
    output logic  [BANK_DATA_WIDTH-1:0] mem_data_in_bit_sel,
    input  logic  [BANK_DATA_WIDTH-1:0] mem_data_out,

    // sram configuration
    cfg_ifc.slave                       if_sram_cfg
);

//===========================================================================//
// signal declaration
//===========================================================================//
// packet
logic                       packet_rd_en_d1, packet_rd_en_d2, packet_rd_en_d3;
// packet_sel_t                packet_rdrq_packet_sel_d1, packet_rdrq_packet_sel_d2;
logic [BANK_DATA_WIDTH-1:0] packet_rd_data_d1;

// sram cfg
logic                       cfg_rd_en_d1, cfg_rd_en_d2, cfg_rd_en_d3;
logic                       cfg_sram_rd_addr_mux_d1, cfg_sram_rd_addr_mux_d2, cfg_sram_rd_addr_mux_d3;
logic [BANK_DATA_WIDTH-1:0] cfg_sram_rd_data, cfg_sram_rd_data_d1;

// internal mem
logic                       internal_mem_rd_en, internal_mem_rd_en_d1, internal_mem_rd_en_d2, internal_mem_rd_en_d3;
logic                       internal_mem_wr_en;
logic [BANK_ADDR_WIDTH-1:0] internal_mem_addr;
logic [BANK_DATA_WIDTH-1:0] internal_mem_data_in;
logic [BANK_DATA_WIDTH-1:0] internal_mem_data_in_bit_sel;

//===========================================================================//
// output assignment
//===========================================================================//
assign mem_wr_en = internal_mem_wr_en;
assign mem_rd_en = internal_mem_rd_en;
assign mem_data_in_bit_sel = internal_mem_data_in_bit_sel;
assign mem_data_in = internal_mem_data_in;
assign mem_addr = internal_mem_addr;

//===========================================================================//
// Set mem_wr_en and mem_data_in output
//===========================================================================//
always_comb begin
    if (if_sram_cfg.wr_en) begin
        if (if_sram_cfg.wr_addr[BANK_BYTE_OFFSET-1] == 0) begin
            internal_mem_wr_en = 1;
            internal_mem_rd_en = 0;
            internal_mem_addr = if_sram_cfg.wr_addr;
            internal_mem_data_in = {{{BANK_DATA_WIDTH-CGRA_CFG_DATA_WIDTH}{1'b0}}, if_sram_cfg.wr_data};
            internal_mem_data_in_bit_sel = {{{BANK_DATA_WIDTH-CGRA_CFG_DATA_WIDTH}{1'b0}}, {CGRA_CFG_DATA_WIDTH{1'b1}}};
        end
        else begin
            internal_mem_wr_en = 1;
            internal_mem_rd_en = 0;
            internal_mem_addr = if_sram_cfg.wr_addr;
            internal_mem_data_in = {if_sram_cfg.wr_data, {{BANK_DATA_WIDTH-CGRA_CFG_DATA_WIDTH}{1'b0}}};
            internal_mem_data_in_bit_sel = {{CGRA_CFG_DATA_WIDTH{1'b1}}, {{BANK_DATA_WIDTH-CGRA_CFG_DATA_WIDTH}{1'b0}}};
        end
    end
    else if (if_sram_cfg.rd_en) begin
        internal_mem_wr_en = 0;
        internal_mem_rd_en = 1;
        internal_mem_addr = if_sram_cfg.rd_addr;
        internal_mem_data_in = 0;
        internal_mem_data_in_bit_sel = 0;
    end
    else if (packet_wr_en) begin
        internal_mem_wr_en = 1;
        internal_mem_data_in_bit_sel = packet_wr_data_bit_sel;
        internal_mem_rd_en = 0;
        internal_mem_data_in = packet_wr_data;
        internal_mem_addr = packet_wr_addr;
    end
    else if (packet_rd_en) begin
        internal_mem_wr_en = 0;
        internal_mem_data_in_bit_sel = {BANK_DATA_WIDTH{1'b0}};
        internal_mem_rd_en = 1;
        internal_mem_data_in = 0;
        internal_mem_addr = packet_rd_addr;
    end
    else begin
        internal_mem_wr_en = 0;
        internal_mem_data_in_bit_sel = {BANK_DATA_WIDTH{1'b0}};
        internal_mem_rd_en = 0;
        internal_mem_data_in = 0;
        internal_mem_addr = 0;
    end
end


//===========================================================================//
// packet assignment
//===========================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        internal_mem_rd_en_d1 <= 0;
        internal_mem_rd_en_d2 <= 0;
        internal_mem_rd_en_d3 <= 0;
        cfg_rd_en_d1 <= 0;
        cfg_rd_en_d2 <= 0;
        cfg_rd_en_d3 <= 0;
        packet_rd_en_d1 <= 0;
        packet_rd_en_d2 <= 0;
        packet_rd_en_d3 <= 0;
        // packet_rdrq_packet_sel_d1 <= '0;
        // packet_rdrq_packet_sel_d2 <= '0;
    end
    else begin
        internal_mem_rd_en_d1 <= internal_mem_rd_en;
        internal_mem_rd_en_d2 <= internal_mem_rd_en_d1;
        internal_mem_rd_en_d3 <= internal_mem_rd_en_d2;
        cfg_rd_en_d1 <= if_sram_cfg.rd_en;
        cfg_rd_en_d2 <= cfg_rd_en_d1;
        cfg_rd_en_d3 <= cfg_rd_en_d2;
        packet_rd_en_d1 <= packet_rd_en;
        packet_rd_en_d2 <= packet_rd_en_d1;
        packet_rd_en_d3 <= packet_rd_en_d2;
        // packet_rdrq_packet_sel_d1 <= packet_rdrq_packet_sel;
        // packet_rdrq_packet_sel_d2 <= packet_rdrq_packet_sel_d1;
    end
end

// output data latch
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        packet_rd_data_d1 <= 0;
    end
    else begin
        packet_rd_data_d1 <= packet_rd_data;
    end
end

// just assumes proc/cfg/packet do not write at the same time
assign packet_rd_data = packet_rd_en_d3 ? mem_data_out : packet_rd_data_d1;
assign packet_rd_data_valid = packet_rd_en_d3;
// assign packet_rdrs_packet_sel = packet_rdrq_packet_sel_d2;

//===========================================================================//
// config output assignment
//===========================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cfg_sram_rd_addr_mux_d1 <= 0;
        cfg_sram_rd_addr_mux_d2 <= 0;
        cfg_sram_rd_addr_mux_d3 <= 0;
    end
    else begin
        cfg_sram_rd_addr_mux_d1 <= if_sram_cfg.rd_addr[BANK_BYTE_OFFSET-1];
        cfg_sram_rd_addr_mux_d2 <= cfg_sram_rd_addr_mux_d1;
        cfg_sram_rd_addr_mux_d3 <= cfg_sram_rd_addr_mux_d2;
    end
end

// output config data latch
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cfg_sram_rd_data_d1 <= 0;
    end
    else begin
        cfg_sram_rd_data_d1 <= if_sram_cfg.rd_data;
    end
end


assign if_sram_cfg.rd_data = cfg_rd_en_d3 ? (cfg_sram_rd_addr_mux_d3 == 0 ? mem_data_out[0 +: CGRA_CFG_DATA_WIDTH] : mem_data_out[CGRA_CFG_DATA_WIDTH +: CGRA_CFG_DATA_WIDTH]) : cfg_sram_rd_data_d1;

assign if_sram_cfg.rd_data_valid = internal_mem_rd_en_d3 & cfg_rd_en_d3;

endmodule
