/*=============================================================================
** Module: pcfg_ifc.sv
** Description:
**              interface for parallel configuration
** Author: Taeyoung Kong
** Change history:
**  04/24/2020 - Implement first version
**===========================================================================*/

interface pcfg_ifc (
    input logic clk);

    // declare the signals
    logic                                               pcfg_start_pulse;
    logic                                               pcfg_interrupt;

    logic [CGRA_PER_GLB-1:0]                            cgra_cfg_wr_en;
    logic [CGRA_PER_GLB-1:0]                            cgra_cfg_rd_en;
    logic [CGRA_PER_GLB-1:0][CGRA_CFG_ADDR_WIDTH-1:0]   cgra_cfg_addr;
    logic [CGRA_PER_GLB-1:0][CGRA_CFG_DATA_WIDTH-1:0]   cgra_cfg_data;

    modport glb (
        input  clk, pcfg_start_pulse,
        output cgra_cfg_wr_en, cgra_cfg_rd_en, cgra_cfg_addr, cgra_cfg_data,
        output pcfg_interrupt
    );

    clocking cbd @(posedge clk);
        input  clk;
        output pcfg_start_pulse;
        input  cgra_cfg_wr_en, cgra_cfg_rd_en, cgra_cfg_addr, cgra_cfg_data;
        input  pcfg_interrupt;
    endclocking : cbd
    modport driver (clocking cbd);

    clocking cbm @(posedge clk);
        input clk, pcfg_start_pulse, cgra_cfg_wr_en, cgra_cfg_rd_en, cgra_cfg_addr, cgra_cfg_data, pcfg_interrupt;
    endclocking : cbm
    modport monitor (clocking cbm);

endinterface

typedef virtual pcfg_ifc vPcfgIfc;
typedef virtual pcfg_ifc.driver vPcfgIfcDriver;
typedef virtual pcfg_ifc.monitor vPcfgIfcMonitor;
