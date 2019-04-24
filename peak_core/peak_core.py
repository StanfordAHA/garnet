import inspect
import math
import hwtypes
import magma
import peak
from gemstone.common.core import ConfigurableCore
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.from_magma import FromMagma


def _convert_type(typ):
    if issubclass(typ, hwtypes.AbstractBit):
        return magma.Bits[1]
    return magma.Bits[typ.size]


class _PeakWrapper:
    def __init__(self, peak_generator):
        pe = peak_generator(hwtypes.BitVector.get_family())
        assert issubclass(pe, peak.Peak)
        pe = pe.__call__
        (self.__instr_name, self.__instr_type) = pe._peak_isa_
        self.__inputs = pe._peak_inputs_
        self.__outputs = pe._peak_outputs_
        circuit = peak_generator(magma.get_family())
        self.__asm, disasm, self.__instr_width, layout = \
            peak.auto_assembler.generate_assembler(self.__instr_type)
        instr_magma_type = type(circuit.interface.ports[self.__instr_name])
        self.__circuit = peak.wrap_with_disassembler(
            circuit, disasm, self.__instr_width, layout, instr_magma_type)

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
        return self.__instr_width

    def assemble(self, instr):
        return self.__asm(instr)


class PeakCore(ConfigurableCore):
    def __init__(self, peak_generator):
        super().__init__(8, 32)

        self.wrapper = _PeakWrapper(peak_generator)

        # Generate core RTL (as magma).
        self.peak_circuit = FromMagma(self.wrapper.rtl())

        # Add input/output ports and wire them.
        inputs = self.wrapper.inputs()
        outputs = self.wrapper.outputs()
        for ports, dir_ in ((inputs, magma.In), (outputs, magma.Out),):
            for i, (name, typ) in enumerate(ports.items()):
                magma_type = _convert_type(typ)
                self.add_port(name, dir_(magma_type))
                my_port = self.ports[name]
                if magma_type is magma.Bits[1]:
                    my_port = my_port[0]
                magma_name = name if dir_ is magma.In else f"O{i}"
                self.wire(my_port, self.peak_circuit.ports[magma_name])

        self.add_ports(
            config=magma.In(ConfigurationType(8, 32)),
        )

        # TODO(rsetaluri): Figure out stall signals.

        # Set up configuration for PE instruction. Currently, we perform a naive
        # partitioning of the large instruction into 32-bit config registers.
        config_width = self.wrapper.instruction_width()
        num_config = math.ceil(config_width / 32)
        instr_name = self.wrapper.instruction_name()
        for i in range(num_config):
            name = f"{instr_name}_{i}"
            self.add_config(name, 32)
            lb = i * 32
            ub = min(i * 32 + 32, config_width)
            len_ = ub - lb
            self.wire(self.registers[name].ports.O[:len_],
                      self.peak_circuit.ports[instr_name][lb:ub])

        self._setup_config()

    def configure(self, instr):
        assert isinstance(instr, self.wrapper.instruction_type())
        config = self.wrapper.assemble(instr)
        config_width = self.wrapper.instruction_width()
        num_config = math.ceil(config_width / 32)
        instr_name = self.wrapper.instruction_name()
        result = []
        for i in range(num_config):
            name = f"{instr_name}_{i}"
            reg_idx = self.registers[name].addr
            data = int(config[i * 32:i * 32 + 32])
            result.append((reg_idx, data))
        return result

    def instruction_type(self):
        return self.wrapper.instruction_type()

    def inputs(self):
        return [self.ports[name] for name in self.wrapper.inputs()]

    def outputs(self):
        return [self.ports[name] for name in self.wrapper.outputs()]

    def name(self):
        return "PE"
