import generator
import magma
import mantle


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
                reg = mantle.Register(self.width, has_ce=True)
                ce = (io.addr_in == magma.bits(self.addr, 32))
                magma.wire(io.data_in[0:self.width], reg.I)
                magma.wire(ce, reg.CE)
                magma.wire(reg.O, io.O)

        return _ConfigRegisterCircuit

    def name(self):
        return f"ConfigRegister_{self.width}_{self.addr}"
