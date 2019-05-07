from gemstone.common.configurable_model import ConfigurableModel
import functools
from hwtypes import BitVector
from enum import Enum
import magma as m
import fault
import logging
logging.basicConfig(level=logging.DEBUG)
import karst.basic as kam
import memory_core.BufferMapping.mapping as bam

class Mode(Enum):
    LINE_BUFFER = 0
    FIFO = 1
    SRAM = 2
    DB = 3

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

        _data_depth = 1024
        # Include functional models
        _fifo_model = kam.define_fifo()
        _sram_model = kam.define_sram()

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


        def switch(self):
          if self.__mode == Mode.DB:
            self._db_model.switch()
            print("switch")
          else:
            raise NotImplementedError(self.__mode)

        def read(self, addr):
            if self.__mode == Mode.SRAM:
                self._sram_model.addr = addr
                self.data_out = self._sram_model.read()
            elif self.__mode == Mode.FIFO:
                self.data_out = self._fifo_model.dequeue()
            elif self.__mode == Mode.DB:
                self.data_out = self._db_model.read()[0]
                print(self.data_out)
            else:
                raise NotImplementedError(self.__mode)  # pragma: nocover

        def write(self, addr, data):
            # SRAM
            if self.__mode == Mode.SRAM:
                self._sram_model.data_in = data
                self._sram_model.addr = addr
                self._sram_model.write()
            # DB
            elif self.__mode == Mode.DB:
                self._db_model.write(data)
            # FIFO
            elif self.__mode == Mode.FIFO:
                self._fifo_model.data_in = data
                self._fifo_model.enqueue()
            else:
                raise NotImplementedError(self.__mode)  # pragma: nocover

        def config_fifo(self, depth):
          self._fifo_model.configure(memory_size=self._data_depth, capacity=depth)
          self._fifo_model.reset()

        def config_sram(self, mem_size):
          self._sram_model.configure(memory_size=mem_size)
          self._sram_model.reset()

        def config_db(self, capacity, ranges, strides, start, manual_switch, dimension):
          setup = {}
          setup["virtual buffer"] = {}
          setup["virtual buffer"]["input_port"] = 1
          setup["virtual buffer"]["output_port"] = 1
          setup["virtual buffer"]["capacity"] = capacity
          setup["virtual buffer"]["access_pattern"] = {}
          setup["virtual buffer"]["access_pattern"]["start"] = start
          setup["virtual buffer"]["access_pattern"]["range"] = ranges[0:dimension]
          setup["virtual buffer"]["access_pattern"]["stride"] = strides[0:dimension]
          setup["virtual buffer"]["manual_switch"] = manual_switch
          self._db_model = bam.CreateVirtualBuffer(setup["virtual buffer"])

        def read_and_write(self, addr, data):
          # write takes priority
          if self.__mode == Mode.SRAM:
            self.write(addr, data)
          elif self.__mode == Mode.FIFO:
            self._fifo_model.data_in = data
            self._fifo_model.enqueue()
            self.data_out = self._fifo_model.dequeue()
          elif self.__mode == Mode.DB:
            self._db_model.write(data)
            self.data_out = self._db_model.read()[0]
            print(self.data_out)
          else:
            raise NotImplementedError(self.__mode) # pragma: nocover

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
