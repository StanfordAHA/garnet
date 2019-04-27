import magma
from gemstone.common.core import Core


class IOCore(Core):
    def __init__(self):
        super().__init__()

        self.add_ports(
            glb2io_16bit=magma.In(magma.Bits[16]),
            glb2io_1bit=magma.In(magma.Bit),
            io2glb_16bit=magma.Out(magma.Bits[16]),
            io2glb_1bit=magma.Out(magma.Bit),
            f2io_16bit=magma.In(magma.Bits[16]),
            f2io_1bit=magma.In(magma.Bit),
            io2f_16bit=magma.Out(magma.Bits[16]),
            io2f_1bit=magma.Out(magma.Bit),
        )

        self.wire(self.ports.glb2io_16bit, self.ports.io2f_16bit)
        self.wire(self.ports.glb2io_1bit, self.ports.io2f_1bit)
        self.wire(self.ports.f2io_16bit, self.ports.io2glb_16bit)
        self.wire(self.ports.f2io_1bit, self.ports.io2glb_1bit)

    def inputs(self):
        return [self.ports.glb2io_16bit, self.ports.glb2io_1bit,
                self.ports.f2io_16bit, self.ports.f2io_1bit]

    def outputs(self):
        return [self.ports.io2glb_16bit, self.ports.io2glb_1bit,
                self.ports.io2f_16bit, self.ports.io2f_1bit]

    def name(self):
        return "io_core"
