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


class GlobalController:
    def __init__(self, config_addr_width, config_data_width, config_op_width,
                 num_analog_regs):
        self.config_addr_width = config_addr_width
        self.config_data_width = config_data_width
        self.config_op_width = config_op_width
        self.num_analog_regs = num_analog_regs
