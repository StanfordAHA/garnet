@name_outputs(cond=Bit)
def __call__(
    self, code: Cond_t, alu: Bit, lut: Bit, Z: Bit, N: Bit, C: Bit, V: Bit
) -> Bit:
    _cond_18 = code == Cond_t.Z
    __0_return_0 = Z
    _cond_17 = code == Cond_t.Z_n
    __0_return_1 = ~Z
    _cond_16 = (code == Cond_t.C) | (code == Cond_t.UGE)
    __0_return_2 = C
    _cond_15 = (code == Cond_t.C_n) | (code == Cond_t.ULT)
    __0_return_3 = ~C
    _cond_14 = code == Cond_t._N
    __0_return_4 = N
    _cond_13 = code == Cond_t._N_n
    __0_return_5 = ~N
    _cond_12 = code == Cond_t.V
    __0_return_6 = V
    _cond_11 = code == Cond_t.V_n
    __0_return_7 = ~V
    _cond_10 = code == Cond_t.UGT
    __0_return_8 = C & (~Z)
    _cond_9 = code == Cond_t.ULE
    __0_return_9 = (~C) | Z
    _cond_8 = code == Cond_t.SGE
    __0_return_10 = N == V
    _cond_7 = code == Cond_t.SLT
    __0_return_11 = N != V
    _cond_6 = code == Cond_t.SGT
    __0_return_12 = (~Z) & (N == V)
    _cond_5 = code == Cond_t.SLE
    __0_return_13 = Z | (N != V)
    _cond_4 = code == Cond_t.ALU
    __0_return_14 = alu
    _cond_3 = code == Cond_t.LUT
    __0_return_15 = lut
    _cond_2 = code == Cond_t.FP_GE
    __0_return_16 = ~N | Z
    _cond_1 = code == Cond_t.FP_GT
    __0_return_17 = ~N & ~Z
    _cond_0 = code == Cond_t.FP_LE
    __0_return_18 = N | Z
    __0_return_19 = N & ~Z
    return __phi(_cond_18, __0_return_0, __phi(_cond_17, __0_return_1, __phi(_cond_16, __0_return_2, __phi(_cond_15, __0_return_3, __phi(_cond_14, __0_return_4, __phi(_cond_13, __0_return_5, __phi(_cond_12, __0_return_6, __phi(_cond_11, __0_return_7, __phi(_cond_10, __0_return_8, __phi(_cond_9, __0_return_9, __phi(_cond_8, __0_return_10, __phi(_cond_7, __0_return_11, __phi(_cond_6, __0_return_12, __phi(_cond_5, __0_return_13, __phi(_cond_4, __0_return_14, __phi(_cond_3, __0_return_15, __phi(_cond_2, __0_return_16, __phi(_cond_1, __0_return_17, __phi(_cond_0, __0_return_18, __0_return_19)))))))))))))))))))
