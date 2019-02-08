import magma
import mantle
import generator.generator as generator
from generator.from_magma import FromMagma
from common.mux_interface import MuxInterface


class MuxWrapper(MuxInterface):
    def definition(self):
        MuxCls = mantle.DefineMux(self.height, self.width)
        self.mux = FromMagma(MuxCls)

        for i in range(self.height):
            self.wire(self.ports.I[i], self.mux.ports[f"I{i}"])
        mux_in = self.ports.S if self.sel_bits > 1 else self.ports.S[0]
        self.wire(mux_in, self.mux.ports.S)
        self.wire(self.mux.ports.O, self.ports.O)

    def name(self):
        return f"MuxWrapper_{self.height}_{self.width}"
