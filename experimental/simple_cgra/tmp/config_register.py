import generator
import magma
import mantle


class ConfigRegister(gemstone.generator.Generator):
    def __init__(self, width, addr_width, data_width, addr, config_en=False):
        super().__init__()

        self.width = width
        self.addr_width = addr_width
        self.data_width = data_width
        self.addr = addr
        self.config_en = config_en

        T = magma.Bits(self.width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            addr_in=magma.In(magma.Bits(self.addr_width)),
            data_in=magma.In(magma.Bits(self.data_width)),
            O=magma.Out(T),
        )
        if self.config_en:
            self.add_ports(ce=magma.In(magma.Bit))

    def circuit(self):
        assert self.addr is not None
        class _ConfigRegisterCircuit(magma.Circuit):
            name = self.name()
            IO = self.decl()

            @classmethod
            def definition(io):
                reg = mantle.Register(self.width, has_ce=True)
                ce = (io.addr_in == magma.bits(self.addr, self.addr_width))
                if self.config_en:
                    ce = ce & io.ce
                magma.wire(io.data_in[0:self.width], reg.I)
                magma.wire(ce, reg.CE)
                magma.wire(reg.O, io.O)

        return _ConfigRegisterCircuit

    def name(self):
        return f"ConfigRegister"\
            f"_{self.width}"\
            f"_{self.addr_width}"\
            f"_{self.data_width}"\
            f"_{self.addr}"
