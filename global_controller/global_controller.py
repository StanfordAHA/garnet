from common.model import Model
from bit_vector import BitVector
from enum import Enum
import magma as m


class opcode(Enum):
    NOP = 0
    write_config = 1
    read_config = 2
    write_A050 = 7
    write_TST = 8
    read_TST = 9
    global_reset = 10
    write_stall = 11
    read_stall = 12
    advance_clk = 13
    read_clk_domain = 14
    switch_clk = 15
    wr_rd_delay_reg = 16
    rd_rd_delay_reg = 17
    wr_delay_sel_reg = 18
    rd_delay_sel_reg = 19
    wr_analog_reg = 20
    rd_analog_reg = 21


def gen_global_controller(config_data_width: int,
                          config_addr_width: int,
                          config_op_width: int,
                          num_analog_regs: int):

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

        def config_read(self, addr):
            self.read = 1
            self.write = 0
            self.config_addr_out = addr

        def config_write(self, addr, data):
            self.read = 0
            self.write = 1
            self.config_addr_out = addr
            self.config_data_out = data

        def __call__(self, *args, **kwargs):
            raise NotImplementedError()
