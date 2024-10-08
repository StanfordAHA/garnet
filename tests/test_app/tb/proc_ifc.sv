/*=============================================================================
** Module: proc_ifc.sv
** Description:
**              interface for processor packet 
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

interface proc_ifc (
    input logic clk
);

    // declare the signals
    logic                         wr_en;
    logic [BANK_DATA_WIDTH/8-1:0] wr_strb;
    logic [   GLB_ADDR_WIDTH-1:0] wr_addr;
    logic [  BANK_DATA_WIDTH-1:0] wr_data;
    logic                         rd_en;
    logic [   GLB_ADDR_WIDTH-1:0] rd_addr;
    logic [  BANK_DATA_WIDTH-1:0] rd_data;
    logic                         rd_data_valid;

    modport glb(
        input clk,
        input wr_en, wr_strb, wr_addr, wr_data, rd_en, rd_addr,
        output rd_data, rd_data_valid
    );

    clocking cbd @(posedge clk);
        input clk;
        output wr_en, wr_strb, wr_addr, wr_data, rd_en, rd_addr;
        input rd_data, rd_data_valid;
    endclocking : cbd
    modport driver(clocking cbd);

    clocking cbm @(posedge clk);
        input clk, wr_en, wr_strb, wr_addr, wr_data, rd_en, rd_addr, rd_data, rd_data_valid;
    endclocking : cbm
    modport monitor(clocking cbm);

endinterface

typedef virtual proc_ifc vProcIfc;
typedef virtual proc_ifc.driver vProcIfcDriver;
typedef virtual proc_ifc.monitor vProcIfcMonitor;
