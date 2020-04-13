from gemstone.common.configurable_model import ConfigurableModel
from hwtypes import BitVector
from enum import Enum
import magma as m
import fault


class GCRegAddr(Enum):
    TST_ADDR = 0
    STALL_ADDR = 1
    CLK_SEL_ADDR = 2
    RW_DELAY_SEL_ADDR = 3
    CLK_SWITCH_DELAY_SEL_ADDR = 4


class GCOp(Enum):
    NOP = 0
    CONFIG_WRITE = 1
    CONFIG_READ = 2
    WRITE_A050 = 4
    WRITE_TST = 5
    READ_TST = 6
    GLOBAL_RESET = 7
    WRITE_STALL = 8
    READ_STALL = 9
    ADVANCE_CLK = 10
    READ_CLK_DOMAIN = 11
    SWITCH_CLK = 12
    WRITE_RW_DELAY_SEL = 13
    READ_RW_DELAY_SEL = 14
    WRITE_CLK_SWITCH_DELAY_SEL = 15
    READ_CLK_SWITCH_DELAY_SEL = 16


def gen_global_controller(config_data_width: int,
                          config_addr_width: int,
                          config_op_width: int):

    class _GlobalController(ConfigurableModel(32, 32)):
        def __init__(self):
            super().__init__()
            self.num_stall_domains = 4
            self.reset()

        def reset(self):
            self.TST = [BitVector[config_data_width](0)]
            self.stall = [BitVector[self.num_stall_domains](0)]
            self.clk_sel = [BitVector[1](0)]
            self.rw_delay_sel = [BitVector[config_data_width](2)]
            self.clk_switch_delay_sel = [BitVector[1](0)]

            self.reset_out = [0]
            self.config_addr_out = [BitVector[config_addr_width](0)]
            self.config_data_out = [BitVector[config_data_width](0)]
            self.config_data_in = fault.UnknownValue
            self.read = [0]
            self.write = [0]
            self.config_data_to_jtag = [BitVector[config_data_width](0)]

        def config_read(self, addr):
            rw_delay = self.rw_delay_sel[0]
            duration = rw_delay.as_uint()
            self.read = [1] * duration + [0]
            self.write = [0] * (duration + 1)
            self.config_addr_out = [BitVector[config_addr_width](addr)] \
                * (duration + 1)
            self.config_data_to_jtag = [self.config_data_to_jtag[-1]] \
                + [self.config_data_in] * duration

        def config_write(self, addr, data):
            rw_delay = self.rw_delay_sel[0]
            duration = rw_delay.as_uint()
            self.read = [0] * (duration + 1)
            self.write = [1] * duration + [0]
            self.config_addr_out = [BitVector[config_addr_width](addr)] \
                * (duration + 1)
            self.config_data_out = [BitVector[config_data_width](data)] \
                * (duration + 1)

        def read_gc_reg(self, addr):
            if (addr == GCRegAddr.TST_ADDR):
                out = self.TST[-1]
            elif (addr == GCRegAddr.STALL_ADDR):
                out = self.stall[-1]
            elif (addr == GCRegAddr.CLK_SEL_ADDR):
                out = self.clk_sel[-1]
            elif (addr == GCRegAddr.RW_DELAY_SEL_ADDR):
                out = self.rw_delay_sel[-1]
            elif (addr == GCRegAddr.CLK_SWITCH_DELAY_SEL_ADDR):
                out = self.clk_switch_delay_sel[-1]
            else:
                raise ValueError("Reading from invalid GC_reg address")
            self.config_data_to_jtag = [BitVector[config_data_width](out)]

        def write_gc_reg(self, addr, data):
            if (addr == GCRegAddr.TST_ADDR):
                self.TST = [BitVector[config_data_width](data)]
            elif (addr == GCRegAddr.STALL_ADDR):
                self.stall = [BitVector[self.num_stall_domains](data)]
            elif (addr == GCRegAddr.CLK_SEL_ADDR):
                self.clk_sel = [BitVector[1](data)]
            elif (addr == GCRegAddr.RW_DELAY_SEL_ADDR):
                self.rw_delay_sel = [BitVector[config_data_width](data)]
            elif (addr == GCRegAddr.CLK_SWITCH_DELAY_SEL_ADDR):
                self.clk_switch_delay_sel = [BitVector[1](data)]
            else:
                raise ValueError("Writing to invalid GC_reg address")

        def global_reset(self, data):
            if (data > 0):
                self.reset_out = [1] * data + [0]
            else:
                self.reset_out = [1] * 20 + [0]

        def wr_A050(self):
            self.config_data_to_jtag = [BitVector[config_data_width](0xA050)]

        def advance_clk(self, addr, data):
            save_stall_reg = self.stall[-1]
            temp_stall_reg = BitVector[self.num_stall_domains](0)
            mask = BitVector[self.num_stall_domains](addr)
            for i in range(self.num_stall_domains):
                if (mask[i] == 1):
                    temp_stall_reg[i] = 0
            self.stall = [temp_stall_reg] * data + [save_stall_reg]

        def set_config_data_in(self, data):
            self.config_data_in = BitVector[config_data_width](data)

        def __cleanup(self):
            # Remove sequences from outputs/regs in preparation for the next
            # op.
            self.stall = [self.stall[-1]]
            self.config_addr_out = [self.config_addr_out[-1]]
            self.config_data_out = [self.config_data_out[-1]]
            self.read = [self.read[-1]]
            self.write = [self.write[-1]]
            self.config_data_to_jtag = [self.config_data_to_jtag[-1]]

        def __call__(self, **kwargs):
            self.__cleanup()
            # Op is mandatory. Other args are optional
            op = kwargs['op']
            if 'data' in kwargs:
                data = kwargs['data']
            if 'addr' in kwargs:
                addr = kwargs['addr']
            # Decode op
            if (op == GCOp.CONFIG_WRITE):
                self.config_write(addr, data)
            if (op == GCOp.CONFIG_READ):
                self.config_read(addr)
            elif (op == GCOp.WRITE_A050):
                self.wr_A050()
            elif (op == GCOp.WRITE_TST):
                self.write_gc_reg(GCRegAddr.TST_ADDR, data)
            elif (op == GCOp.READ_TST):
                self.read_gc_reg(GCRegAddr.TST_ADDR)
            elif (op == GCOp.GLOBAL_RESET):
                self.global_reset(data)
            elif (op == GCOp.WRITE_STALL):
                self.write_gc_reg(GCRegAddr.STALL_ADDR, data)
            elif (op == GCOp.READ_STALL):
                self.read_gc_reg(GCRegAddr.STALL_ADDR)
            elif (op == GCOp.ADVANCE_CLK):
                self.advance_clk(addr, data)
            elif (op == GCOp.READ_CLK_DOMAIN):
                self.read_gc_reg(GCRegAddr.CLK_SEL_ADDR)
            elif (op == GCOp.SWITCH_CLK):
                self.write_gc_reg(GCRegAddr.CLK_SEL_ADDR, data)
            elif (op == GCOp.WRITE_RW_DELAY_SEL):
                self.write_gc_reg(GCRegAddr.RW_DELAY_SEL_ADDR, data)
            elif (op == GCOp.READ_RW_DELAY_SEL):
                self.read_gc_reg(GCRegAddr.RW_DELAY_SEL_ADDR)
            elif (op == GCOp.WRITE_CLK_SWITCH_DELAY_SEL):
                self.write_gc_reg(GCRegAddr.CLK_SWITCH_DELAY_SEL_ADDR, data)
            elif (op == GCOp.READ_CLK_SWITCH_DELAY_SEL):
                self.read_gc_reg(GCRegAddr.CLK_SWITCH_DELAY_SEL_ADDR)
            return self

    return _GlobalController
