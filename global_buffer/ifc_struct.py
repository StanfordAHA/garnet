import magma

def ProcPacketIfc(addr_width, data_width):
    """
    This function returns a class (parameterized by @addr_width and
    @data_width) which can be used as the magma ports
    """

    _Slave = magma.Product.from_fields("ProcPacketIfcSlave", dict(
        wr_en=magma.In(magma.Bit),
        wr_strb=magma.In(magma.Bits[int(self.data_width/8)]),
        wr_addr=magma.In(magma.Bits[self.addr_width]),
        wr_data=magma.In(magma.Bits[self.data_width]),
        rd_en=magma.In(magma.Bit),
        rd_addr=magma.In(magma.Bits[self.addr_width]),
        rd_data=magma.Out(magma.Bits[self.data_width]),
        rd_data_valid=magma.Out(magma.Bit)))

    return _Slave

def GlbCfgIfc(addr_width, data_width):
    """
    This function returns a class (parameterized by @addr_width and
    @data_width) which can be used as the magma ports
    """

    _Slave = magma.Product.from_fields("GlbCfgIfcSlave", dict(
        wr_en=magma.In(magma.Bit),
        wr_clk_en=magma.In(magma.Bit),
        wr_addr=magma.In(magma.Bits[addr_width]),
        wr_data=magma.In(magma.Bits[data_width]),
        rd_en=magma.In(magma.Bit),
        rd_clk_en=magma.In(magma.Bit),
        rd_addr=magma.In(magma.Bits[addr_width]),
        rd_data=magma.Out(magma.Bits[data_width]),
        rd_data_valid=magma.Out(magma.Bit)))

    return _Slave

def CgraCfgStruct(addr_width, data_width):
    return magma.Tuple(wr_en=magma.Bits[1],
                       wr_clk_en=magma.Bits[1],
                       wr_addr=magma.Bits[addr_width],
                       wr_data=magma.Bits[data_width])
