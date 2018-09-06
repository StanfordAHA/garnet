import magma
from mux_wrapper import MuxWrapper
from configurable import Configurable, ConfigurationType


class CB(Configurable):
    def __init__(self, height, width):
        super().__init__()

        self.height = height
        self.width = width
        sel_bits = magma.bitutils.clog2(self.height)

        self.mux = MuxWrapper(self.height, self.width)

        T = magma.Bits(self.width)

        self.add_ports(
            I=magma.In(magma.Array(self.height, T)),
            O=magma.Out(T),
            clk=magma.In(magma.Clock),
            config=magma.In(ConfigurationType(8, 32)),
        )
        self.add_configs(
           S=sel_bits,
        )
        self.registers["S"].addr = 0

        self.wire(self.I, self.mux.I)
        self.wire(self.S, self.mux.S)
        self.wire(self.mux.O, self.O)

        self.fanout(self.config.config_addr, self.registers.values())
        self.fanout(self.config.config_data, self.registers.values())
        self.fanout(self.clk, self.registers.values())

    def name(self):
        return f"CB_{self.height}_{self.width}"
