/*=============================================================================
** Module: axil_ifc
** Description:
**              AXI4-Lite interface
** Author: Taeyoung Kong
** Change history: 02/01/2019 - Implement first version of interface
**===========================================================================*/
`ifndef AXIL_IFC
`define AXIL_IFC

interface axil_ifc #(
    parameter integer AXI_AWIDTH = 12,
    parameter integer AXI_DWIDTH = 32,
    parameter integer AXI_STRBWIDTH = (AXI_DWIDTH / 8)
);
    // AW ports
    logic [AXI_AWIDTH-1:0]      awaddr;
    logic                       awready;
    logic                       awvalid;

    // W ports
    logic [AXI_DWIDTH-1:0]      wdata;
    logic                       wready;
    logic                       wvalid;

    // B ports
    logic                       bready;
    logic [1:0]                 bresp;
    logic                       bvalid;

    // AR ports
    logic [AXI_AWIDTH-1:0]      araddr;
    logic                       arready;
    logic                       arvalid;

    // R ports
    logic [AXI_DWIDTH-1:0]      rdata;
    logic                       rready;
    logic [1:0]                 rresp;
    logic                       rvalid;

    // unused ports
    logic [AXI_STRBWIDTH-1:0]   wstrb;
    logic [2:0]                 arprot;
    logic [2:0]                 awprot;

    modport slave(
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
   
    modport master (
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

    modport test (
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

endinterface: axil_ifc

`endif
