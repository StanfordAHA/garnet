def __call__(self, in0: Data, in1: Data) -> Data:
    in0_float_0 = cast(in0)
    in1_float_0 = cast(in1)
    out_float_0 = getattr(in0_float_0, op_name)(in1_float_0)
    out_0 = out_float_0.reinterpret_as_bv()
    __0_return_0 = out_0
    return __0_return_0
