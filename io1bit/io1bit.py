import math
from bit_vector import BitVector
from common.configurable_model import ConfigurableModel
import fault


def gen_io1bit():
    CONFIG_ADDR_WIDTH = 32
    CONFIG_DATA_WIDTH = 32
    CONFIG_ADDR = BitVector(0, CONFIG_ADDR_WIDTH)

    ParentCls = ConfigurableModel(CONFIG_DATA_WIDTH, CONFIG_ADDR_WIDTH)

    class _IO1Bit(ParentCls):
        def __init__(self):
            super().__init__()
            self.reset()

        def reset(self):
            self.pad = fault.UnknownValue
            self.p2f = fault.UnknownValue
            self.read_config_data = fault.UnknownValue
            self.configure(CONFIG_ADDR, BitVector(0, 32))

        def configure(self, addr, data):
            self.config[addr] = data

        def config_read(self, addr):
            if(addr == CONFIG_ADDR):
                self.read_data = self.config[addr]
            else:
                self.read_data = BitVector(0, 32)

        def __call__(self, pad, f2p_16, f2p_1):
            select = self.config[CONFIG_ADDR]
            in_out = select[0]
            bus16_bus1 = select[1]
            if in_out == 0:
                self.p2f = pad
                return self.p2f
            elif bus16_bus1 == 0:
                self.pad = f2p_16
                return self.pad
            else:
                self.pad = f2p_1
                return self.pad

    return _IO1Bit
