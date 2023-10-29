def __call__(self, in1: Data, in0: Data, sel: Bit) -> Data:

    __0_return_0 = Data(sel.ite(UInt(in1), UInt(in0)))
    return __0_return_0
