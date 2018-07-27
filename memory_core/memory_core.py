from common.configurable_model import ConfigurableModel
import functools
from bit_vector import BitVector
from enum import Enum
import magma as m
import logging


class Mode(Enum):
    LINE_BUFFER = 0
    FIFO = 1
    SRAM = 2


class Memory:
    def __init__(self, address_width, data_width):
        self.address_width = address_width
        self.data_width = data_width
        self.data_depth = 1 << address_width
        self.memory = {BitVector(i, address_width): BitVector(0, data_width)
                       for i in range(self.data_depth)}
        self.data_out = None
        self.data_out_delayed = None

    def check_addr(fn):
        @functools.wraps(fn)
        def wrapped(self, addr, *args):
            assert 0 <= addr < self.data_depth, \
                f"Address ({addr}) must be within range(0, {self.data_depth})"
            return fn(self, addr, *args)
        return wrapped

    @check_addr
    def read(self, addr):
        return self.memory[addr]

    @check_addr
    def write(self, addr, value):
        if isinstance(value, BitVector):
            assert value.num_bits <= self.data_width, \
                f"value.num_bits must be <= {self.data_width}"
        if isinstance(value, int):
            assert value.bit_length() <= self.data_width, \
                f"value.bit_length() must be <= {self.data_width}"
        self.memory[addr] = value


def gen_memory_core(data_width: int, data_depth: int):

    CONFIG_ADDR = BitVector(0, 32)

    class MemoryCore(ConfigurableModel(32, 32)):
        def __init__(self):
            super().__init__()
            # TODO: should clock start at 0?
            self.last_clk = 0
            self.__reset()

        def __reset(self):
            address_width = m.bitutils.clog2(data_depth)
            # Partition memories into two
            self.memories = [Memory(address_width - 1, data_width)
                             for _ in range(2)]
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
                        for memory in self.memories:
                            if memory.data_out_delayed is not None:
                                memory.data_out = memory.data_out_delayed
                                memory.data_out_delayed = None
                        if self.data_out_delayed is not None:
                            self.data_out = self.data_out_delayed
                            self.data_out_delayed = None
                        memory = self.memories[not addr_in[0]]
                        # Write takes priority
                        if wen_in:
                            memory.write(addr_in[1:], data_in)
                        elif ren_in:
                            memory.data_out = memory.read(addr_in[1:])
                        other_memory = self.memories[addr_in[0]]
                        if ren_in:
                            other_memory.data_out = \
                                other_memory.read(addr_in[1:])
                        self.data_out_delayed = memory.data_out
                        logging.debug(f"addr_in = {addr_in}")
                        logging.debug(f"memory.data_out = {memory.data_out}")
                        logging.debug(f"other_memory.data_out = {other_memory.data_out}")
                        logging.debug(f"self.data_out_delayed = {self.data_out}")
                        logging.debug(f"self.data_out_delayed = {self.data_out_delayed}")

            self.last_clk = clk_in
            return self.data_out

        @property
        def __mode(self):
            """
            The mode is stored in the lowest 2 (least significant) bits of the
            configuration data.
            """
            return Mode((self.config[CONFIG_ADDR] & 0x3).unsigned_value)
    return MemoryCore
