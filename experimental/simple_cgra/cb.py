import magma
from mux_wrapper import MuxWrapper
from configurable import Configurable


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
        )
        self.add_configs(
            S=sel_bits,
        )

        self.wire(self.I, self.mux.I)
        self.wire(self.S, self.mux.S)
        self.wire(self.mux.O, self.O)

    def name(self):
        return f"SB_{self.height}_{self.width}"
