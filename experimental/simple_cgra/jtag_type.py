import magma


JTAGType = magma.Tuple(
    tdi=magma.Bit,
    tdo=magma.Bit,
    tms=magma.Bit,
    tck=magma.Bit,
    trst_n=magma.Bit)
