import magma
from gemstone.common.core import Core


class IO16bit(Core):
    def __init__(self):
        super().__init__()
        TBit = magma.Bits[16]

        self.add_ports(
            glb2io=magma.In(TBit),
            io2glb=magma.Out(TBit),
            io2f_16=magma.Out(TBit),
            f2io_16=magma.In(TBit)
        )

        self.wire(self.ports.glb2io, self.ports.io2f_16)
        self.wire(self.ports.f2io_16, self.ports.io2glb)

    def inputs(self):
        return [self.ports.glb2io, self.ports.f2io_16]

    def outputs(self):
        return [self.ports.io2glb, self.ports.io2f_16]

    def name(self):
        return "io16bit"
