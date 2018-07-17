import random
from bit_vector import BitVector
from common.configurable_model import ConfigurableModel


def test_configurable_model_smoke():
    EXPECTED_MSG = "TypeError(\"Can't instantiate abstract class _ConfigurableModel with abstract methods __call__\",)"  # nopep8
    has_type_error = False
    try:
        my_model = ConfigurableModel(32, 32)()
    except TypeError as e:
        msg = e.__repr__()
        has_type_error = True
    assert has_type_error
    assert msg == EXPECTED_MSG


def test_configurable_model_subclass():
    def value(v):
        return BitVector(v, 32)

    class Foo(ConfigurableModel(32, 32)):
        def __init__(self):
            super().__init__()

        def __call__(self):
            return 0

    f = Foo()
    addr = value(random.randint(0, 2**32 - 1))
    data = value(random.randint(0, 2**32 - 1))
    f.configure(addr, data)
    assert f.read_config(addr) == data
    assert f() == 0
