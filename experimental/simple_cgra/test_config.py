import generator
import magma
import mantle
from from_magma import FromMagma


class ConfigRegister(generator.Generator):
    def __init__(self, width):
        super().__init__()

        self.width = width
        self.addr = None
        self.addr_width = 32
        self.data_width = 32

        T = magma.Bits(self.width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            addr_in=magma.In(magma.Bits(self.addr_width)),
            data_in=magma.In(magma.Bits(self.data_width)),
            O=magma.Out(T),
        )

    def circuit(self):
        assert self.addr is not None
        class _ConfigRegisterCircuit(magma.Circuit):
            name = self.name()
            IO = self.decl()

            @classmethod
            def definition(io):
                reg = mantle.Register(self.width)
                magma.wire(io.data_in[0:self.width], reg.I)
                magma.wire(reg.O, io.O)

        return _ConfigRegisterCircuit

    def name(self):
        return f"ConfigRegister_{self.width}_{self.addr}"


class Configurable(generator.Generator):
    def __init__(self):
        super().__init__()

        self.registers = {}
        self.addr_width = 32
        self.data_width = 32

        self.add_ports(
            clk=magma.In(magma.Clock),
            config_addr=magma.In(magma.Bits(self.addr_width)),
            config_data=magma.In(magma.Bits(self.data_width)),
        )

    def __getattr__(self, name):
        if name in self.registers:
            return self.registers[name].O
        return super().__getattr__(name)

    def add_config(self, name, width):
        assert name not in self._ports
        assert name not in self.registers
        register = ConfigRegister(width)
        self.wire(self.config_addr, register.addr_in)
        self.wire(self.config_data, register.data_in)
        self.registers[name] = register

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)


class InnerGenerator(Configurable):
    def __init__(self, width):
        super().__init__()

        self.width = width
        T = magma.Bits(width)

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )

        self.add_configs(
            operand0=self.width,
            operand1=self.width,
        )
        self.registers["operand0"].addr = 0
        self.registers["operand1"].addr = 0

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
            I0=magma.In(T),
            I1=magma.In(T),
            I2=magma.In(T),
            I3=magma.In(T),
            O=magma.Out(T),
        )

        self.add_configs(
            sel=2,
        )
        self.registers["sel"].addr = 0

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
