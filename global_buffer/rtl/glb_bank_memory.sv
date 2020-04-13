/*=============================================================================
** Module: glb_memory_core.sv
** Description:
**              glb memory core
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of memory core
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_bank_memory (
    input  logic                        clk,
    input  logic                        reset,

    input  logic                        ren,
    input  logic                        wen,
    input  logic [BANK_ADDR_WIDTH-1:0]  addr,
    input  logic [BANK_DATA_WIDTH-1:0]  data_in,
    input  logic [BANK_DATA_WIDTH-1:0]  data_in_bit_sel,
    output logic [BANK_DATA_WIDTH-1:0]  data_out,

    // sram configuration
    cfg_ifc.slave                       if_sram_cfg
);

//===========================================================================//
// memory-SRAM interface signal declaration
//===========================================================================//
logic                                           sram_cen;
logic                                           sram_wen;
logic                                           sram_ren;
logic [BANK_ADDR_WIDTH-BANK_BYTE_OFFSET-1:0]    sram_addr;
logic [BANK_DATA_WIDTH-1:0]                     sram_data_in;
logic [BANK_DATA_WIDTH-1:0]                     sram_bit_sel;
logic [BANK_DATA_WIDTH-1:0]                     sram_data_out;
logic                                           sram_ren_d1;
logic [BANK_DATA_WIDTH-1:0]                     data_out_d1;

//===========================================================================//
// memory instantiation
//===========================================================================//
glb_bank_sram_gen #(
    .DATA_WIDTH(BANK_DATA_WIDTH),
    .ADDR_WIDTH(BANK_ADDR_WIDTH-BANK_BYTE_OFFSET)
) glb_bank_sram_gen (
    .CLK(clk),
    .CEB(~sram_cen),
    .WEB(~sram_wen),
    .A(sram_addr),
    .D(sram_data_in),
    .BWEB(~sram_bit_sel),
    .Q(sram_data_out)
);

//===========================================================================//
// sram control logic
//===========================================================================//
always_comb begin
    if (if_sram_cfg.wr_en && if_sram_cfg.wr_clk_en) begin
        if (if_sram_cfg.wr_addr[BANK_BYTE_OFFSET-1] == 0) begin
            sram_wen = 1;
            sram_ren = 0;
            sram_cen = 1;
            sram_addr = if_sram_cfg.wr_addr[BANK_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_BYTE_OFFSET];
            sram_data_in = {{{BANK_DATA_WIDTH-CGRA_CFG_DATA_WIDTH}{1'b0}}, if_sram_cfg.wr_data};
            sram_bit_sel = {{{BANK_DATA_WIDTH-CGRA_CFG_DATA_WIDTH}{1'b0}}, {CGRA_CFG_DATA_WIDTH{1'b1}}};
        end
        else begin
            sram_wen = 1;
            sram_ren = 0;
            sram_cen = 1;
            sram_addr = if_sram_cfg.wr_addr[BANK_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_BYTE_OFFSET];
            sram_data_in = {{{BANK_DATA_WIDTH-CGRA_CFG_DATA_WIDTH}{1'b0}}, if_sram_cfg.wr_data};
            sram_bit_sel = {{{BANK_DATA_WIDTH-CGRA_CFG_DATA_WIDTH}{1'b0}}, {CGRA_CFG_DATA_WIDTH{1'b1}}};
        end
    end
    else if (if_sram_cfg.rd_en && if_sram_cfg.rd_clk_en) begin
        sram_wen = 0;
        sram_ren = 1;
        sram_cen = 1;
        sram_addr = if_sram_cfg.rd_addr[BANK_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_BYTE_OFFSET];
        sram_data_in = 0;
        sram_bit_sel = 0;
    end
    else begin
        sram_wen = wen;
        sram_ren = ren;
        sram_cen = wen | ren;
        sram_addr = addr[BANK_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_BYTE_OFFSET];
        sram_data_in = data_in;
        sram_bit_sel = data_in_bit_sel;
    end
end

//===========================================================================//
// output assignment
//===========================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        sram_ren_d1 <= 0;
        data_out_d1 <= 0;
    end
    else begin
        sram_ren_d1 <= sram_ren;
        data_out_d1 <= data_out;
    end
end
assign data_out = sram_ren_d1 ? sram_data_out : data_out_d1;

//===========================================================================//
// config output assignment
//===========================================================================//
logic cfg_sram_rd_en_d1;
logic cfg_sram_rd_addr_mux_d1;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cfg_sram_rd_en_d1 <= 0;
        cfg_sram_rd_addr_mux_d1 <= 0;
    end
    else begin
        cfg_sram_rd_en_d1 <= if_sram_cfg.rd_en && if_sram_cfg.rd_clk_en;
        cfg_sram_rd_addr_mux_d1 <= if_sram_cfg.rd_addr[BANK_BYTE_OFFSET-1];
    end
end

always_comb begin
    if (cfg_sram_rd_en_d1 == 1) begin
        if (cfg_sram_rd_addr_mux_d1 == 0) begin
            if_sram_cfg.rd_data = sram_data_out[0 +: CGRA_CFG_DATA_WIDTH];
        end
        else begin
            if_sram_cfg.rd_data = sram_data_out[CGRA_CFG_DATA_WIDTH +: CGRA_CFG_DATA_WIDTH];
        end
    end
    else begin
        if_sram_cfg.rd_data = data_out_d1;
    end
end
assign if_sram_cfg.rd_data_valid = cfg_sram_rd_en_d1;

endmodule
