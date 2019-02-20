import magma as m
from bit_vector import BitVector
from common.configurable_model import ConfigurableModel
import fault


def gen_simple_pe(ops: list, data_width: int = 16):
    CONFIG_DATA_WIDTH = m.bitutils.clog2(len(ops))
    CONFIG_ADDR_WIDTH = 1
    CONFIG_ADDR = BitVector(0, CONFIG_ADDR_WIDTH)

    ParentCls = ConfigurableModel(CONFIG_DATA_WIDTH, CONFIG_ADDR_WIDTH)

    class _SimplePE(ParentCls):
        def __init__(self):
            super().__init__()
            self.ops = ops
            self.reset()

        def reset(self):
            self.O = fault.UnknownValue
            self.read_data = fault.UnknownValue
            self.configure(CONFIG_ADDR, BitVector(0, CONFIG_DATA_WIDTH))

        def configure(self, addr, data):
            self.config[addr] = data

        def __call__(self, I0, I1):
            select = self.config[CONFIG_ADDR]
            self.O = self.ops[select.as_uint()](I0, I1)
            return self.O

    return _SimplePE
