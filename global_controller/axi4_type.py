import magma

def AXI4SlaveType(addr_width, data_width):
    """
    This function returns a axi4-slave class (parameterized by @addr_width and
    @data_width) which can be used as the magma ports with these inputs
    and outputs
    Below is AXI4-Lite interface ports in verilog

    input  logic [`$axi_addr_width-1`:0]    AWADDR,
    input  logic                            AWVALID,
    output logic                            AWREADY,
    input  logic [`$cfg_bus_width-1`:0]     WDATA,
    input  logic                            WVALID,
    output logic                            WREADY,
    input  logic [`$axi_addr_width-1`:0]     ARADDR,
    input  logic                            ARVALID,
    output logic                            ARREADY,
    output logic [`$cfg_bus_width-1`:0]     RDATA,
    output logic [1:0]                      RRESP,
    output logic                            RVALID,
    input  logic                            RREADY,
    output logic                            interrupt,

    """

    _AXI4SlaveType = magma.Product.from_fields("AXI4SlaveType", dict(
        awaddr=magma.In(magma.Bits[addr_width]),
        awvalid=magma.In(magma.Bit),
        awready=magma.Out(magma.Bit),
        wdata=magma.In(magma.Bits[data_width]),
        wvalid=magma.In(magma.Bit),
        wready=magma.Out(magma.Bit),
        araddr=magma.In(magma.Bits[addr_width]),
        arvalid=magma.In(magma.Bit),
        arready=magma.Out(magma.Bit),
        rdata=magma.Out(magma.Bits[data_width]),
        rresp=magma.Out(magma.Bits[2]),
        rvalid=magma.Out(magma.Bit),
        rready=magma.In(magma.Bit),
        interrupt=magma.Out(magma.Bit)))

    return _AXI4SlaveType
