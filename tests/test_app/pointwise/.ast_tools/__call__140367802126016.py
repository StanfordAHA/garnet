@name_outputs(res=Data, res_p=Bit, Z=Bit, N=Bit, C=Bit, V=Bit)
def __call__(
    self,
    alu: Const(ALU_t),
    signed_: Const(Signed_t),
    a: DataPy,
    b: DataPy,
    c: DataPy,
    d: BitPy,
) -> (DataPy, BitPy, BitPy, BitPy, BitPy, BitPy):
    _cond_0 = signed_ == Signed_t.signed
    mula_0 = UData32(SData(a).sext(16))
    mulb_0 = UData32(SData(b).sext(16))
    mula_1 = UData(a).zext(16)
    mulb_1 = UData(b).zext(16)
    mula_2 = __phi(_cond_0, mula_0, mula_1)
    mulb_2 = __phi(_cond_0, mulb_0, mulb_1)
    mul_0 = mula_2 * mulb_2
    _cond_1 = signed_ == Signed_t.signed
    lte_pred_0 = SData(a) <= SData(b)
    lte_pred_1 = UData(a) <= UData(b)
    lte_pred_2 = __phi(_cond_1, lte_pred_0, lte_pred_1)
    min_ab_0 = lte_pred_2.ite(a, b)
    _cond_2 = alu == ALU_t.CROP
    max_in0_0 = min_ab_0
    max_in0_1 = b
    max_in0_2 = __phi(_cond_2, max_in0_0, max_in0_1)
    _cond_3 = signed_ == Signed_t.signed
    gte_pred_0 = SData(max_in0_2) >= SData(c)
    gte_pred_1 = UData(max_in0_2) >= UData(c)
    gte_pred_2 = __phi(_cond_3, gte_pred_0, gte_pred_1)
    max_bc_0 = gte_pred_2.ite(max_in0_2, c)
    _cond_4 = alu == ALU_t.MULSHR
    shr_in0_0 = mul_0[:16]
    shr_in0_1 = a
    shr_in0_2 = __phi(_cond_4, shr_in0_0, shr_in0_1)
    _cond_5 = signed_ == Signed_t.signed
    shr_0 = Data(SData(shr_in0_2) >> SData(c))
    shr_1 = Data(UData(shr_in0_2) >> UData(c))
    shr_2 = __phi(_cond_5, shr_0, shr_1)
    _cond_6 = (alu == ALU_t.Sbc) | (alu == ALU_t.TSA) | (alu == ALU_t.TSS)
    b_0 = ~b
    b_1 = __phi(_cond_6, b_0, b)

    Cin_0 = d

    # factor out comman add
    adder_res_0, adder_C_0 = UData(a).adc(UData(b_1), Cin_0)
    _cond_7 = (
        (alu == ALU_t.TAA)
        | (alu == ALU_t.TAS)
        | (alu == ALU_t.TSA)
        | (alu == ALU_t.TSS)
    )
    adder2_in0_0 = adder_res_0
    adder2_in0_1 = mul_0[:16]
    adder2_in0_2 = __phi(_cond_7, adder2_in0_0, adder2_in0_1)
    _cond_8 = (alu == ALU_t.MULSUB) | (alu == ALU_t.TAS) | (alu == ALU_t.TSS)
    adder2_in1_0 = ~c
    Cin2_0 = Bit(1)
    adder2_in1_1 = c
    Cin2_1 = Bit(0)
    Cin2_2 = __phi(_cond_8, Cin2_0, Cin2_1)
    adder2_in1_2 = __phi(_cond_8, adder2_in1_0, adder2_in1_1)

    adder2_res_0, adder2_C_0 = UData(adder2_in0_2).adc(adder2_in1_2, Cin2_2)

    C_0 = Bit(0)
    V_0 = Bit(0)
    _cond_21 = (alu == ALU_t.Adc) | (alu == ALU_t.Sbc)
    res_0, C_1 = adder_res_0, adder_C_0
    V_1 = overflow(a, b_1, res_0)
    res_p_0 = C_1
    _cond_20 = alu == ALU_t.Mult0
    res_1, C_2, V_2 = mul_0[:16], Bit(0), Bit(0)
    res_p_1 = C_2
    _cond_19 = alu == ALU_t.Mult1
    res_2, C_3, V_3 = mul_0[8:24], Bit(0), Bit(0)
    res_p_2 = C_3
    _cond_18 = alu == ALU_t.Mult2
    res_3, C_4, V_4 = mul_0[16:32], Bit(0), Bit(0)
    res_p_3 = C_4
    _cond_17 = alu == ALU_t.Abs
    abs_pred_0 = SData(a) >= SData(0)
    res_4, res_p_4 = abs_pred_0.ite(a, UInt[16](-SInt[16](a))), Bit(a[-1])
    _cond_16 = alu == ALU_t.Sel
    res_5, res_p_5 = d.ite(a, b_1), Bit(0)
    _cond_15 = alu == ALU_t.And
    res_6, res_p_6 = a & b_1, Bit(0)
    _cond_14 = alu == ALU_t.Or
    res_7, res_p_7 = a | b_1, Bit(0)
    _cond_13 = alu == ALU_t.XOr
    res_8, res_p_8 = a ^ b_1, Bit(0)
    _cond_12 = alu == ALU_t.SHR
    res_9, res_p_9 = shr_2, Bit(0)
    _cond_11 = alu == ALU_t.SHL
    res_10, res_p_10 = a << b_1, Bit(0)
    _cond_10 = (
        (alu == ALU_t.MULADD)
        | (alu == ALU_t.MULSUB)
        | (alu == ALU_t.TAA)
        | (alu == ALU_t.TSA)
        | (alu == ALU_t.TAS)
        | (alu == ALU_t.TSS)
    )
    res_11, res_p_11 = adder2_res_0, Bit(0)
    _cond_9 = alu == ALU_t.CROP
    res_12, res_p_12 = max_bc_0, Bit(0)
    res_13, res_p_13 = shr_2, Bit(0)
    res_14 = __phi(_cond_9, res_12, res_13)
    res_p_14 = __phi(_cond_9, res_p_12, res_p_13)
    res_15 = __phi(_cond_10, res_11, res_14)
    res_p_15 = __phi(_cond_10, res_p_11, res_p_14)
    res_16 = __phi(_cond_11, res_10, res_15)
    res_p_16 = __phi(_cond_11, res_p_10, res_p_15)
    res_17 = __phi(_cond_12, res_9, res_16)
    res_p_17 = __phi(_cond_12, res_p_9, res_p_16)
    res_18 = __phi(_cond_13, res_8, res_17)
    res_p_18 = __phi(_cond_13, res_p_8, res_p_17)
    res_19 = __phi(_cond_14, res_7, res_18)
    res_p_19 = __phi(_cond_14, res_p_7, res_p_18)
    res_20 = __phi(_cond_15, res_6, res_19)
    res_p_20 = __phi(_cond_15, res_p_6, res_p_19)
    res_21 = __phi(_cond_16, res_5, res_20)
    res_p_21 = __phi(_cond_16, res_p_5, res_p_20)
    res_22 = __phi(_cond_17, res_4, res_21)
    res_p_22 = __phi(_cond_17, res_p_4, res_p_21)
    C_5 = __phi(_cond_18, C_4, C_0)
    V_5 = __phi(_cond_18, V_4, V_0)
    res_23 = __phi(_cond_18, res_3, res_22)
    res_p_23 = __phi(_cond_18, res_p_3, res_p_22)
    C_6 = __phi(_cond_19, C_3, C_5)
    V_6 = __phi(_cond_19, V_3, V_5)
    res_24 = __phi(_cond_19, res_2, res_23)
    res_p_24 = __phi(_cond_19, res_p_2, res_p_23)
    C_7 = __phi(_cond_20, C_2, C_6)
    V_7 = __phi(_cond_20, V_2, V_6)
    res_25 = __phi(_cond_20, res_1, res_24)
    res_p_25 = __phi(_cond_20, res_p_1, res_p_24)
    C_8 = __phi(_cond_21, C_1, C_7)
    V_8 = __phi(_cond_21, V_1, V_7)
    res_26 = __phi(_cond_21, res_0, res_25)
    res_p_26 = __phi(_cond_21, res_p_0, res_p_25)

    N_0 = Bit(res_26[-1])
    Z_0 = res_26 == SData(0)

    __0_return_0 = res_26, res_p_26, Z_0, N_0, C_8, V_8
    return __0_return_0
