/*=============================================================================
** Module: axil_ifc
** Description:
**              AXI4-Lite interface
** Author: Taeyoung Kong
** Change history: 10/14/2020 - Implement first version of interface
**===========================================================================*/

interface axil_ifc #(
    parameter integer ADDR_WIDTH = 13,
    parameter integer DATA_WIDTH = 32
) ( input logic clk );
    // AW ports
    logic [ADDR_WIDTH-1:0]      awaddr;
    logic                       awready;
    logic                       awvalid;

    // W ports
    logic [DATA_WIDTH-1:0]      wdata;
    logic                       wready;
    logic                       wvalid;

    // B ports
    logic                       bready;
    logic [1:0]                 bresp;
    logic                       bvalid;

    // AR ports
    logic [ADDR_WIDTH-1:0]      araddr;
    logic                       arready;
    logic                       arvalid;

    // R ports
    logic [DATA_WIDTH-1:0]      rdata;
    logic                       rready;
    logic [1:0]                 rresp;
    logic                       rvalid;

    // unused ports
    logic [DATA_WIDTH/8-1:0]    wstrb;
    logic [2:0]                 arprot;
    logic [2:0]                 awprot;

    clocking cbd @(posedge clk);
        input clk;
        // AW
        output awaddr, awvalid;
        input  awready;
        // W
        output wdata, wvalid, wstrb;
        input  wready;
        // B
        output bready;
        input  bresp, bvalid;
        // AR
        output araddr, arvalid;
        input  arready;
        // R
        output rready;
        input  rdata, rresp, rvalid;
        // unused
        output arprot, awprot;
    endclocking : cbd
    modport driver (clocking cbd);

    modport master (
        input  clk,
        output awaddr,
        input  awready,
        output awvalid,

        output wdata,
        input  wready,
        output wvalid,

        output bready,
        input  bresp,
        input  bvalid,

        output araddr,
        input  arready,
        output arvalid,

        input  rdata,
        output rready,
        input  rresp,
        input  rvalid,

        output wstrb,
        output arprot,
        output awprot
    );

    modport slave(
        input  clk,
        input  awaddr,
        output awready,
        input  awvalid,

        input  wdata,
        output wready,
        input  wvalid,

        input  bready,
        output bresp,
        output bvalid,

        input  araddr,
        output arready,
        input  arvalid,

        output rdata,
        input  rready,
        output rresp,
        output rvalid,

        input  wstrb,
        input  arprot,
        input  awprot
    );

endinterface

typedef virtual axil_ifc vAxilIfc;
typedef virtual axil_ifc.driver vAxilIfcDriver;
