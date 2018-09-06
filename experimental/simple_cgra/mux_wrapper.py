import generator
import magma
import mantle
from from_magma import FromMagma


class MuxWrapper(generator.Generator):
    def __init__(self, height, width):
        super().__init__()

        self.height = height
        self.width = width
        MuxCls = mantle.DefineMux(self.height, self.width)
        self.mux = FromMagma(MuxCls)

        T = magma.Bits(self.width)
        self.sel_bits = magma.bitutils.clog2(self.height)

        self.add_ports(
            I=magma.In(magma.Array(self.height, T)),
            S=magma.In(magma.Bits(self.sel_bits)),
            O=magma.Out(T),
        )

        for i in range(self.height):
            self.wire(self.I[i], getattr(self.mux, f"I{i}"))
        self.wire(self.S, self.mux.S)
        self.wire(self.mux.O, self.O)

    def name(self):
        return f"MuxWrapper_{self.height}_{self.width}"


