def __call__(self, in0: Data, in1: Data, in2: Data) -> Data:
    min_in0_in1_0 = (SInt(in0) <= SInt(in1)).ite(SInt(in0), SInt(in1))
    __0_return_0 = Data(
        (SInt(min_in0_in1_0) >= SInt(in2)).ite(SInt(min_in0_in1_0), SInt(in2))
    )
    return __0_return_0
