/*=============================================================================
** Module: glb_tile_pc_switch.sv
** Description:
**              Global Buffer Tile Parallel Configuration Controller
** Author: Taeyoung Kong
** Change history: 03/02/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_tile_pc_switch (
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
    output cgra_cfg_t                       cgra_cfg_g2f [CGRA_PER_GLB]
);

//============================================================================//
// Simple router
//============================================================================//
cgra_cfg_t cgra_cfg_pc_switched;
cgra_cfg_t cgra_cfg_pc_jtag_esto_r;
assign cgra_cfg_pc_switched = (cfg_pc_dma_mode == 1) ? cgra_cfg_c2sw : cgra_cfg_pc_wsti;

//============================================================================//
// no pipeline registers for configuration read
//============================================================================//
// if it is read, just bypass configuration packet
always_comb begin
    if (cgra_cfg_jtag_wsti.cfg_rd_en) begin
        cgra_cfg_jtag_esto = cgra_cfg_jtag_wsti;
    end
    else begin
        cgra_cfg_jtag_esto = cgra_cfg_jtag_esto_r;
    end
end

//============================================================================//
// pipeline registers for configuration write
//============================================================================//
always_ff @ (posedge clk or posedge reset) begin
    if (reset) begin
        cgra_cfg_jtag_esto_r <= '0;
        cgra_cfg_pc_esto <= '0;
    end
    else begin
        cgra_cfg_jtag_esto_r <= cgra_cfg_jtag_wsti;
        cgra_cfg_pc_esto <= cgra_cfg_pc_switched;
    end
end

//============================================================================//
// output assignment
//============================================================================//
// Just ORing works
always_comb begin
    for (int i=0; i<CGRA_PER_GLB; i=i+1) begin
        cgra_cfg_g2f[i] = cgra_cfg_jtag_esto | cgra_cfg_pc_esto;
    end
end

endmodule
