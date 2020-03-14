import global_buffer_pkg::*;

module global_buffer_wrapper (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,

    // axi lite
    input  logic [AXI_ADDR_WIDTH-1:0]  if_axil_awaddr,
    output logic                       if_axil_awready,
    input  logic                       if_axil_awvalid,
                                               
    input  logic [AXI_DATA_WIDTH-1:0]  if_axil_wdata,
    output logic                       if_axil_wready,
    input  logic                       if_axil_wvalid,
                                               
    input  logic                       if_axil_bready,
    output logic [1:0]                 if_axil_bresp,
    output logic                       if_axil_bvalid,
                                               
    input  logic [AXI_ADDR_WIDTH-1:0]  if_axil_araddr,
    output logic                       if_axil_arready,
    input  logic                       if_axil_arvalid,
                                               
    output logic [AXI_DATA_WIDTH-1:0]  if_axil_rdata,
    input  logic                       if_axil_rready,
    output logic [1:0]                 if_axil_rresp,
    output logic                       if_axil_rvalid,
                                               
    input  logic [AXI_STRB_WIDTH-1:0]  if_axil_wstrb,
    input  logic [2:0]                 if_axil_arprot,
    input  logic [2:0]                 if_axil_awprot,

    // cgra to glb streaming word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g [NUM_GLB_TILES],
    input  logic                            stream_data_valid_f2g [NUM_GLB_TILES],

    // glb to cgra streaming word
    output logic [CGRA_DATA_WIDTH-1:0]      stream_data_g2f [NUM_GLB_TILES],
    output logic                            stream_data_valid_g2f [NUM_GLB_TILES],

    // cgra configuration from global controller
    input  cgra_cfg_t                       cgra_cfg_gc2glb,

    // cgra configuration to cgra
    output cgra_cfg_t                       cgra_cfg_g2f [NUM_GLB_TILES],

    output logic                            interrupt
);

axil_ifc if_axil();

assign if_axil.awaddr = if_axil_awaddr;
assign if_axil.awready = if_axil_awready;
assign if_axil.awvalid = if_axil_awvalid;

assign if_axil.wdata = if_axil_wdata;
assign if_axil.wready = if_axil_wready;
assign if_axil.wvalid = if_axil_wvalid;

assign if_axil.bready = if_axil_bready;
assign if_axil.bresp = if_axil_bresp;
assign if_axil.bvalid = if_axil_bvalid;

assign if_axil.araddr = if_axil_araddr;
assign if_axil.arready = if_axil_arready;
assign if_axil.arvalid = if_axil_arvalid;

assign if_axil.rdata = if_axil_rdata;
assign if_axil.rready = if_axil_rready;
assign if_axil.rresp = if_axil_rresp;
assign if_axil.rvalid = if_axil_rvalid;

assign if_axil.wstrb = if_axil_wstrb;
assign if_axil.arprot = if_axil_arprot;
assign if_axil.awprot = if_axil_awprot;

global_buffer global_buffer (
    if_axil(if_axil.slave),
    .*);

endmodule
