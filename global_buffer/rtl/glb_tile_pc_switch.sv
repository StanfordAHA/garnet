/*=============================================================================
** Module: glb_tile_pc_switch.sv
** Description:
**              Global Buffer Tile Parallel Configuration Controller
** Author: Taeyoung Kong
** Change history: 03/02/2020 - Implement first version of global buffer tile
**===========================================================================*/

module glb_tile_pc_switch
import global_buffer_pkg::*;
import global_buffer_param::*;
(
    input  logic                            clk,
    input  logic                            reset,

    // parallel config ctrl on
    input  logic                            cfg_pc_dma_mode,

    // parallel configuration
    input  cgra_cfg_t                       cgra_cfg_c2sw,
    input  cgra_cfg_t                       cgra_cfg_jtag_wsti,
    output cgra_cfg_t                       cgra_cfg_jtag_esto,
    input  cgra_cfg_t                       cgra_cfg_pc_wsti,
    output cgra_cfg_t                       cgra_cfg_pc_esto,
    output cgra_cfg_t                       cgra_cfg_g2f [CGRA_PER_GLB],

    // cgra_cfg_jtag_addr bypass
    input  logic                            cgra_cfg_jtag_wsti_rd_en_bypass,
    input  logic [CGRA_CFG_ADDR_WIDTH-1:0]  cgra_cfg_jtag_wsti_addr_bypass,
    output logic                            cgra_cfg_jtag_esto_rd_en_bypass,
    output logic [CGRA_CFG_ADDR_WIDTH-1:0]  cgra_cfg_jtag_esto_addr_bypass
);

//============================================================================//
// Simple router
//============================================================================//
cgra_cfg_t cgra_cfg_g2f_internal_d1 [CGRA_PER_GLB];
cgra_cfg_t cgra_cfg_g2f_internal [CGRA_PER_GLB];
cgra_cfg_t cgra_cfg_pc_switched;
assign cgra_cfg_pc_switched = (cfg_pc_dma_mode == 1) ? cgra_cfg_c2sw : cgra_cfg_pc_wsti;

// just bypass configuration packet
always_comb begin
    cgra_cfg_jtag_esto_rd_en_bypass = cgra_cfg_jtag_wsti_rd_en_bypass;
    cgra_cfg_jtag_esto_addr_bypass = cgra_cfg_jtag_wsti_addr_bypass;
end

//============================================================================//
// pipeline registers for configuration write
//============================================================================//
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        cgra_cfg_jtag_esto <= '0;
        cgra_cfg_pc_esto <= '0;
    end
    else begin
        cgra_cfg_jtag_esto <= cgra_cfg_jtag_wsti;
        cgra_cfg_pc_esto <= cgra_cfg_pc_switched;
    end
end

//============================================================================//
// output assignment
//============================================================================//
always_comb begin
    for (int i=0; i<CGRA_PER_GLB; i=i+1) begin
        if (cgra_cfg_jtag_esto_rd_en_bypass) begin
            cgra_cfg_g2f_internal[i].cfg_addr = cgra_cfg_jtag_esto_addr_bypass;
            cgra_cfg_g2f_internal[i].cfg_rd_en = 1'b1;
            cgra_cfg_g2f_internal[i].cfg_wr_en = 1'b0;
            cgra_cfg_g2f_internal[i].cfg_data = '0;
        end
        else begin
            cgra_cfg_g2f_internal[i] = cgra_cfg_jtag_esto | cgra_cfg_pc_esto;
        end
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (int i=0; i<CGRA_PER_GLB; i=i+1) begin
            cgra_cfg_g2f_internal_d1[i] <= 0;
        end
    end
    else begin
        for (int i=0; i<CGRA_PER_GLB; i=i+1) begin
            cgra_cfg_g2f_internal_d1[i] <= cgra_cfg_g2f_internal[i];
        end
    end
end

always_comb begin
    for (int i=0; i<CGRA_PER_GLB; i=i+1) begin
        cgra_cfg_g2f[i] = cgra_cfg_g2f_internal_d1[i];
    end
end

endmodule
