import magma
from core import Core
from from_verilog import FromVerilog


class PECore(Core):
    def __init__(self):
        super().__init__()

        self.impl = FromVerilog("experimental/simple_cgra/pe_core.v")

        TData = magma.Bits(16)
        TBit = magma.Bits(1)

        self.add_ports(
            data0=magma.In(TData),
            data1=magma.In(TData),
            bit0=magma.In(TBit),
            bit1=magma.In(TBit),
            bit2=magma.In(TBit),
            res=magma.Out(TData),
            res_p=magma.Out(TBit),
        )

        for name, port in self.ports.items():
            self.wire(port, getattr(self.impl, name))

    def inputs(self):
        return [self.data0, self.data1, self.bit0, self.bit1, self.bit2]

    def outputs(self):
        return [self.res, self.res_p]

    def name(self):
        return "PECore"
