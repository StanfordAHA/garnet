import magma
import mantle
import generator.generator as generator
from generator.from_magma import FromMagma
from common.mux_interface import MuxInterface
from generator.const import Const


class _AOIMuxCell(magma.Circuit):
    T = magma.Bit
    IO = ["I0", magma.In(T), "I1", magma.In(T), "S", magma.In(T),
          "O", magma.Out(T)]

    @classmethod
    def definition(io):
        magma.wire(io.O, ((io.I0 & ~io.S) | (io.I1 & io.S)))


class AOIMux(MuxInterface):
    def definition(self):
        # TODO(rsetaluri): Move this to a mantle generator.
        num_stages = magma.bitutils.clog2(self.height)
        num_inputs = 2 ** num_stages
        num_muxes = num_inputs
        delta = num_inputs - self.height
        outputs = {}
        for i in range(num_stages):  # each stage
            num_muxes = num_muxes / 2
            for j in range(int(num_muxes)):  # each mux in a stage
                for k in range(self.width):  # each width
                    inst = FromMagma(_AOIMuxCell)
                    self.wire(self.ports.S[i], inst.ports.S)
                    if i == 0:
                        if delta == 0 or (j * 2 + 1) < self.height:
                            I0 = self.ports.I[j * 2][k]
                            I1 = self.ports.I[j * 2 + 1][k]
                        elif self.height % 2 and (j * 2 + 1) == self.height:
                            I0 = self.ports.I[j * 2][k]
                            I1 = Const(magma.bit(0))
                        else:
                            I0 = Const(magma.bit(0))
                            I1 = Const(magma.bit(0))
                    else:
                        I0 = outputs[(i - 1, j * 2, k)]
                        I1 = outputs[(i - 1, j * 2 + 1, k)]
                    self.wire(I0, inst.ports.I0)
                    self.wire(I1, inst.ports.I1)
                    outputs[(i, j, k)] = inst.ports.O
        for k in range(self.width):
            self.wire(self.ports.O[k], outputs[(i, j, k)])

    def name(self):
        return f"MuxWrapper_{self.height}_{self.width}"
