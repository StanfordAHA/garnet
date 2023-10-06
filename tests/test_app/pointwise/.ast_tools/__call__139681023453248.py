def __call__(self, in0: Data, in1: Data, in2: Data) -> Data:
    min_in0_in1_0 = (UInt(in0) <= UInt(in1)).ite(UInt(in0), UInt(in1))
    __0_return_0 = Data(
        (UInt(min_in0_in1_0) >= UInt(in2)).ite(UInt(min_in0_in1_0), UInt(in2))
    )
    return __0_return_0
