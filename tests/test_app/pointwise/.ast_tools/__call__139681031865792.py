@name_outputs(
    res=DataPy,
    res_p=BitPy,
    reg0_config_data=DataPy,
    reg1_config_data=DataPy,
    reg2_config_data=DataPy,
)
def __call__(
    self,
    inst: Const(Inst),
    data0: DataPy = Data(0),
    data1: DataPy = Data(0),
    data2: DataPy = Data(0),
    bit0: BitPy = Bit(0),
    bit1: BitPy = Bit(0),
    bit2: BitPy = Bit(0),
    clk_en: Global(BitPy) = Bit(1),
) -> (DataPy, BitPy, DataPy, DataPy, DataPy):

    ra_0, ra_rdata_0 = self.rega(inst.rega, inst.data0, data0, clk_en)
    rb_0, rb_rdata_0 = self.regb(inst.regb, inst.data1, data1, clk_en)
    rc_0, rc_rdata_0 = self.regc(inst.regc, inst.data2, data2, clk_en)

    rd_0, rd_rdata_0 = self.regd(inst.regd, inst.bit0, bit0, clk_en)
    re_0, re_rdata_0 = self.rege(inst.rege, inst.bit1, bit1, clk_en)
    rf_0, rf_rdata_0 = self.regf(inst.regf, inst.bit2, bit2, clk_en)

    # set default values to each of the op kinds
    alu_op_0 = ALU_t_c(ALU_t.Adc)
    fpu_op_0 = FPU_t_c(FPU_t.FP_add)
    fp_custom_op_0 = FPCustom_t_c(FPCustom_t.FGetMant)
    _cond_1 = inst.op.alu.match
    alu_op_1 = inst.op.alu.value
    _cond_0 = inst.op.fpu.match
    fpu_op_1 = inst.op.fpu.value
    fp_custom_op_1 = inst.op.fp_custom.value
    fp_custom_op_2 = __phi(_cond_0, fp_custom_op_0, fp_custom_op_1)
    fpu_op_2 = __phi(_cond_0, fpu_op_1, fpu_op_0)
    alu_op_2 = __phi(_cond_1, alu_op_1, alu_op_0)
    fp_custom_op_3 = __phi(_cond_1, fp_custom_op_0, fp_custom_op_2)
    fpu_op_3 = __phi(_cond_1, fpu_op_0, fpu_op_2)

    # calculate alu results
    alu_res_0, alu_res_p_0, alu_Z_0, alu_N_0, C_0, alu_V_0 = self.alu(
        alu_op_2, inst.signed, ra_0, rb_0, rc_0, rd_0
    )

    fpu_res_0, fpu_N_0, fpu_Z_0 = self.fpu(fpu_op_3, ra_0, rb_0)

    fpc_res_0, fpc_res_p_0, fpc_V_0 = self.fp_custom(
        fp_custom_op_3, inst.signed, ra_0, rb_0
    )

    Z_0 = Bit(0)
    N_0 = Bit(0)
    V_0 = Bit(0)
    res_p_0 = Bit(0)
    res_0 = Data(0)
    _cond_3 = inst.op.alu.match
    Z_1 = alu_Z_0
    N_1 = alu_N_0
    V_1 = alu_V_0
    res_p_1 = alu_res_p_0
    res_1 = alu_res_0
    _cond_2 = inst.op.fpu.match
    N_2 = fpu_N_0
    Z_2 = fpu_Z_0
    res_2 = fpu_res_0
    V_2 = fpc_V_0
    res_p_2 = fpc_res_p_0
    res_3 = fpc_res_0
    N_3 = __phi(_cond_2, N_2, N_0)
    V_3 = __phi(_cond_2, V_0, V_2)
    Z_3 = __phi(_cond_2, Z_2, Z_0)
    res_4 = __phi(_cond_2, res_2, res_3)
    res_p_3 = __phi(_cond_2, res_p_0, res_p_2)
    N_4 = __phi(_cond_3, N_1, N_3)
    V_4 = __phi(_cond_3, V_1, V_3)
    Z_4 = __phi(_cond_3, Z_1, Z_3)
    res_5 = __phi(_cond_3, res_1, res_4)
    res_p_4 = __phi(_cond_3, res_p_1, res_p_3)

    # calculate lut results
    lut_res_0 = self.lut(inst.lut, rd_0, re_0, rf_0)

    # calculate 1-bit result
    cond_0 = self.cond(inst.cond, res_p_4, lut_res_0, Z_4, N_4, C_0, V_4)

    # return 16-bit result, 1-bit result
    __0_return_0 = res_5, cond_0, ra_rdata_0, rb_rdata_0, rc_rdata_0
    return __0_return_0
