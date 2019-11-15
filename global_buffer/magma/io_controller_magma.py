import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper

GLB_ADDR_WIDTH = 32
BANK_ADDR_WIDTH = 17
BANK_DATA_WIDTH = 64

class _ToBits(Generator):
    def __init__(self):
        super().__init__()
        self.add_ports(
            I=m.In(m.Bit),
            O=m.Out(m.Bits[1])
        )
        tmp = m.Array[1, self.ports.I]
        m.wire(self.ports.O, tmp)

    def name(self):
        return f"ToBits"

def _tobits(parent, I):
    tobits = _ToBits()
    parent.wire(I, tobits.ports.I)
    return tobits.ports.O

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
            io_to_bank_wr_en=m.Out(m.Array[self.num_banks, m.Bits[1]]),
            io_to_bank_wr_data=m.Out(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
            io_to_bank_wr_data_bit_sel=m.Out(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
            io_to_bank_wr_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),

            # io_to_bank_rd_en=m.Out(m.Array[self.num_banks, 1),
            # io_to_bank_rd_addr=m.Out(m.Array[self.num_banks, BANK_ADDR_WIDTH),
            # bank_to_io_rd_data=m.In(m.Array[self.num_banks, BANK_DATA_WIDTH),

            io_ctrl_switch_sel=m.In(TArray),
            adgn_addr=m.In(m.Array[self.num_io_channels, m.Bits[GLB_ADDR_WIDTH]]),
            adgn_wr_en=m.In(m.Array[self.num_io_channels, m.Bit]),
            adgn_wr_data=m.In(m.Array[self.num_io_channels, m.Bits[BANK_DATA_WIDTH]]),
            adgn_wr_data_bit_sel=m.In(m.Array[self.num_io_channels, m.Bits[BANK_DATA_WIDTH]]),
        )

        # wr_en, wr_data, wr_data_bit_sel channels chain mux
        bank_wr_en_int = [m.Bit]*self.num_banks
        bank_wr_data_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        bank_wr_data_bit_sel_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_wr_en_int[0] = _ternary(self, 1, self.ports.adgn_wr_en[0], Const(0), self.ports.io_ctrl_switch_sel[0][0])
                    bank_wr_data_int[0] = _ternary(self, BANK_DATA_WIDTH, self.ports.adgn_wr_data[0], Const(0), self.ports.io_ctrl_switch_sel[0][0])
                    bank_wr_data_bit_sel_int[0] = _ternary(self, BANK_DATA_WIDTH, self.ports.adgn_wr_data_bit_sel[0], Const(0), self.ports.io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_wr_en_int[idx] = _ternary(self, 1, self.ports.adgn_wr_en[j], bank_wr_en_int[idx - 1], self.ports.io_ctrl_switch_sel[j][k])
                    bank_wr_data_int[idx] = _ternary(self, BANK_DATA_WIDTH, self.ports.adgn_wr_data[j], bank_wr_data_int[idx-1], self.ports.io_ctrl_switch_sel[j][k])
                    bank_wr_data_bit_sel_int[idx] = _ternary(self, BANK_DATA_WIDTH, self.ports.adgn_wr_data_bit_sel[j], bank_wr_data_bit_sel_int[idx-1], self.ports.io_ctrl_switch_sel[j][k])

        # address channel chain mux
        bank_addr_int = [m.Bits[GLB_ADDR_WIDTH]]*self.num_banks
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_addr_int[0] = _ternary(self, GLB_ADDR_WIDTH, self.ports.adgn_addr[0], Const(0), self.ports.io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_addr_int[idx] = _ternary(self, GLB_ADDR_WIDTH, self.ports.adgn_addr[j], bank_addr_int[idx - 1], self.ports.io_ctrl_switch_sel[j][k])

        # output wr_en
        for i in range(self.num_banks):
            eq = FromMagma(mantle.DefineEQ(GLB_ADDR_WIDTH-BANK_ADDR_WIDTH))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(bank_addr_int[i][BANK_ADDR_WIDTH:GLB_ADDR_WIDTH], eq.ports.I1)
            self.wire(Const(i), eq.ports.I0)
            self.wire(and_.ports.I0, _tobits(self, eq.ports.O))
            self.wire(and_.ports.I1, bank_wr_en_int[i])
            self.wire(self.ports.io_to_bank_wr_en[i], and_.ports.O)

        # output wr_addr
        for i in range(self.num_banks):
            self.wire(self.ports.io_to_bank_wr_addr[i], bank_addr_int[i][0:BANK_ADDR_WIDTH])

        # output wr_data, wr_data_bit_sel
        for i in range(self.num_banks):
            self.wire(self.ports.io_to_bank_wr_data[i], bank_wr_data_int[i])
            self.wire(self.ports.io_to_bank_wr_data_bit_sel[i], bank_wr_data_bit_sel_int[i])

        # output rd_en
        # for i in range(self.num_banks):
        #     eq = FromMagma(mantle.DefineEQ(GLB_ADDR_WIDTH-BANK_ADDR_WIDTH))
        #     self.wire(bank_addr_int[i][BANK_ADDR_WIDTH:GLB_ADDR_WIDTH], eq.ports.I1)
        #     self.wire(Const(i), eq.ports.I0)
        #     self.wire(self.ports.io_to_bank_wr_en[i], eq.ports.O)

    def name(self):
        return f"IoController_{self.num_banks}"


io_controller = IoController(32, 8)
print (repr(io_controller.circuit()))
m.compile("io_controller", io_controller.circuit(), output="coreir-verilog")
