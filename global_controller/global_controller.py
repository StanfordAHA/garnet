from common.model import Model
from bit_vector import BitVector
from enum import Enum
import magma as m


class GC_reg_addr(Enum):
    TST_addr = 0
    stall_addr = 1
    clk_sel_addr = 2
    rw_delay_sel_addr = 3
    clk_switch_delay_sel_addr = 4


def gen_global_controller(config_data_width: int,
                          config_addr_width: int,
                          config_op_width: int):

    class GlobalController(Model()):
        def __init__(self):
            super().__init__()
            self.NUM_STALL_DOMAINS = 4
            self.reset()

        def reset(self):
            self.regs = {GC_reg_addr.TST_addr: BitVector(0, config_data_width),
                         GC_reg_addr.stall_addr: BitVector(0,
                         self.NUM_STALL_DOMAINS),
                         GC_reg_addr.clk_sel_addr: BitVector(0, 1),
                         GC_reg_addr.rw_delay_sel_addr:
                         BitVector(0, config_data_width),
                         GC_reg_addr.clk_switch_delay_sel_addr:
                         BitVector(0, 1)}
            self.reset_out = BitVector(0, 1)
            self.config_addr_out = BitVector(0, config_addr_width)
            self.config_data_out = BitVector(0, config_data_width)
            self.read = BitVector(0, 1)
            self.write = BitVector(0, 1)

        def config_read(self, addr):
            self.read = 1
            self.write = 0
            self.config_addr_out = addr

        def config_write(self, addr, data):
            self.read = 0
            self.write = 1
            self.config_addr_out = addr
            self.config_data_out = data

        def read_GC_reg(self, addr):
            self.config_data_to_jtag = BitVector(self.regs[addr]._value,
                                                 config_data_width)

        def write_GC_reg(self, addr, data: BitVector):
            reg_width = self.regs[addr].num_bits
            self.regs[addr] = BitVector(data._value, reg_width)

        def advance_clk(self, addr: BitVector):
            raise NotImplementedError()

        def global_reset(self, data: BitVector):
            raise NotImplementedError()

        def __call__(self, *args, **kwargs):
            raise NotImplementedError()
