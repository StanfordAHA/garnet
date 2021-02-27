import math
import hwtypes
from hwtypes.modifiers import strip_modifiers
import magma as m
import peak
from peak.assembler import Assembler
from peak.family import PyFamily, MagmaFamily
import mantle
from gemstone.common.core import ConfigurableCore, PnRTag
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.const import Const
from gemstone.generator.generator import Generator
from collections import OrderedDict
from .data_gate import data_gate


class HashableDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.keys())))


def _convert_type(typ):
    if issubclass(typ, hwtypes.AbstractBit):
        return m.Bits[1]
    return m.Bits[typ.size]


class _PeakWrapperMeta(type):
    _cache = {}

    def __call__(cls, peak_generator):
        key = id(peak_generator)
        if key in _PeakWrapperMeta._cache:
            return _PeakWrapperMeta._cache[key]
        self = super().__call__(peak_generator)
        _PeakWrapperMeta._cache[key] = self
        return self


class _PeakWrapper(metaclass=_PeakWrapperMeta):
    def __init__(self, peak_generator):
        pe = peak_generator(PyFamily())
        assert issubclass(pe, peak.Peak)
        self._model = pe()
        #Lassen's name for the ISA is 'inst', so this is hardcoded
        self.__instr_name = 'inst'
        self.__instr_type = strip_modifiers(pe.input_t.field_dict['inst'])
        self.__inputs = OrderedDict(pe.input_t.field_dict)
        del self.__inputs['inst']
        self.__outputs = OrderedDict(pe.output_t.field_dict)
        circuit = peak_generator(MagmaFamily())
        self.__asm = Assembler(self.__instr_type)
        instr_magma_type = type(circuit.interface.ports[self.__instr_name])
        self.__circuit = peak.wrap_with_disassembler(
            circuit, self.__asm.disassemble, self.__asm.width,
            HashableDict(self.__asm.layout),
            instr_magma_type)
        data_gate(self.__circuit)

    @property
    def model(self):
        return self._model

    def rtl(self):
        return self.__circuit

    def inputs(self):
        return self.__inputs

    def outputs(self):
        return self.__outputs

    def instruction_name(self):
        return self.__instr_name

    def instruction_type(self):
        return self.__instr_type

    def instruction_width(self):
        return self.__asm.width

    def assemble(self, instr):
        return self.__asm.assemble(instr)


class PassThroughReg(m.Generator2):
    def __init__(self, name: str):
        self.name = name
        self.io = m.IO(
            config_addr=m.In(m.Bits[8]),
            config_addr_out=m.Out(m.Bits[8]),
            config_data=m.In(m.Bits[32]),
            config_data_out=m.Out(m.Bits[32]),
            config_en=m.In(m.Bit),
            config_en_out=m.Out(m.Bit),
            reset=m.In(m.AsyncReset),
            reset_out=m.Out(m.AsyncReset),
            O=m.Out(m.Out(m.Bits[32])),
            O_in=m.In(m.In(m.Bits[32]))
        )
        self.width = 32

        m.wire(self.io.config_addr, self.io.config_addr_out)
        m.wire(self.io.config_data, self.io.config_data_out)
        m.wire(self.io.config_en, self.io.config_en_out)
        m.wire(self.io.reset, self.io.reset_out)
        m.wire(self.io.O_in, self.io.O)

        self.addr = 0

    def set_addr(self, addr):
        self.addr = addr

    def set_global_addr(self, global_addr):
        pass

    def set_addr_width(self, addr_width):
        pass

    def set_data_width(self, data_width):
        pass

    def name(self):
        return f"PassThroughRegister"


class PeakCore(ConfigurableCore):
    def __init__(self, peak_generator):
        super().__init__(8, 32)
        self.name = "PE"
        self.ignored_ports = {"clk_en", "reset", "config_addr", "config_data",
                              "config_en", "read_config_data"}

        self.wrapper = _PeakWrapper(peak_generator)

        # Generate core RTL
        self.peak_circuit = self.wrapper.rtl()

        # Add input/output ports and wire them.
        inputs = self.wrapper.inputs()
        outputs = self.wrapper.outputs()
        for ports, dir_ in ((inputs, m.In), (outputs, m.Out),):
            for i, (name, typ) in enumerate(ports.items()):
                if name in self.ignored_ports:
                    continue
                magma_type = _convert_type(typ)
                self.io += m.IO(**{name: dir_(magma_type)})
                my_port = getattr(self.io, name)
                if magma_type is m.Bits[1]:
                    my_port = my_port[0]
                magma_name = name if dir_ is m.In else f"O{i}"
                m.wire(my_port, getattr(self.peak_circuit, magma_name)

        self.io += m.IO(
            config=m.In(ConfigurationType(8, 32)),
            stall=m.In(m.Bits[1])
        )

        # Set up configuration for PE instruction. Currently, we perform a naive
        # partitioning of the large instruction into 32-bit config registers.
        config_width = self.wrapper.instruction_width()
        num_config = math.ceil(config_width / 32)
        instr_name = self.wrapper.instruction_name()
        self.reg_width = {}
        for i in range(num_config):
            name = f"{instr_name}_{i}"
            self.add_config(name, 32)
            lb = i * 32
            ub = min(i * 32 + 32, config_width)
            len_ = ub - lb
            self.reg_width[name] = len_
            m.wire(self.registers[name].O[:len_],
                   getattr(self.peak_circuit, instr_name)[lb:ub])

        # connecting the wires
        # TODO: connect this wire once lassen has async reset
        m.wire(self.io.reset, self.peak_circuit.ASYNCRESET)

        # wire the fake register to the actual lassen core
        ports = ["config_data", "config_addr"]
        for port in ports:
            m.wire(self.io.config[port], getattr(self.peak_circuit, port))
            # self.wire(reg1.ports[reg_port], self.peak_circuit.ports[port])

        # wire it to 0, since we'll never going to use it
        m.wire(0, self.peak_circuit.config_en)

        # PE core uses clk_en (essentially active low stall)
        self.stallInverter = mantle.DefineInvert(1)
        m.wire(self.stallInverter.I, self.io.stall)
        m.wire(self.stallInverter.O[0], self.peak_circuit.clk_en)

        self._setup_config()

    def get_config_bitstream(self, instr):
        assert isinstance(instr, self.wrapper.instruction_type())
        config = self.wrapper.assemble(instr)
        config_width = self.wrapper.instruction_width()
        num_config = math.ceil(config_width / 32)
        instr_name = self.wrapper.instruction_name()
        result = []
        for i in range(num_config):
            name = f"{instr_name}_{i}"
            reg_idx = self.get_reg_idx(name)
            data = int(config[i * 32:i * 32 + 32])
            result.append((reg_idx, data))
        return result

    def instruction_type(self):
        return self.wrapper.instruction_type()

    def inputs(self):
        return [self.ports[name] for name in self.wrapper.inputs()
                if name not in self.ignored_ports]

    def outputs(self):
        return [self.ports[name] for name in self.wrapper.outputs()
                if name not in self.ignored_ports]

    def pnr_info(self):
        # PE has highest priority
        return PnRTag("p", self.DEFAULT_PRIORITY, self.DEFAULT_PRIORITY)

