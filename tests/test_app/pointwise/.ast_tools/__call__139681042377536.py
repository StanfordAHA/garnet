def __call__(self, value: T, en: family.Bit) -> T:
    _attr_self_value_0 = self.value
    assert value is not None
    retvalue_0 = _attr_self_value_0
    _cond_0 = en
    _attr_self_value_1 = value
    _attr_self_value_2 = __phi(_cond_0, _attr_self_value_1, _attr_self_value_0)
    __0_final_self_value_0 = _attr_self_value_2; __0_return_0 = retvalue_0
    self.value = __0_final_self_value_0
    return __0_return_0
