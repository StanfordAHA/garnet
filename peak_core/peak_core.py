import hwtypes
import magma
from gemstone.common.core import Core
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.from_magma import FromMagma


def _convert_type(typ):
    return magma.Bits(typ.size)


class _PeakWrapper:
    def __init__(self, peak_program):
        self.pe = peak_program(hwtypes.BitVector.get_family())
        isa = self.pe._peak_isa_
        assert len(isa) == 1
        key = list(isa.keys())[0]
        self.instr_type = isa[key]

    def rtl(self):
        IO = []
        for name, typ in self.inputs().items():
            IO.extend([name, magma.In(_convert_type(typ))])
        for name, typ in self.outputs().items():
            IO.extend([name, magma.Out(_convert_type(typ))])
        circ = magma.DefineCircuit("peak", *IO)

        # TODO(rsetaluri): Remove!
        magma.wire(circ.a, circ.alu_res)

        magma.EndCircuit()
        return circ

    def inputs(self):
        return self.pe._peak_inputs_

    def outputs(self):
        return self.pe._peak_outputs_

    def instruction_type(self):
        return self.instr_type


class PeakCore(Core):
    def __init__(self, peak_program):
        super().__init__(8, 32)

        self.wrapper = _PeakWrapper(peak_program)

        # Generate core RTL (as magma).
        self.peak_circuit = FromMagma(self.wrapper.rtl())
        # Add input ports and wire them.
        for name, typ in self.wrapper.inputs().items():
            self.add_port(name, magma.In(_convert_type(typ)))
            self.wire(self.ports[name], self.peak_circuit.ports[name])
        # Add output ports and wire them.
        for name, typ in self.wrapper.outputs().items():
            self.add_port(name, magma.Out(_convert_type(typ)))
            self.wire(self.ports[name], self.peak_circuit.ports[name])

        self.add_ports(
            config=magma.In(ConfigurationType(8, 32)),
        )

        # TODO(rsetaluri): Figure out stall signals.

        self.add_config("op", 32)

        self._setup_config()

    def configure(self, instr):
        assert isinstance(instr, self.wrapper.instruction_type())
        print (instr)
        #exit()

    def instruction_type(self):
        return self.wrapper.instruction_type()

    def inputs(self):
        return [self.ports[name] for name in self.wrapper.inputs()]

    def outputs(self):
        return [self.ports[name] for name in self.wrapper.outputs()]

    def name(self):
        return "PE"
