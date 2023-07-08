@name_outputs(res=Data, N=Bit, Z=Bit)
def __call__(self, fpu_op: Const(FPU_t), a: Data, b: Data) -> (Data, Bit, Bit):

    a_inf_0 = fp_is_inf(a)
    b_inf_0 = fp_is_inf(b)
    a_neg_0 = fp_is_neg(a)
    b_neg_0 = fp_is_neg(b)

    neg_b_0 = (fpu_op == FPU_t.FP_sub) | (fpu_op == FPU_t.FP_cmp)
    _cond_0 = neg_b_0
    b_0 = b ^ (2 ** (16 - 1))
    b_1 = __phi(_cond_0, b_0, b)
    Add_val_0 = self.Add(a, b_1)
    Mul_val_0 = self.Mul(a, b_1)
    _cond_1 = (
        (fpu_op == FPU_t.FP_add)
        | (fpu_op == FPU_t.FP_sub)
        | (fpu_op == FPU_t.FP_cmp)
    )
    res_0 = Add_val_0
    res_1 = Mul_val_0
    res_2 = __phi(_cond_1, res_0, res_1)

    Z_0 = fp_is_zero(res_2)
    _cond_3 = fpu_op == FPU_t.FP_cmp
    _cond_2 = (a_inf_0 & b_inf_0) & (a_neg_0 == b_neg_0)
    Z_1 = family.Bit(1)
    Z_2 = __phi(_cond_2, Z_1, Z_0)
    Z_3 = __phi(_cond_3, Z_2, Z_0)

    N_0 = family.Bit(res_2[-1])
    __0_return_0 = res_2, N_0, Z_3
    return __0_return_0
