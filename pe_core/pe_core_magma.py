import magma
from common.core import Core
from generator.configurable import ConfigurationType
from generator.from_verilog import FromVerilog


class PECore(Core):
    def __init__(self):
        super().__init__()

        self.impl = FromVerilog("pe_core/pe_core.v")

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
            config=magma.In(ConfigurationType(8, 32)),
        )

        for name, port in self.ports.items():
            if name == "config":
                continue
            self.wire(port, self.impl.ports[name])

    def inputs(self):
        return [self.data0, self.data1, self.bit0, self.bit1, self.bit2]

    def outputs(self):
        return [self.res, self.res_p]

    def name(self):
        return "PECore"
