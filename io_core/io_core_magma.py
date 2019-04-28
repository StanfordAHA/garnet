import magma
from gemstone.common.core import Core, PnRTag


class IOCore(Core):
    def __init__(self):
        super().__init__()

        self.add_ports(
            glb2io_16=magma.In(magma.Bits[16]),
            glb2io_1=magma.In(magma.Bits[1]),
            io2glb_16=magma.Out(magma.Bits[16]),
            io2glb_1=magma.Out(magma.Bits[1]),
            f2io_16=magma.In(magma.Bits[16]),
            f2io_1=magma.In(magma.Bits[1]),
            io2f_16=magma.Out(magma.Bits[16]),
            io2f_1=magma.Out(magma.Bits[1]),
        )

        self.wire(self.ports.glb2io_16, self.ports.io2f_16)
        self.wire(self.ports.glb2io_1, self.ports.io2f_1)
        self.wire(self.ports.f2io_16, self.ports.io2glb_16)
        self.wire(self.ports.f2io_1, self.ports.io2glb_1)

    def inputs(self):
        return [self.ports.glb2io_16, self.ports.glb2io_1,
                self.ports.f2io_16, self.ports.f2io_1]

    def outputs(self):
        return [self.ports.io2glb_16, self.ports.io2glb_1,
                self.ports.io2f_16, self.ports.io2f_1]

    def name(self):
        return "io_core"

    def pnr_info(self):
        return [PnRTag("I", 2, self.DEFAULT_PRIORITY),
		PnRTag("i", 1, self.DEFAULT_PRIORITY)]
