import magma
from gemstone.common.core import Core


class IO1bit(Core):
    def __init__(self):
        super().__init__()
        TBit = magma.Bits(1)

        self.add_ports(
            glb2io=magma.In(TBit),
            io2glb=magma.Out(TBit),
            io2f_1=magma.Out(TBit),
            f2io_1=magma.In(TBit)
        )
        self.wire(self.ports.glb2io, self.ports.io2f_1)
        self.wire(self.ports.f2io_1, self.ports.io2glb)

    def inputs(self):
        return [self.ports.glb2io, self.ports.f2io_1]

    def outputs(self):
        return [self.ports.io2glb, self.ports.io2f_1]

    def name(self):
        return "io1bit"
