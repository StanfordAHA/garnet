import global_buffer_pkg::*;

module global_buffer_wrapper (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,

    // axi lite
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
    input  awprot,

    // cgra to glb streaming word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g [NUM_TILES],
    input  logic                            stream_data_valid_f2g [NUM_TILES],

    // glb to cgra streaming word
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f [NUM_TILES],
    output logic                            stream_data_valid_g2f [NUM_TILES],

    // cgra configuration from global controller
    input  cgra_cfg_t                       cgra_cfg_gc2glb,

    // cgra configuration to cgra
    output cgra_cfg_t                       cgra_cfg_g2f [NUM_TILES],

    output logic                            interrupt
);

global_buffer global_buffer (
    if_axil.awaddr(awaddr),
    if_axil.awready(awready),
    if_axil.awvalid(awvalid),

    if_axil.wdata(wdata),
    if_axil.wready(wready),
    if_axil.wvalid(wvalid),

    if_axil.bready(bready),
    if_axil.bresp(bresp),
    if_axil.bvalid(bvalid),

    if_axil.araddr(araddr),
    if_axil.arready(arready),
    if_axil.arvalid(arvalid),

    if_axil.rdata(rdata),
    if_axil.rready(rready),
    if_axil.rresp(rresp),
    if_axil.rvalid(rvalid),

    if_axil.wstrb(wstrb),
    if_axil.arprot(arprot),
    if_axil.awprot(awprot),
    .*);

endmodule
