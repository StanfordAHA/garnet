/*=============================================================================
** Module: pcfg_ifc.sv
** Description:
**              interface for parallel configuration
** Author: Taeyoung Kong
** Change history:
**  04/24/2020 - Implement first version
**===========================================================================*/

interface pcfg_ifc (input logic clk);

    // declare the signals
    logic [CGRA_PER_GLB-1:0]                            cgra_cfg_wr_en;
    logic [CGRA_PER_GLB-1:0]                            cgra_cfg_rd_en;
    logic [CGRA_PER_GLB-1:0][CGRA_CFG_ADDR_WIDTH-1:0]   cgra_cfg_addr;
    logic [CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0]   cgra_cfg_data;

    modport glb (
        input  clk,
        output cgra_cfg_wr_en, cgra_cfg_rd_en, cgra_cfg_addr, cgra_cfg_data
    );

    clocking cbd @(posedge clk);
        input  clk;
        input  cgra_cfg_wr_en, cgra_cfg_rd_en, cgra_cfg_addr, cgra_cfg_data;
    endclocking : cbd
    modport driver (clocking cbd);

    clocking cbm @(posedge clk);
        input clk, cgra_cfg_wr_en, cgra_cfg_rd_en, cgra_cfg_addr, cgra_cfg_data;
    endclocking : cbm
    modport monitor (clocking cbm);

endinterface

typedef virtual pcfg_ifc vPcfgIfc;
typedef virtual pcfg_ifc.driver vPcfgIfcDriver;
typedef virtual pcfg_ifc.monitor vPcfgIfcMonitor;
