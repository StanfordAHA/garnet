import generator
import magma
import mantle
from from_magma import FromMagma


class _Register(generator.Generator):
    def __init__(self, width):
        super().__init__()

        self.width = width

        T = magma.Bits(self.width)

        self.add_ports(O=magma.Out(T))

    def circuit(self):
        circ = magma.DefineCircuit(self.name(), *self.decl())
        magma.wire(magma.bits(0, self.width), circ.O)
        magma.EndCircuit()
        return circ

    def name(self):
        return f"Register_{self.width}"

class Configurable(generator.Generator):
    def __init__(self):
        super().__init__()
        self.registers = {}

    def __getattr__(self, name):
        if name in self.registers:
            return self.registers[name].O
        return super().__getattr__(name)        

    def add_config(self, name, width):
        assert name not in self._ports
        assert name not in self.registers
        self.registers[name] = _Register(width)

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)


class InnerGenerator(Configurable):
    def __init__(self, width):
        super().__init__()

        self.width = width
        T = magma.Bits(width)

        self.add_ports(
            config_addr=magma.In(magma.Bits(32)),
            config_data=magma.In(magma.Bits(32)),
            I=magma.In(T),
            O=magma.Out(T),
        )

        self.add_configs(
            operand0=self.width,
            operand1=self.width,
        )

        self.and_ = FromMagma(mantle.DefineAnd(3, width))

        self.wire(self.I, self.and_.I0)
        self.wire(self.operand0, self.and_.I1)
        self.wire(self.operand1, self.and_.I2)
        self.wire(self.and_.O, self.O)

    def name(self):
        return f"InnerGenerator_{self.width}"


class TopGenerator(Configurable):
    def __init__(self):
        super().__init__()

        width = 16
        T = magma.Bits(width)

        self.inner = InnerGenerator(width)

        self.add_ports(
            config_addr=magma.In(magma.Bits(32)),
            config_data=magma.In(magma.Bits(32)),
            I0=magma.In(T),
            I1=magma.In(T),
            I2=magma.In(T),
            I3=magma.In(T),
            O=magma.Out(T),
        )

        self.add_configs(
            sel=2,
        )

        self.mux = FromMagma(mantle.DefineMux(4, width))

        self.wire(self.config_addr, self.inner.config_addr)
        self.wire(self.config_data, self.inner.config_data)
        self.wire(self.I0, self.mux.I0)
        self.wire(self.I1, self.mux.I1)
        self.wire(self.I2, self.mux.I2)
        self.wire(self.I3, self.mux.I3)
        self.wire(self.sel, self.mux.S)
        self.wire(self.mux.O, self.inner.I)
        self.wire(self.O, self.inner.O)
    
    def name(self):
        return "Top"    


if __name__ == "__main__":
    top_gen = TopGenerator()
    top_circ = top_gen.circuit()
    magma.compile("top", top_circ, output="coreir")
    print(open("top.json").read())
