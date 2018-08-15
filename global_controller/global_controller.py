from common.configurable_model import ConfigurableModel
from bit_vector import BitVector
from enum import Enum
import magma as m
import fault


class GC_reg_addr(Enum):
    TST_addr = 0
    stall_addr = 1
    clk_sel_addr = 2
    rw_delay_sel_addr = 3
    clk_switch_delay_sel_addr = 4


def gen_global_controller(config_data_width: int,
                          config_addr_width: int,
                          config_op_width: int):

    class _GlobalController(ConfigurableModel(32, 32)):
        def __init__(self):
            super().__init__()
            self.NUM_STALL_DOMAINS = 4
            self.reset()

        def reset(self):
            self.TST = [BitVector(0, config_data_width)]
            self.stall = [BitVector(0, self.NUM_STALL_DOMAINS)]
            self.clk_sel = [BitVector(0, 1)]
            self.rw_delay_sel = [BitVector(0, config_data_width)]
            self.clk_switch_delay_sel = [BitVector(0, 1)]

            self.reset_out = [0]
            self.config_addr_out = [BitVector(0, config_addr_width)]
            self.config_data_out = [BitVector(0, config_data_width)]
            self.config_data_in = fault.UnknownValue
            self.read = [0]
            self.write = [0]
            self.config_data_to_jtag = [BitVector(0, config_data_width)]

        def config_read(self, addr):
            rw_delay = self.rw_delay_sel[0]
            duration = rw_delay.as_uint()
            self.read = [1] * duration + [0]
            self.write = [0] * (duration + 1)
            self.config_addr_out = [BitVector(addr, config_addr_width)] \
                * (duration + 1)
            self.config_data_to_jtag = [self.config_data_to_jtag[-1]] \
                + [self.config_data_in] * duration

        def config_write(self, addr, data):
            rw_delay = self.rw_delay_sel[0]
            duration = rw_delay.as_uint()
            self.read = [0] * (duration + 1)
            self.write = [1] * duration + [0]
            self.config_addr_out = [BitVector(addr, config_addr_width)] \
                * (duration + 1)
            self.config_data_out = [BitVector(data, config_data_width)] \
                * (duration + 1)

        def read_GC_reg(self, addr):
            if (addr == GC_reg_addr.TST_addr):
                out = self.TST[-1]
            elif (addr == GC_reg_addr.stall_addr):
                out = self.stall[-1]
            elif (addr == GC_reg_addr.clk_sel_addr):
                out = self.clk_sel[-1]
            elif (addr == GC_reg_addr.rw_delay_sel_addr):
                out = self.rw_delay_sel[-1]
            elif (addr == GC_reg_addr.clk_switch_delay_sel_addr):
                out = self.clk_switch_delay_sel[-1]
            else:
                raise ValueError("Reading from invalid GC_reg address")
            self.config_data_to_jtag = [BitVector(out, config_data_width)]

        def write_GC_reg(self, addr, data: BitVector):
            if (addr == GC_reg_addr.TST_addr):
                self.TST = [BitVector(data, config_data_width)]
            elif (addr == GC_reg_addr.stall_addr):
                self.stall = [BitVector(data, self.NUM_STALL_DOMAINS)]
            elif (addr == GC_reg_addr.clk_sel_addr):
                self.clk_sel = [BitVector(data, 1)]
            elif (addr == GC_reg_addr.rw_delay_sel_addr):
                self.rw_delay_sel = [BitVector(data, config_data_width)]
            elif (addr == GC_reg_addr.clk_switch_delay_sel_addr):
                self.clk_switch_delay_sel = [BitVector(data, 1)]
            else:
                raise ValueError("Writing to invalid GC_reg address")

        def global_reset(self, data: BitVector):
            if (data > 0):
                self.reset_out = [1] * data.as_uint() + [0]
            else:
                self.reset_out = [1] * 20 + [0]

        def advance_clk(self, addr: BitVector, data: BitVector):
            save_stall_reg = self.stall[-1]
            temp_stall_reg = BitVector(0, self.NUM_STALL_DOMAINS)
            for i in range(self.NUM_STALL_DOMAINS):
                if (addr[i] == 1 and save_stall_reg[i] == 1):
                    temp_stall_reg[i] = 0
                else:
                    temp_stall_reg[i] = save_stall_reg[i]
            self.stall = [temp_stall_reg] * data.as_uint() + [save_stall_reg]

        def set_config_data_in(self, data):
            self.config_data_in = BitVector(data, config_data_width)

        def __cleanup(self):
            # Remove sequences from outputs/regs in preparation for the next
            # op.
            self.stall = [self.stall[-1]]
            self.config_addr_out = [self.config_addr_out[-1]]
            self.config_data_out = [self.config_data_out[-1]]
            self.read = [self.read[-1]]
            self.write = [self.write[-1]]
            self.config_data_to_jtag = self.config_data_to_jtag[-1]

        def __call__(self, *args, **kwargs):
            output_obj = self
            self._cleanup()
            return output_obj

    return _GlobalController
