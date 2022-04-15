import magma


class ProcPacketIfc:
    """
    This class is like a SystemVerilog interface
    slave and master attributes are classes which can be used as the magma ports
    """

    def __init__(self, addr_width, data_width):
        self.addr_width = addr_width
        self.data_width = data_width

        self.slave = magma.Product.from_fields("ProcPacketIfcSlave", dict(
            wr_en=magma.In(magma.Bit),
            wr_strb=magma.In(magma.Bits[self.data_width // 8]),
            wr_addr=magma.In(magma.Bits[self.addr_width]),
            wr_data=magma.In(magma.Bits[self.data_width]),
            rd_en=magma.In(magma.Bit),
            rd_addr=magma.In(magma.Bits[self.addr_width]),
            rd_data=magma.Out(magma.Bits[self.data_width]),
            rd_data_valid=magma.Out(magma.Bit)))

        self.master = magma.Product.from_fields("ProcPacketIfcMaster", dict(
            wr_en=magma.Out(magma.Bit),
            wr_strb=magma.Out(magma.Bits[self.data_width // 8]),
            wr_addr=magma.Out(magma.Bits[self.addr_width]),
            wr_data=magma.Out(magma.Bits[self.data_width]),
            rd_en=magma.Out(magma.Bit),
            rd_addr=magma.Out(magma.Bits[self.addr_width]),
            rd_data=magma.In(magma.Bits[self.data_width]),
            rd_data_valid=magma.In(magma.Bit)))


class GlbCfgIfc:
    def __init__(self, addr_width, data_width, is_clk_en=True):
        self.addr_width = addr_width
        self.data_width = data_width

        if is_clk_en:
            self.slave = magma.Product.from_fields("GlbCfgIfcSlave", dict(
                wr_en=magma.In(magma.Bit),
                wr_clk_en=magma.In(magma.Bit),
                wr_addr=magma.In(magma.Bits[addr_width]),
                wr_data=magma.In(magma.Bits[data_width]),
                rd_en=magma.In(magma.Bit),
                rd_clk_en=magma.In(magma.Bit),
                rd_addr=magma.In(magma.Bits[addr_width]),
                rd_data=magma.Out(magma.Bits[data_width]),
                rd_data_valid=magma.Out(magma.Bit)))

            self.master = magma.Product.from_fields("GlbCfgIfcMaster", dict(
                wr_en=magma.Out(magma.Bit),
                wr_clk_en=magma.Out(magma.Bit),
                wr_addr=magma.Out(magma.Bits[addr_width]),
                wr_data=magma.Out(magma.Bits[data_width]),
                rd_en=magma.Out(magma.Bit),
                rd_clk_en=magma.Out(magma.Bit),
                rd_addr=magma.Out(magma.Bits[addr_width]),
                rd_data=magma.In(magma.Bits[data_width]),
                rd_data_valid=magma.In(magma.Bit)))
        else:
            self.slave = magma.Product.from_fields("GlbCfgIfcSlave", dict(
                wr_en=magma.In(magma.Bit),
                wr_addr=magma.In(magma.Bits[addr_width]),
                wr_data=magma.In(magma.Bits[data_width]),
                rd_en=magma.In(magma.Bit),
                rd_addr=magma.In(magma.Bits[addr_width]),
                rd_data=magma.Out(magma.Bits[data_width]),
                rd_data_valid=magma.Out(magma.Bit)))

            self.master = magma.Product.from_fields("GlbCfgIfcMaster", dict(
                wr_en=magma.Out(magma.Bit),
                wr_addr=magma.Out(magma.Bits[addr_width]),
                wr_data=magma.Out(magma.Bits[data_width]),
                rd_en=magma.Out(magma.Bit),
                rd_addr=magma.Out(magma.Bits[addr_width]),
                rd_data=magma.In(magma.Bits[data_width]),
                rd_data_valid=magma.In(magma.Bit)))


"""
This class returns a axi4-slave class (parameterized by @addr_width and
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


class AXI4LiteIfc:
    def __init__(self, addr_width, data_width):
        self.addr_width = addr_width
        self.data_width = data_width

        self.slave = magma.Product.from_fields("AXI4SlaveType", dict(
            awaddr=magma.In(magma.Bits[addr_width]),
            awvalid=magma.In(magma.Bit),
            awready=magma.Out(magma.Bit),
            wdata=magma.In(magma.Bits[data_width]),
            wvalid=magma.In(magma.Bit),
            wready=magma.Out(magma.Bit),
            bready=magma.In(magma.Bit),
            bresp=magma.Out(magma.Bits[2]),
            bvalid=magma.Out(magma.Bit),
            araddr=magma.In(magma.Bits[addr_width]),
            arvalid=magma.In(magma.Bit),
            arready=magma.Out(magma.Bit),
            rdata=magma.Out(magma.Bits[data_width]),
            rresp=magma.Out(magma.Bits[2]),
            rvalid=magma.Out(magma.Bit),
            rready=magma.In(magma.Bit)))

        self.master = magma.Product.from_fields("AXI4MasterType", dict(
            awaddr=magma.Out(magma.Bits[addr_width]),
            awvalid=magma.Out(magma.Bit),
            awready=magma.In(magma.Bit),
            wdata=magma.Out(magma.Bits[data_width]),
            wvalid=magma.Out(magma.Bit),
            wready=magma.In(magma.Bit),
            bready=magma.Out(magma.Bit),
            bresp=magma.In(magma.Bits[2]),
            bvalid=magma.In(magma.Bit),
            araddr=magma.Out(magma.Bits[addr_width]),
            arvalid=magma.Out(magma.Bit),
            arready=magma.In(magma.Bit),
            rdata=magma.In(magma.Bits[data_width]),
            rresp=magma.In(magma.Bits[2]),
            rvalid=magma.In(magma.Bit),
            rready=magma.Out(magma.Bit)))
