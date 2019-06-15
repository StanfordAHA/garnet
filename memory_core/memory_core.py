from gemstone.common.configurable_model import ConfigurableModel
import functools
from hwtypes import BitVector
import magma as m
import fault
import logging
import karst.basic as kam
import buffer_mapping.mapping as bam
from .memory_mode import Mode
logging.basicConfig(level=logging.DEBUG)


class Memory:
    def __init__(self, address_width, data_width):
        self.address_width = address_width
        self.data_width = data_width
        self.data_depth = 1 << address_width
        self.memory = {BitVector[address_width](i): BitVector[data_width](0)
                       for i in range(self.data_depth)}


def gen_memory_core(data_width: int, data_depth: int):

    CONFIG_ADDR = BitVector[32](0)

    class MemoryCore(ConfigurableModel(32, 32)):

        _data_depth = 1024
        # Include functional models
        _fifo_model = kam.define_fifo()
        _sram_model = kam.define_sram()
        ___mode = 0
        _switch = 0

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
            self.configure(CONFIG_ADDR, BitVector[32](0))
            # Ignore these signals for now
            self.valid_out = fault.UnknownValue
            self.chain_out = fault.UnknownValue
            self.chain_valid_out = fault.UnknownValue
            self.almost_full = fault.UnknownValue
            self.almost_empty = fault.UnknownValue
            self.read_data_sram = fault.UnknownValue
            self.read_data_linebuf = fault.UnknownValue

        def set_mode(self, newmode):
            self.___mode = newmode

        def switch(self):
            if self.__mode == Mode.DB:
                self._db_model.switch()
            else:
                raise NotImplementedError(self.__mode)  # pragma: nocover

        def read(self, addr=0):
            if self.__mode == Mode.SRAM:
                self._sram_model.addr = addr
                self.data_out = self._sram_model.read()
            elif self.__mode == Mode.FIFO:
                self.data_out = self._fifo_model.dequeue()
            elif self.__mode == Mode.DB:
                self.data_out = self._db_model.read(0, addr)[0]
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
            self._fifo_model.configure(memory_size=self._data_depth,
                                       capacity=depth)
            self._fifo_model.reset()
            self.set_mode(Mode.FIFO)

        def config_sram(self, mem_size):
            self._sram_model.configure(memory_size=mem_size)
            self._sram_model.reset()
            self.set_mode(Mode.SRAM)

        def config_db(self, capacity, ranges, strides, start,
                      manual_switch, dimension, arb_addr=0):
            setup = {}
            setup["virtual buffer"] = {}
            setup["virtual buffer"]["input_port"] = 1
            setup["virtual buffer"]["output_port"] = 1
            setup["virtual buffer"]["capacity"] = capacity
            setup["virtual buffer"]["access_pattern"] = {}
            setup["virtual buffer"]["access_pattern"]["start"] = [start]
            setup["virtual buffer"]["access_pattern"]["range"] = \
                ranges[0:dimension]
            setup["virtual buffer"]["access_pattern"]["stride"] = \
                strides[0:dimension]
            setup["virtual buffer"]["manual_switch"] = manual_switch
            setup["virtual buffer"]["arbitrary_addr"] = arb_addr
            self._db_model = bam.CreateVirtualBuffer(setup["virtual buffer"])
            self.set_mode(Mode.DB)

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
                self.data_out = self._db_model.read(0, addr)[0]
            else:
                raise NotImplementedError(self.__mode)  # pragma: nocover

        def __call__(self, *args, **kwargs):
            raise NotImplementedError()  # pragma: nocover

        @property
        def __mode(self):
            """
            The mode is stored in the lowest 2 (least significant) bits of the
            configuration data.
            """
            return Mode(self.___mode)
    return MemoryCore
