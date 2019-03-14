from gemstone.common.configurable_model import ConfigurableModel
import functools
from hwtypes import BitVector
from enum import Enum
import magma as m
import fault
import logging
logging.basicConfig(level=logging.DEBUG)


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
            self.reset()

        def configure(self, addr, data):
            self.config[addr] = data

        def reset(self):
            address_width = m.bitutils.clog2(data_depth)
            self.memory = Memory(address_width, data_width)
            self.data_out = fault.UnknownValue
            self.read_data = fault.UnknownValue
            # TODO: Is the initial config actually 0?
            self.configure(CONFIG_ADDR, BitVector(0, 32))
            # Ignore these signals for now
            self.valid_out = fault.UnknownValue
            self.chain_out = fault.UnknownValue
            self.chain_valid_out = fault.UnknownValue
            self.almost_full = fault.UnknownValue
            self.almost_empty = fault.UnknownValue
            self.read_data_sram = fault.UnknownValue
            self.read_data_linebuf = fault.UnknownValue

        def read(self, addr):
            if self.__mode == Mode.SRAM:
                self.data_out = self.memory.read(addr)
            else:
                raise NotImplementedError(self.__mode)  # pragma: nocover

        def write(self, addr, data):
            if self.__mode == Mode.SRAM:
                self.memory.write(addr, data)
            else:
                raise NotImplementedError(self.__mode)  # pragma: nocover

        def read_and_write(self, addr, data):
            # write takes priority
            self.write(addr, data)

        def __call__(self, *args, **kwargs):
            raise NotImplementedError()

        @property
        def __mode(self):
            """
            The mode is stored in the lowest 2 (least significant) bits of the
            configuration data.
            """
            return Mode((self.config[CONFIG_ADDR] & 0x3).as_uint())
    return MemoryCore
