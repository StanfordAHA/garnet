import magma
from core import Core
from from_verilog import FromVerilog


class MemCore(Core):
    def __init__(self):
        super().__init__()

        TData = magma.Bits(16)
        TBit = magma.Bit

        self.add_ports(
            data_in=magma.In(TData),
            addr_in=magma.In(TData),
            data_out=magma.Out(TBit),
        )

        # TODO(rsetaluri): Actual impl.

    def inputs(self):
        return [self.data_in, self.addr_in]

    def outputs(self):
        return [self.data_out]

    def name(self):
        return "MemCore"
