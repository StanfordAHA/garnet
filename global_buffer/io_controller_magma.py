import magma
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.common.mux_wrapper import MuxWrapper


GLB_ADDR_WIDTH = 32


class _Ternary(Generator):
    def __init__(self, width):
        super().__init__()

        self.width = width
        T = magma.Bits[width]

        self.add_ports(
            first=magma.In(T),
            second=magma.In(T),
            select=magma.In(magma.Bit),
            out=magma.Out(T)
        )

        mux = MuxWrapper(2, self.width)
        self.wire(self.ports.first, mux.ports.I[0])
        self.wire(self.ports.second, mux.ports.I[1])
        self.wire(self.ports.select, mux.ports.S)
        self.wire(self.ports.out, mux.ports.O)

    def name(self):
        return f"Ternary{self.width}"


def _ternary(parent, width, first, second, select, out):
    ternary = _Ternary(width)
    parent.wire(first, ternary.ports.first)
    parent.wire(second, ternary.ports.second)
    parent.wire(select, ternary.ports.select)
    return ternary.ports.out


class IoController(Generator):
    def __init__(self, num_banks, num_io_channels):
        super().__init__()

        self.num_banks = num_banks
        self.num_io_channels = num_io_channels
        self.banks_per_io = int(num_banks / num_io_channels)


        TArray = magma.Array[self.num_io_channels,
                             magma.Array[self.banks_per_io, magma.Bit]]
        self.add_ports(
            bank_addr_int=magma.Out(magma.Bits[self.num_banks]),
            io_ctrl_switch_sel=magma.In(TArray),
        )

        bank_addr_int = FromMagma(mantle.DefineRegister(self.num_banks))
        self.wire(bank_addr_int.ports.O, self.ports.tmp)
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    pass
                else:
                    idx = j * self.banks_per_io + k
                    out = _ternary(self, 1, , bank_addr_int.ports.O[idx - 1], self.ports.io_ctrl_switch_sel[j][k])
                    self.wire(out, bank_addr_int.ports.I[idx])

    def name(self):
        return "IoController"


controller = IoController(32, 8)
print (repr(controller.circuit()))
