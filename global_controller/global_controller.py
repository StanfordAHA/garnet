from common.model import Model
from bit_vector import BitVector
from enum import Enum
import magma as m


class GC_reg_addr(Enum):
    TST_addr = 0
    stall_addr = 1
    


def gen_global_controller(config_data_width: int,
                          config_addr_width: int,
                          config_op_width: int):

    class GlobalController(Model()):
        def __init__(self):
            super().__init__()
            self.reset()

        def reset(self):
            self.TST = BitVector(0, config_data_width)
            # There are 4 stall domains.
            # Should parametrize this in the RTL
            self.stall = BitVector(0, 4)
            # 0: slow JTAG clk, 1: fast sys_clk
            self.clock_sel = BitVector(0, 1)
            self.reset_out = BitVector(0, 1)
            self.config_addr_out = BitVector(0, config_addr_width)
            self.config_data_out = BitVector(0, config_data_width)
            self.read = BitVector(0, 1)
            self.write = BitVector(0, 1)
            self.rw_delay_sel = BitVector(config_data_width, 2)
            self.clk_switch_delay_sel = BitVector(0, 2)

        def config_read(self, addr):
            self.read = 1
            self.write = 0
            self.config_addr_out = addr

        def config_write(self, addr, data):
            self.read = 0
            self.write = 1
            self.config_addr_out = addr
            self.config_data_out = data

        def clock_switch(self, data):
            raise NotImplementedError()

        def read_GC_reg(self, addr):
            raise NotImplementedError()
  
        def write_GC_reg(self, addr, data):
            raise NotImplementedError()

        def __call__(self, *args, **kwargs):
            raise NotImplementedError()
