import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper


GLB_ADDR_WIDTH = 32
BANK_ADDR_WIDTH = 17


class _Ternary(Generator):
    def __init__(self, width):
        super().__init__()

        self.width = width
        T = m.Bits[width]

        self.add_ports(
            first=m.In(T),
            second=m.In(T),
            select=m.In(m.Bits[1]),
            out=m.Out(T)
        )

        mux = MuxWrapper(2, self.width)
        self.wire(self.ports.first, mux.ports.I[0])
        self.wire(self.ports.second, mux.ports.I[1])
        self.wire(self.ports.select, mux.ports.S)
        self.wire(self.ports.out, mux.ports.O)

    def name(self):
        return f"_Ternary{self.width}"


def _ternary(parent, width, first, second, select):
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

        TArray = m.Array[self.num_io_channels,
                             m.Array[self.banks_per_io, m.Bits[1]]]
        self.add_ports(
            io_to_bank_wr_en=m.Out(m.Array[self.num_banks, m.Bit]),
            # io_to_bank_wr_data=m.Out(m.Array[self.num_banks, BANK_DATA_WIDTH),
            # io_to_bank_wr_data_bit_sel=m.Out(m.Array[self.num_banks, BANK_DATA_WIDTH),
            io_to_bank_wr_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),

            # io_to_bank_rd_en=m.Out(m.Array[self.num_banks, 1),
            # io_to_bank_rd_addr=m.Out(m.Array[self.num_banks, BANK_ADDR_WIDTH),
            # bank_to_io_rd_data=m.In(m.Array[self.num_banks, BANK_DATA_WIDTH),

            io_ctrl_switch_sel=m.In(TArray),
            io_addr=m.In(m.Array[self.num_io_channels, m.Bits[GLB_ADDR_WIDTH]]),
        )

        # bank_addr_int = [Fromm(mantle.DefineRegister(GLB_ADDR_WIDTH)) * self.num_banksArray[]
        bank_addr_int = [m.Bits[GLB_ADDR_WIDTH]]*self.num_banks

        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_addr_int[0] = _ternary(self, GLB_ADDR_WIDTH, self.ports.io_addr[0], Const(0), self.ports.io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_addr_int[idx] = _ternary(self, GLB_ADDR_WIDTH, self.ports.io_addr[j], bank_addr_int[idx - 1], self.ports.io_ctrl_switch_sel[j][k])


        for i in range(self.num_banks):
            self.wire(self.ports.io_to_bank_wr_en[i],
                      (Const(i) == bank_addr_int[i][BANK_ADDR_WIDTH:GLB_ADDR_WIDTH]))
            self.wire(self.ports.io_to_bank_wr_addr[i], bank_addr_int[i][0:BANK_ADDR_WIDTH])

    def name(self):
        return f"IoController_{self.num_banks}"


io_controller = IoController(32, 8)
print (repr(io_controller.circuit()))
m.compile("io_controller", io_controller.circuit(), output="coreir-verilog")
