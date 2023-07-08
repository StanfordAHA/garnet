def __call__(
    self, mode: Mode_t, const_: T, value: T, clk_en: Bit
) -> (T, T):
    _cond_0 = mode == Mode_t.DELAY
    data_0, en_0 = value, clk_en
    data_1, en_1 = value, Bit(0)
    data_2 = __phi(_cond_0, data_0, data_1)
    en_2 = __phi(_cond_0, en_0, en_1)

    reg_val_0 = self.register(data_2, en_2)
    _cond_2 = mode == Mode_t.CONST
    __0_return_0 = const_, reg_val_0
    _cond_1 = mode == Mode_t.BYPASS
    __0_return_1 = value, reg_val_0
    __0_return_2 = reg_val_0, reg_val_0
    return __phi(_cond_2, __0_return_0, __phi(_cond_1, __0_return_1, __0_return_2))
