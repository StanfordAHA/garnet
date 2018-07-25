from common.configurable_model import ConfigurableModel
import functools
from bit_vector import BitVector
from enum import Enum
import magma as m


class Mode(Enum):
    LINE_BUFFER = 0
    FIFO = 1
    SRAM = 2


def gen_mem(data_width: int,
            data_depth: int):
    def check_addr(fn):
        @functools.wraps(fn)
        def wrapped(self, addr, *args):
            assert 0 <= addr < data_depth, \
                f"Address ({addr}) must be within range(0, {data_depth})"
            return fn(self, addr, *args)
        return wrapped

    CONFIG_ADDR = BitVector(0, 32)

    class Mem(ConfigurableModel(32, 32)):
        def __init__(self):
            super().__init__()
            # TODO: should clock start at 0?
            self.last_clk = 0
            self.__reset()

        def __reset(self):
            self.memory = {}
            self.data_out_delayed = None
            self.data_out = None
            self.read_data = None
            # TODO: Is this actually 0?
            self.config[CONFIG_ADDR] = BitVector(0, 32)
            # TODO: should we reset last_clk?

        def __call__(self, clk_in, clk_en, reset, config_en, wen_in: m.Bit,
                     ren_in: m.Bit, config_addr, config_data, data_in, addr_in,
                     **kwargs):
            if reset == 1:
                self.__reset()
            else:
                # On the posedge
                if clk_in and not self.last_clk:
                    if config_en:
                        self.config[config_addr] = config_data
                        self.read_data = self.config[config_addr]
                    # TODO: can we config and execute at the same time or
                    # should this be an elif?
                    if self.__mode == Mode.SRAM:
                        # (From Raj) In the case that both read enable and
                        # write enable are asserted the output data is the data
                        # written in the same cycle (not the previous value).
                        if wen_in & ren_in:
                            self.__write(addr_in, data_in)
                            self.data_out = self.__read(addr_in)
                        elif wen_in:
                            self.__write(addr_in, data_in)
                        elif ren_in:
                            if self.data_out_delayed:
                                self.data_out = self.data_out_delayed
                                self.data_out_delayed = None
                            self.data_out_delayed = self.__read(addr_in)

            self.last_clk = clk_in
            return self.data_out

        @property
        def __mode(self):
            """
            The mode is stored in the lowest 2 (least significant) bits of the
            configuration data.
            """
            return Mode((self.config[CONFIG_ADDR] & 0x3).unsigned_value)

        @check_addr
        def __read(self, addr):
            if self.__mode == Mode.SRAM:
                return self.memory[addr]
            else:
                raise NotImplementedError(self.__mode)  # pragma: nocover

        @check_addr
        def __write(self, addr, value):
            if isinstance(value, BitVector):
                assert value.num_bits <= data_width, \
                    f"value.num_bits must be <= {data_width}"
            if isinstance(value, int):
                assert value.bit_length() <= data_width, \
                    f"value.bit_length() must be <= {data_width}"
            if self.__mode == Mode.SRAM:
                self.memory[addr] = value
            else:
                raise NotImplementedError(self.__mode)  # pragma: nocover
    return Mem
