/*=============================================================================
** Module: axil_ifc
** Description:
**              AXI4-Lite interface
** Author: Taeyoung Kong
** Change history: 02/01/2019 - Implement first version of interface
**===========================================================================*/

interface axil_ifc #(
    parameter int ADDR_WIDTH = 13,
    parameter int DATA_WIDTH = 32
) (
    input clk
);
    // AW ports
    logic [  ADDR_WIDTH-1:0] awaddr;
    logic                    awready;
    logic                    awvalid;

    // W ports
    logic [  DATA_WIDTH-1:0] wdata;
    logic                    wready;
    logic                    wvalid;
    logic [DATA_WIDTH/8-1:0] wstrb;

    // B ports
    logic                    bready;
    logic [             1:0] bresp;
    logic                    bvalid;

    // AR ports
    logic [  ADDR_WIDTH-1:0] araddr;
    logic                    arready;
    logic                    arvalid;

    // R ports
    logic [  DATA_WIDTH-1:0] rdata;
    logic                    rready;
    logic [             1:0] rresp;
    logic                    rvalid;

    // unused ports
    logic [             2:0] arprot;
    logic [             2:0] awprot;

    modport slave(
        input clk,
        input awaddr,
        output awready,
        input awvalid,

        input wdata,
        output wready,
        input wvalid,
        input wstrb,

        input bready,
        output bresp,
        output bvalid,

        input araddr,
        output arready,
        input arvalid,

        output rdata,
        input rready,
        output rresp,
        output rvalid,

        input arprot,
        input awprot
    );

    clocking cbd @(posedge clk);
        input clk;

        output awaddr;
        input awready;
        output awvalid;

        output wdata;
        input wready;
        output wvalid;
        output wstrb;

        output bready;
        input bresp;
        input bvalid;

        output araddr;
        input arready;
        output arvalid;

        input rdata;
        output rready;
        input rresp;
        input rvalid;

        output arprot;
        output awprot;
    endclocking : cbd
    modport driver(clocking cbd);

endinterface

typedef virtual axil_ifc vAxilIfc;
typedef virtual axil_ifc.driver vAxilIfcDriver;
