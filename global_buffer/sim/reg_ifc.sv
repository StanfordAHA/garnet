/*=============================================================================
** Module: reg_ifc.sv
** Description:
**              interface for configuration
** Author: Taeyoung Kong
** Change history:
**  04/19/2020 - Implement first version
**===========================================================================*/

interface reg_ifc #(
    parameter int ADDR_WIDTH = AXI_ADDR_WIDTH,
    parameter int DATA_WIDTH = AXI_DATA_WIDTH
)    
(
    input logic clk
);

    // declare the signals
    logic                       wr_en;
    logic                       wr_clk_en;
    logic [ADDR_WIDTH-1:0]      wr_addr;
    logic [DATA_WIDTH-1:0]      wr_data;
    logic                       rd_en;
    logic                       rd_clk_en;
    logic [ADDR_WIDTH-1:0]      rd_addr;
    logic [DATA_WIDTH-1:0]      rd_data;
    logic                       rd_data_valid;

    modport glb (
        input  clk,
        input  wr_en, wr_clk_en, wr_addr, wr_data, rd_en, rd_clk_en, rd_addr,
        output rd_data, rd_data_valid
    );

    clocking cbd @(posedge clk);
        default input #200ps output #200ps;
        output wr_en, wr_addr, wr_data, rd_en, rd_addr;
        input  rd_data, rd_data_valid;
    endclocking : cbd
    clocking cbd_n @(negedge clk);
        default input #200ps output #200ps;
        output wr_clk_en, rd_clk_en;
    endclocking : cbd_n
    modport driver (clocking cbd, clocking cbd_n);

    clocking cbm @(posedge clk);
        default input #200ps output #200ps;
        input  wr_en, wr_clk_en, wr_addr, wr_data, rd_en, rd_clk_en, rd_addr, rd_data, rd_data_valid;
    endclocking : cbm
    modport monitor (clocking cbm);

endinterface

typedef virtual reg_ifc#(.ADDR_WIDTH(32)) vRegIfc;
typedef virtual reg_ifc#(.ADDR_WIDTH(32)).driver vRegIfcDriver;
typedef virtual reg_ifc#(.ADDR_WIDTH(32)).monitor vRegIfcMonitor;
