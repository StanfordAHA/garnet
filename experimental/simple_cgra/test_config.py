import generator
import magma
import mantle
from from_magma import FromMagma


class ConfigurationManager(generator.Generator):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.__idx = 0

    def __generate_name(self):
        name = f"unq_name_{self.__idx}"
        self.__idx += 1
        return name
    
    def config(self, width):
        T = magma.Out(magma.Bits(width))
        name = self.__generate_name()
        self.add_port(name, T)
        return getattr(self, name)

    def circuit(self):
        io = self.decl()
        circ = magma.DefineCircuit(self.name(), *self.decl())
        for i in range(0, len(io), 2):
            name = io[i]
            T = io[i + 1]
            magma.wire(getattr(circ, name), magma.bits(0, T.N))
        magma.EndCircuit()
        return circ

    def name(self):
        return f"ConfigurationManager_{self.owner.name()}"


class InnerGenerator(generator.Generator):
    def __init__(self, width):
        super().__init__()

        self.width = width
        T = magma.Bits(width)
        manager = ConfigurationManager(self)

        self.add_ports(
            config_addr=magma.In(magma.Bits(32)),
            config_data=magma.In(magma.Bits(32)),
            I=magma.In(T),
            O=magma.Out(T),
        )

        self.operand = manager.config(width)
        self.and_ = FromMagma(mantle.DefineAnd(2, width))

        self.wire(self.I, self.and_.I0)
        self.wire(self.operand, self.and_.I1)
        self.wire(self.and_.O, self.O)

    def name(self):
        return f"InnerGenerator_{self.width}"


class TopGenerator(generator.Generator):
    def __init__(self):
        super().__init__()

        width = 16
        T = magma.Bits(width)
        manager = ConfigurationManager(self)

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

        self.mux = FromMagma(mantle.DefineMux(4, width))
        self.sel = manager.config(2)

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
