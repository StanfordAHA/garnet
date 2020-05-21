/*=============================================================================
** Module: glb_core_sram_cfg_ctrl.sv
** Description:
**              Controller of jtag config for sram
** Author: Taeyoung Kong
** Change history:
**      03/14/2020
**          - Implement first version of memory core
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_core_sram_cfg_ctrl (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // SRAM Config
    cfg_ifc.master                          if_sram_cfg_est_m,
    cfg_ifc.slave                           if_sram_cfg_wst_s,

    cfg_ifc.master                          if_sram_cfg_bank [0:BANKS_PER_TILE-1]
);

//============================================================================//
// Internal logic
//============================================================================//
logic                           if_sram_cfg_bank_rd_en [BANKS_PER_TILE];
logic                           if_sram_cfg_bank_rd_en_d1 [BANKS_PER_TILE];
logic                           if_sram_cfg_bank_rd_en_d2 [BANKS_PER_TILE];
logic [CGRA_CFG_DATA_WIDTH-1:0] rd_data_next;
logic                           rd_data_valid_next;
logic [CGRA_CFG_DATA_WIDTH-1:0] bank_rd_data_internal [BANKS_PER_TILE];
logic                           bank_rd_data_valid_internal [BANKS_PER_TILE];

//============================================================================//
// Control logic
//============================================================================//
generate
for (genvar i=0; i<BANKS_PER_TILE; i=i+1) begin
    assign if_sram_cfg_bank[i].wr_en = ((if_sram_cfg_wst_s.wr_addr[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH] == i)
                                        & (if_sram_cfg_wst_s.wr_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id))
                                        ? if_sram_cfg_wst_s.wr_en : 0;
    // assign if_sram_cfg_bank[i].wr_clk_en = if_sram_cfg_wst_s.wr_clk_en;
    assign if_sram_cfg_bank[i].wr_clk_en = 1;
    assign if_sram_cfg_bank[i].wr_addr =  if_sram_cfg_wst_s.wr_addr[0 +: BANK_ADDR_WIDTH];
    assign if_sram_cfg_bank[i].wr_data = if_sram_cfg_wst_s.wr_data;
    assign if_sram_cfg_bank[i].rd_en = ((if_sram_cfg_wst_s.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id)
                                        & (if_sram_cfg_wst_s.rd_addr[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH] == i))
                                        ? if_sram_cfg_wst_s.rd_en : 0;
    // assign if_sram_cfg_bank[i].rd_clk_en = if_sram_cfg_wst_s.rd_clk_en;
    assign if_sram_cfg_bank[i].rd_clk_en = 1;
    assign if_sram_cfg_bank[i].rd_addr = if_sram_cfg_wst_s.rd_addr[0 +: BANK_ADDR_WIDTH];
    assign bank_rd_data_valid_internal[i] = if_sram_cfg_bank[i].rd_data_valid;
    assign bank_rd_data_internal[i] = if_sram_cfg_bank[i].rd_data;
end
endgenerate

always_comb begin
    for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
        if_sram_cfg_bank_rd_en[i]  = ((if_sram_cfg_wst_s.rd_addr[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH] == glb_tile_id)
                                        & (if_sram_cfg_wst_s.rd_addr[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH] == i))
                                        ? if_sram_cfg_wst_s.rd_en : 0;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
            if_sram_cfg_bank_rd_en_d1[i] <= 0;
            if_sram_cfg_bank_rd_en_d2[i] <= 0;
        end
    end
    else begin
        for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
            if_sram_cfg_bank_rd_en_d1[i] <= if_sram_cfg_bank_rd_en[i];
            if_sram_cfg_bank_rd_en_d2[i] <= if_sram_cfg_bank_rd_en_d1[i];
        end
    end
end

always_comb begin
    rd_data_next = if_sram_cfg_est_m.rd_data;
    rd_data_valid_next = if_sram_cfg_est_m.rd_data_valid;
    for (int i=0; i<BANKS_PER_TILE; i=i+1) begin
        // fixed latency of 2 cycle
        if (if_sram_cfg_bank_rd_en_d2[i] == 1) begin
            rd_data_next = bank_rd_data_internal[i];
            rd_data_valid_next = bank_rd_data_valid_internal[i];
        end
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_sram_cfg_est_m.wr_en <= 0;
        // if_sram_cfg_est_m.wr_clk_en <= 0;
        if_sram_cfg_est_m.wr_addr <= 0;
        if_sram_cfg_est_m.wr_data <= 0;
        if_sram_cfg_est_m.rd_en <= 0;
        // if_sram_cfg_est_m.rd_clk_en <= 0;
        if_sram_cfg_est_m.rd_addr <= 0;
        if_sram_cfg_wst_s.rd_data <= 0;
        if_sram_cfg_wst_s.rd_data_valid <= 0;
    end
    else begin
        if_sram_cfg_est_m.wr_en <= if_sram_cfg_wst_s.wr_en;
        // if_sram_cfg_est_m.wr_clk_en <= if_sram_cfg_wst_s.wr_clk_en;
        if_sram_cfg_est_m.wr_addr <= if_sram_cfg_wst_s.wr_addr;
        if_sram_cfg_est_m.wr_data <= if_sram_cfg_wst_s.wr_data;
        if_sram_cfg_est_m.rd_en <= if_sram_cfg_wst_s.rd_en;
        // if_sram_cfg_est_m.rd_clk_en <= if_sram_cfg_wst_s.rd_clk_en;
        if_sram_cfg_est_m.rd_addr <= if_sram_cfg_wst_s.rd_addr;
        if_sram_cfg_wst_s.rd_data <= rd_data_next;
        if_sram_cfg_wst_s.rd_data_valid <= rd_data_valid_next;
    end
end
assign if_sram_cfg_est_m.wr_clk_en = 1;
assign if_sram_cfg_est_m.rd_clk_en = 1;

endmodule
