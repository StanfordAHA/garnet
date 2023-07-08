@name_outputs(res=Data, res_p=Bit, V=Bit)
def __call__(
    self, op: Const(FPCustom_t), signed_: Const(Signed_t), a: Data, b: Data
) -> (Data, Bit, Bit):
    _cond_27 = op == FPCustom_t.FCnvExp2F
    expa0_0 = BitVector[8](a[7:15])
    biased_exp0_0 = SInt[9](expa0_0.zext(1))
    unbiased_exp0_0 = SInt[9](biased_exp0_0 - SInt[9](127))
    _cond_0 = unbiased_exp0_0 < 0
    sign_0 = BitVector[16](0x8000)
    abs_exp0_0 = -unbiased_exp0_0
    sign_1 = BitVector[16](0x0000)
    abs_exp0_1 = unbiased_exp0_0
    abs_exp0_2 = __phi(_cond_0, abs_exp0_0, abs_exp0_1)
    sign_2 = __phi(_cond_0, sign_0, sign_1)
    abs_exp_0 = BitVector[8](abs_exp0_2[0:8])
    scale_0 = SInt[16](-127)
    _cond_1 = abs_exp_0[0] == Bit(1)
    scale_1 = SInt[16](0)
    scale_2 = __phi(_cond_1, scale_1, scale_0)
    _cond_2 = abs_exp_0[1] == Bit(1)
    scale_3 = SInt[16](1)
    scale_4 = __phi(_cond_2, scale_3, scale_2)
    _cond_3 = abs_exp_0[2] == Bit(1)
    scale_5 = SInt[16](2)
    scale_6 = __phi(_cond_3, scale_5, scale_4)
    _cond_4 = abs_exp_0[3] == Bit(1)
    scale_7 = SInt[16](3)
    scale_8 = __phi(_cond_4, scale_7, scale_6)
    _cond_5 = abs_exp_0[4] == Bit(1)
    scale_9 = SInt[16](4)
    scale_10 = __phi(_cond_5, scale_9, scale_8)
    _cond_6 = abs_exp_0[5] == Bit(1)
    scale_11 = SInt[16](5)
    scale_12 = __phi(_cond_6, scale_11, scale_10)
    _cond_7 = abs_exp_0[6] == Bit(1)
    scale_13 = SInt[16](6)
    scale_14 = __phi(_cond_7, scale_13, scale_12)
    _cond_8 = abs_exp_0[7] == Bit(1)
    scale_15 = SInt[16](7)
    scale_16 = __phi(_cond_8, scale_15, scale_14)
    normmant_mul_left_0 = SInt[16](abs_exp_0)
    normmant_mul_right_0 = SInt[16](7) - scale_16
    normmant_mask_0 = SInt[16](0x7F)
    _cond_9 = signed_ == Signed_t.signed
    sign_3 = BitVector[16](a & 0x8000)
    sign_4 = BitVector[16](0)
    sign_5 = __phi(_cond_9, sign_3, sign_4)
    _cond_10 = sign_5[15] == Bit(1)
    abs_input_0 = BitVector[16](-SInt[16](a))
    abs_input_1 = BitVector[16](a)
    abs_input_2 = __phi(_cond_10, abs_input_0, abs_input_1)
    scale_17 = SInt[16](-127)
    _cond_11 = abs_input_2[0] == Bit(1)
    scale_18 = SInt[16](0)
    scale_19 = __phi(_cond_11, scale_18, scale_17)
    _cond_12 = abs_input_2[1] == Bit(1)
    scale_20 = SInt[16](1)
    scale_21 = __phi(_cond_12, scale_20, scale_19)
    _cond_13 = abs_input_2[2] == Bit(1)
    scale_22 = SInt[16](2)
    scale_23 = __phi(_cond_13, scale_22, scale_21)
    _cond_14 = abs_input_2[3] == Bit(1)
    scale_24 = SInt[16](3)
    scale_25 = __phi(_cond_14, scale_24, scale_23)
    _cond_15 = abs_input_2[4] == Bit(1)
    scale_26 = SInt[16](4)
    scale_27 = __phi(_cond_15, scale_26, scale_25)
    _cond_16 = abs_input_2[5] == Bit(1)
    scale_28 = SInt[16](5)
    scale_29 = __phi(_cond_16, scale_28, scale_27)
    _cond_17 = abs_input_2[6] == Bit(1)
    scale_30 = SInt[16](6)
    scale_31 = __phi(_cond_17, scale_30, scale_29)
    _cond_18 = abs_input_2[7] == Bit(1)
    scale_32 = SInt[16](7)
    scale_33 = __phi(_cond_18, scale_32, scale_31)
    _cond_19 = abs_input_2[8] == Bit(1)
    scale_34 = SInt[16](8)
    scale_35 = __phi(_cond_19, scale_34, scale_33)
    _cond_20 = abs_input_2[9] == Bit(1)
    scale_36 = SInt[16](9)
    scale_37 = __phi(_cond_20, scale_36, scale_35)
    _cond_21 = abs_input_2[10] == Bit(1)
    scale_38 = SInt[16](10)
    scale_39 = __phi(_cond_21, scale_38, scale_37)
    _cond_22 = abs_input_2[11] == Bit(1)
    scale_40 = SInt[16](11)
    scale_41 = __phi(_cond_22, scale_40, scale_39)
    _cond_23 = abs_input_2[12] == Bit(1)
    scale_42 = SInt[16](12)
    scale_43 = __phi(_cond_23, scale_42, scale_41)
    _cond_24 = abs_input_2[13] == Bit(1)
    scale_44 = SInt[16](13)
    scale_45 = __phi(_cond_24, scale_44, scale_43)
    _cond_25 = abs_input_2[14] == Bit(1)
    scale_46 = SInt[16](14)
    scale_47 = __phi(_cond_25, scale_46, scale_45)
    _cond_26 = abs_input_2[15] == Bit(1)
    scale_48 = SInt[16](15)
    scale_49 = __phi(_cond_26, scale_48, scale_47)
    normmant_mul_left_1 = SInt[16](abs_input_2)
    normmant_mul_right_1 = SInt[16](15) - scale_49
    normmant_mask_1 = SInt[16](0x7F00)
    normmant_mask_2 = __phi(_cond_27, normmant_mask_0, normmant_mask_1)
    normmant_mul_left_2 = __phi(_cond_27, normmant_mul_left_0, normmant_mul_left_1)
    normmant_mul_right_2 = __phi(_cond_27, normmant_mul_right_0, normmant_mul_right_1)
    scale_50 = __phi(_cond_27, scale_16, scale_49)
    sign_6 = __phi(_cond_27, sign_2, sign_5)
    _cond_28 = scale_50 >= 0
    normmant_0 = BitVector[16](
        (normmant_mul_left_2 << normmant_mul_right_2) & normmant_mask_2
    )
    normmant_1 = BitVector[16](0)
    normmant_2 = __phi(_cond_28, normmant_0, normmant_1)
    _cond_29 = op == FPCustom_t.FCnvInt2F
    normmant_3 = BitVector[16](normmant_2) >> 8
    normmant_4 = __phi(_cond_29, normmant_3, normmant_2)

    biased_scale_0 = scale_50 + 127
    to_float_result_0 = (
        sign_6 | ((BitVector[16](biased_scale_0) << 7) & (0xFF << 7)) | normmant_4
    )

    V_0 = Bit(0)
    _cond_39 = op == FPCustom_t.FGetMant
    res_0, res_p_0 = (a & 0x7F), Bit(0)
    _cond_38 = op == FPCustom_t.FAddIExp
    sign_7 = BitVector[16]((a & 0x8000))
    exp_0 = UData(a)[7:15]
    exp_check_0 = exp_0.zext(1)
    exp_1 = exp_0 + UData(b)[0:8]
    exp_check_1 = exp_check_0 + UData(b)[0:9]
    # Augassign not supported by magma yet
    # exp += SInt[8](b[0:8])
    # exp_check += SInt[9](b[0:9])
    exp_shift_0 = BitVector[16](exp_1)
    exp_shift_1 = exp_shift_0 << 7
    mant_0 = BitVector[16]((a & 0x7F))
    res_1, res_p_1 = (sign_7 | exp_shift_1 | mant_0), (exp_check_1 > 255)
    _cond_37 = op == FPCustom_t.FSubExp
    signa_0 = BitVector[16]((a & 0x8000))
    expa_0 = UData(a)[7:15]
    signb_0 = BitVector[16]((b & 0x8000))
    expb_0 = UData(b)[7:15]
    expa_1 = expa_0 - expb_0 + 127
    exp_shift_2 = BitVector[16](expa_1)
    exp_shift_3 = exp_shift_2 << 7
    manta_0 = BitVector[16]((a & 0x7F))
    res_2, res_p_2 = ((signa_0 | signb_0) | exp_shift_3 | manta_0), Bit(0)
    _cond_36 = op == FPCustom_t.FCnvExp2F
    res_3, res_p_3 = to_float_result_0, Bit(0)
    _cond_35 = op == FPCustom_t.FGetFInt
    signa_1 = BitVector[16]((a & 0x8000))
    manta_1 = BitVector[16]((a & 0x7F)) | 0x80
    expa0_1 = UData(a)[7:15]
    biased_exp0_1 = SInt[9](expa0_1.zext(1))
    unbiased_exp0_1 = SInt[9](biased_exp0_1 - SInt[9](127))
    _cond_30 = unbiased_exp0_1 < 0
    manta_shift0_0 = BitVector[23](0)
    manta_shift0_1 = BitVector[23](manta_1) << BitVector[23](unbiased_exp0_1)
    manta_shift0_2 = __phi(_cond_30, manta_shift0_0, manta_shift0_1)
    unsigned_res0_0 = BitVector[23](manta_shift0_2 >> BitVector[23](7))
    unsigned_res_0 = BitVector[16](unsigned_res0_0[0:16])
    _cond_31 = signa_1 == 0x8000
    signed_res_0 = -SInt[16](unsigned_res_0)
    signed_res_1 = SInt[16](unsigned_res_0)
    signed_res_2 = __phi(_cond_31, signed_res_0, signed_res_1)
    # We are not checking for overflow when converting to int
    res_4, res_p_4, V_1 = signed_res_2, Bit(0), (expa0_1 > BitVector[8](142))
    _cond_34 = op == FPCustom_t.FGetFFrac
    signa_2 = BitVector[16]((a & 0x8000))
    manta_2 = BitVector[16]((a & 0x7F)) | 0x80
    expa0_2 = BitVector[8](a[7:15])
    biased_exp0_2 = SInt[9](expa0_2.zext(1))
    unbiased_exp0_2 = SInt[9](biased_exp0_2 - SInt[9](127))
    _cond_32 = unbiased_exp0_2 < 0
    manta_shift1_0 = BitVector[16](manta_2) >> BitVector[16](-unbiased_exp0_2)
    manta_shift1_1 = BitVector[16](manta_2) << BitVector[16](unbiased_exp0_2)
    manta_shift1_2 = __phi(_cond_32, manta_shift1_0, manta_shift1_1)
    unsigned_res_1 = BitVector[16]((manta_shift1_2 & 0x07F))
    _cond_33 = signa_2 == 0x8000
    signed_res_3 = -SInt[16](unsigned_res_1)
    signed_res_4 = SInt[16](unsigned_res_1)
    signed_res_5 = __phi(_cond_33, signed_res_3, signed_res_4)

    # We are not checking for overflow when converting to int
    res_5, res_p_5 = signed_res_5, Bit(0)
    res_6, res_p_6 = to_float_result_0, Bit(0)
    biased_exp0_3 = __phi(_cond_34, biased_exp0_2, biased_exp0_0)
    expa0_3 = __phi(_cond_34, expa0_2, expa0_0)
    res_7 = __phi(_cond_34, res_5, res_6)
    res_p_7 = __phi(_cond_34, res_p_5, res_p_6)
    unbiased_exp0_3 = __phi(_cond_34, unbiased_exp0_2, unbiased_exp0_0)
    V_2 = __phi(_cond_35, V_1, V_0)
    biased_exp0_4 = __phi(_cond_35, biased_exp0_1, biased_exp0_3)
    expa0_4 = __phi(_cond_35, expa0_1, expa0_3)
    manta_3 = __phi(_cond_35, manta_1, manta_2)
    res_8 = __phi(_cond_35, res_4, res_7)
    res_p_8 = __phi(_cond_35, res_p_4, res_p_7)
    signa_3 = __phi(_cond_35, signa_1, signa_2)
    signed_res_6 = __phi(_cond_35, signed_res_2, signed_res_5)
    unbiased_exp0_4 = __phi(_cond_35, unbiased_exp0_1, unbiased_exp0_3)
    unsigned_res_2 = __phi(_cond_35, unsigned_res_0, unsigned_res_1)
    V_3 = __phi(_cond_36, V_0, V_2)
    biased_exp0_5 = __phi(_cond_36, biased_exp0_0, biased_exp0_4)
    expa0_5 = __phi(_cond_36, expa0_0, expa0_4)
    res_9 = __phi(_cond_36, res_3, res_8)
    res_p_9 = __phi(_cond_36, res_p_3, res_p_8)
    unbiased_exp0_5 = __phi(_cond_36, unbiased_exp0_0, unbiased_exp0_4)
    V_4 = __phi(_cond_37, V_0, V_3)
    biased_exp0_6 = __phi(_cond_37, biased_exp0_0, biased_exp0_5)
    expa0_6 = __phi(_cond_37, expa0_0, expa0_5)
    manta_4 = __phi(_cond_37, manta_0, manta_3)
    res_10 = __phi(_cond_37, res_2, res_9)
    res_p_10 = __phi(_cond_37, res_p_2, res_p_9)
    signa_4 = __phi(_cond_37, signa_0, signa_3)
    unbiased_exp0_6 = __phi(_cond_37, unbiased_exp0_0, unbiased_exp0_5)
    V_5 = __phi(_cond_38, V_0, V_4)
    biased_exp0_7 = __phi(_cond_38, biased_exp0_0, biased_exp0_6)
    exp_shift_4 = __phi(_cond_38, exp_shift_1, exp_shift_3)
    expa0_7 = __phi(_cond_38, expa0_0, expa0_6)
    res_11 = __phi(_cond_38, res_1, res_10)
    res_p_11 = __phi(_cond_38, res_p_1, res_p_10)
    sign_8 = __phi(_cond_38, sign_7, sign_6)
    unbiased_exp0_7 = __phi(_cond_38, unbiased_exp0_0, unbiased_exp0_6)
    V_6 = __phi(_cond_39, V_0, V_5)
    biased_exp0_8 = __phi(_cond_39, biased_exp0_0, biased_exp0_7)
    expa0_8 = __phi(_cond_39, expa0_0, expa0_7)
    res_12 = __phi(_cond_39, res_0, res_11)
    res_p_12 = __phi(_cond_39, res_p_0, res_p_11)
    sign_9 = __phi(_cond_39, sign_6, sign_8)
    unbiased_exp0_8 = __phi(_cond_39, unbiased_exp0_0, unbiased_exp0_7)

    __0_return_0 = res_12, res_p_12, V_6
    return __0_return_0
