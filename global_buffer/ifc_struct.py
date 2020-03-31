import magma

def ProcPacketIfc(addr_width, data_width):
    """
    This function returns a class (parameterized by @addr_width and
    @data_width) which can be used as the magma ports
    """

    _Slave = magma.Product.from_fields("ProcPacketIfcSlave", dict(
        wr_en=magma.In(magma.Bit),
        wr_strb=magma.In(magma.Bits[int(data_width/8)]),
        wr_addr=magma.In(magma.Bits[addr_width]),
        wr_data=magma.In(magma.Bits[data_width]),
        rd_en=magma.In(magma.Bit),
        rd_addr=magma.In(magma.Bits[addr_width]),
        rd_data=magma.Out(magma.Bits[data_width]),
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

def CgraCfgStruct(addr_width, data_width, arr_size=1):
    return magma.Product.from_fields("CgraCfgStruct",
                                     dict(wr_en=magma.Bits[arr_size*1],
                                          rd_en=magma.Bits[arr_size*1],
                                          addr=magma.Bits[(arr_size
                                                           *addr_width)],
                                          data=magma.Bits[(arr_size
                                                           *data_width)]))
