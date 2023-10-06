def __call__(self, in0: Data) -> Data:

    __0_return_0 = Data((SInt(in0) >= SInt(0)).ite(SInt(in0), SInt(-1) * SInt(in0)))
    return __0_return_0
