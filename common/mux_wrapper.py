import magma
import mantle
import generator.generator as generator
from generator.from_magma import FromMagma


class MuxWrapper(generator.Generator):
    def __init__(self, height, width, name=None):
        super().__init__(name)

        self.height = height
        self.width = width

        T = magma.Bits(self.width)

        # In the case that @height <= 1, we make this circuit a simple
        # pass-through circuit.
        if self.height <= 1:
            self.add_ports(
                I=magma.In(magma.Array(1, T)),
                O=magma.Out(T),
            )
            self.wire(self.ports.I[0], self.ports.O)
            self.sel_bits = 0
            return

        MuxCls = mantle.DefineMux(self.height, self.width)
        self.mux = FromMagma(MuxCls)

        self.sel_bits = magma.bitutils.clog2(self.height)

        self.add_ports(
            I=magma.In(magma.Array(self.height, T)),
            S=magma.In(magma.Bits(self.sel_bits)),
            O=magma.Out(T),
        )

        for i in range(self.height):
            self.wire(self.ports.I[i], self.mux.ports[f"I{i}"])
        mux_in = self.ports.S if self.sel_bits > 1 else self.ports.S[0]
        self.wire(mux_in, self.mux.ports.S)
        self.wire(self.mux.ports.O, self.ports.O)

    def name(self):
        return f"MuxWrapper_{self.height}_{self.width}"
