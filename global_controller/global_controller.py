from common.model import Model
from bit_vector import BitVector
from enum import Enum
import magma as m


class State(Enum):
    READY = 0
    READING = 1
    RESETTING = 2
    ADVANCING_CLK = 3
    SWITCHING_CLK = 4


def gen_global_controller(config_data_with: int,
                          config_addr_width: int,
                          config_op_with: int,
                          num_analog_regs: int):
    CONFIG_ADDR_WIDTH = 32
    CONFIG_DATA_WIDTH = 32
    CONFIG_OP_WIDTH = 5

    class GlobalController(Model()):
        def __init__(self):
            super().__init__()
            self.reset()

        def reset(self):
            self.config_addr_out = None
            self.config_data_out = None
            self.read = None
            self.write = None
            self.cgra_stalled = None
            self.reset_out = 1
            self.state = State.READY

        def config_read(self, addr):
            if (self.state == State.READY):
                self.read = 1
                self.write = 0
                self.config_addr_out = addr

        def config_write(self, addr, data):
            if (self.state == State.READY):
                self.read = 0
                self.write = 1
                self.config_addr_out = addr
                self.config_data_out = data

        def __call__(self, *args, **kwargs):
            raise NotImplementedError()
