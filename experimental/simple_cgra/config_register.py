import generator
import magma
import mantle


class ConfigRegister(generator.Generator):
    def __init__(self, width, use_config_en=True):
        super().__init__()

        self.width = width
        self.addr = None
        self.global_addr = None
        self.use_config_en = use_config_en

        T = magma.Bits(self.width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            O=magma.Out(T),
        )
        if self.use_config_en:
            self.add_ports(config_en=magma.In(magma.Bit))

    def circuit(self):
        assert self.addr is not None
        assert "config_addr" in self.ports
        assert "config_data" in self.ports

        self.addr_width = self.config_addr.base_type().N
        self.data_width = self.config_data.base_type().N

        class _ConfigRegisterCircuit(magma.Circuit):
            name = self.name()
            IO = self.decl()

            @classmethod
            def definition(io):
                reg = mantle.Register(self.width, has_ce=True)
                ce = (io.config_addr == magma.bits(self.addr, self.addr_width))
                if self.use_config_en:
                    ce = ce & io.config_en
                magma.wire(io.config_data[0:self.width], reg.I)
                magma.wire(ce, reg.CE)
                magma.wire(reg.O, io.O)

        return _ConfigRegisterCircuit

    def name(self):
        return f"ConfigRegister"\
            f"_{self.width}"\
            f"_{self.addr_width}"\
            f"_{self.data_width}"\
            f"_{self.addr}"
