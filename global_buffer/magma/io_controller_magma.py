import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.common.configurable import Configurable, ConfigurationType

GLB_ADDR_WIDTH = 32
BANK_ADDR_WIDTH = 17
BANK_DATA_WIDTH = 64

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

        mux = MuxWrapper(2, self.width,)
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


class IoController(Configurable):
    def __init__(self, num_banks, num_io_channels):

        self.num_banks = num_banks
        self.num_io_channels = num_io_channels
        self.banks_per_io = int(num_banks / num_io_channels)
        super().__init__(32, 32)

        TArray = m.Array[self.num_io_channels,
                         m.Array[self.banks_per_io, m.Bits[1]]]

        self.add_ports(
            stall=m.In(m.Bits[1]),
            cgra_done_pulse=m.Out(m.Bit),

            io_to_bank_wr_en=m.Out(m.Array[self.num_banks, m.Bits[1]]),
            io_to_bank_wr_data=m.Out(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
            io_to_bank_wr_data_bit_sel=m.Out(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
            io_to_bank_wr_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),

            io_to_bank_rd_en=m.Out(m.Array[self.num_banks, m.Bits[1]]),
            io_to_bank_rd_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),
            bank_to_io_rd_data=m.In(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),

            io_ctrl_switch_sel=m.In(TArray),
            adgn_addr=m.In(m.Array[self.num_io_channels, m.Bits[GLB_ADDR_WIDTH]]),
            adgn_wr_en=m.In(m.Array[self.num_io_channels, m.Bits[1]]),
            adgn_wr_data=m.In(m.Array[self.num_io_channels, m.Bits[BANK_DATA_WIDTH]]),
            adgn_wr_data_bit_sel=m.In(m.Array[self.num_io_channels, m.Bits[BANK_DATA_WIDTH]]),

            adgn_rd_en=m.In(m.Array[self.num_io_channels, m.Bits[1]]),
            adgn_rd_data=m.Out(m.Array[self.num_io_channels, m.Bits[BANK_DATA_WIDTH]]),
            adgn_cgra_done_pulse=m.In(m.Array[self.num_io_channels, m.Bit]),
        )

        # wr_en, wr_data, wr_data_bit_sel channels chain mux
        bank_wr_en_int = [m.Bit]*self.num_banks
        bank_wr_data_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        bank_wr_data_bit_sel_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_wr_en_int[0] = _ternary(self, 1,
                                                 self.ports.adgn_wr_en[0],
                                                 Const(0),
                                                 self.ports.io_ctrl_switch_sel[0][0])
                    bank_wr_data_int[0] = _ternary(self,
                                                   BANK_DATA_WIDTH,
                                                   self.ports.adgn_wr_data[0],
                                                   Const(0),
                                                   self.ports.io_ctrl_switch_sel[0][0])
                    bank_wr_data_bit_sel_int[0] = _ternary(self,
                                                           BANK_DATA_WIDTH,
                                                           self.ports.adgn_wr_data_bit_sel[0],
                                                           Const(0),
                                                           self.ports.io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_wr_en_int[idx] = _ternary(self, 1,
                                                   self.ports.adgn_wr_en[j],
                                                   bank_wr_en_int[idx - 1],
                                                   self.ports.io_ctrl_switch_sel[j][k])
                    bank_wr_data_int[idx] = _ternary(self, BANK_DATA_WIDTH,
                                                     self.ports.adgn_wr_data[j],
                                                     bank_wr_data_int[idx-1],
                                                     self.ports.io_ctrl_switch_sel[j][k])
                    bank_wr_data_bit_sel_int[idx] = _ternary(self,
                                                             BANK_DATA_WIDTH,
                                                             self.ports.adgn_wr_data_bit_sel[j],
                                                             bank_wr_data_bit_sel_int[idx-1],
                                                             self.ports.io_ctrl_switch_sel[j][k])

        # address channel chain mux
        bank_addr_int = [m.Bits[GLB_ADDR_WIDTH]]*self.num_banks
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_addr_int[0] = _ternary(self, GLB_ADDR_WIDTH,
                                                self.ports.adgn_addr[0],
                                                Const(0),
                                                self.ports.io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_addr_int[idx] = _ternary(self,
                                                  GLB_ADDR_WIDTH,
                                                  self.ports.adgn_addr[j],
                                                  bank_addr_int[idx-1],
                                                  self.ports.io_ctrl_switch_sel[j][k])

        # rd_en channel chain mux
        bank_rd_en_int = [m.Bit]*self.num_banks
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_rd_en_int[0] = _ternary(self, 1,
                                                 self.ports.adgn_rd_en[0],
                                                 Const(0),
                                                 self.ports.io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_rd_en_int[idx] = _ternary(self, 1,
                                                   self.ports.adgn_rd_en[j],
                                                   bank_rd_en_int[idx - 1],
                                                   self.ports.io_ctrl_switch_sel[j][k])

        # clk_en
        not_ = FromMagma(mantle.DefineNegate(1))
        self.wire(not_.ports.I, self.ports.stall)
        clk_en = not_.ports.O[0]


        # output wr_en
        for i in range(self.num_banks):
            eq = FromMagma(mantle.DefineEQ(GLB_ADDR_WIDTH-BANK_ADDR_WIDTH))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(bank_addr_int[i][BANK_ADDR_WIDTH:GLB_ADDR_WIDTH], eq.ports.I1)
            self.wire(Const(i), eq.ports.I0)
            self.wire(and_.ports.I0, bank_wr_en_int[i])
            self.wire(and_.ports.I1[0], eq.ports.O)
            self.wire(self.ports.io_to_bank_wr_en[i], and_.ports.O)

        # output wr_addr
        for i in range(self.num_banks):
            self.wire(self.ports.io_to_bank_wr_addr[i], bank_addr_int[i][0:BANK_ADDR_WIDTH])

        # output wr_data, wr_data_bit_sel
        for i in range(self.num_banks):
            self.wire(self.ports.io_to_bank_wr_data[i], bank_wr_data_int[i])
            self.wire(self.ports.io_to_bank_wr_data_bit_sel[i], bank_wr_data_bit_sel_int[i])

        # output rd_en
        io_to_bank_rd_en = [m.Bits[1]]*self.num_banks
        for i in range(self.num_banks):
            eq = FromMagma(mantle.DefineEQ(GLB_ADDR_WIDTH-BANK_ADDR_WIDTH))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(bank_addr_int[i][BANK_ADDR_WIDTH:GLB_ADDR_WIDTH], eq.ports.I1)
            self.wire(Const(i), eq.ports.I0)
            self.wire(and_.ports.I0, bank_rd_en_int[i])
            self.wire(and_.ports.I1[0], eq.ports.O)
            self.wire(self.ports.io_to_bank_rd_en[i], and_.ports.O)
            io_to_bank_rd_en[i] = and_.ports.O

        # rd_en pipeline
        io_to_bank_rd_en_d2 = [m.Bits[1]]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(1, has_ce=True, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.CLK)
            self.wire(clk_en, pipeline_reg_d1.ports.CE)
            self.wire(io_to_bank_rd_en[i], pipeline_reg_d1.ports.I)

            pipeline_reg_d2 = FromMagma(mantle.DefineRegister(1, has_ce=True, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d2.ports.CLK)
            self.wire(clk_en, pipeline_reg_d2.ports.CE)
            self.wire(pipeline_reg_d1.ports.O, pipeline_reg_d2.ports.I)
            io_to_bank_rd_en_d2[i] = pipeline_reg_d2.ports.O

        # output rd_addr
        for i in range(self.num_banks):
            self.wire(self.ports.io_to_bank_rd_addr[i], bank_addr_int[i][0:BANK_ADDR_WIDTH])

        # rd_data channel pipeline
        bank_to_io_rd_data_d1 = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(BANK_DATA_WIDTH,
                                                              has_ce=True,
                                                              has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.CLK)
            self.wire(clk_en, pipeline_reg_d1.ports.CE)
            self.wire(self.ports.bank_to_io_rd_data[i], pipeline_reg_d1.ports.I)
            bank_to_io_rd_data_d1[i] = pipeline_reg_d1.ports.O

        # rd_data channel
        bank_rd_data_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for i in reversed(range(self.num_banks)):
            if i == (self.num_banks - 1):
                bank_rd_data_int[self.num_banks-1] = _ternary(self, BANK_DATA_WIDTH,
                                             bank_to_io_rd_data_d1[self.num_banks-1],
                                             Const(0),
                                             io_to_bank_rd_en_d2[self.num_banks-1])
            else:
                bank_rd_data_int[i] = _ternary(self, BANK_DATA_WIDTH,
                                             bank_to_io_rd_data_d1[i],
                                             bank_rd_data_int[i+1],
                                             io_to_bank_rd_en_d2[i])

        # output adgn_data
        priority_encoder_def=m.DefineFromVerilogFile("./priority_encoder.sv")[0]
        adgn_rd_data=m.Out(m.Array[self.num_io_channels, m.Bits[BANK_DATA_WIDTH]]),
        for j in range(self.num_io_channels):
            priority_encoder = FromMagma(priority_encoder_def)
            self.wire(priority_encoder.ports.data_0, bank_rd_data_int[self.banks_per_io*j])
            self.wire(priority_encoder.ports.data_1, bank_rd_data_int[self.banks_per_io*j+1])
            self.wire(priority_encoder.ports.data_2, bank_rd_data_int[self.banks_per_io*j+2])
            self.wire(priority_encoder.ports.data_3, bank_rd_data_int[self.banks_per_io*j+3])
            for k in range(self.banks_per_io):
                self.wire(priority_encoder.ports.sel[k], self.ports.io_ctrl_switch_sel[j][k][0])
            self.wire(self.ports.adgn_rd_data[j], priority_encoder.ports.data_out)

        for i in range(self.num_io_channels):
            self.add_config(f"io_ctrl_mode_{i}", 2)
            self.add_config(f"io_ctrl_start_addr_{i}", GLB_ADDR_WIDTH)
            self.add_config(f"io_ctrl_num_words_{i}", GLB_ADDR_WIDTH)
            self.add_config(f"io_ctrl_switch_sel_{i}", self.num_banks)
            self.add_config(f"io_ctrl_done_delay_{i}", 32)
        self._setup_config

        # cgra_done_pulse
        cgra_done_pulse_d1 = [m.Bit]*self.num_io_channels
        pulse_reg_def = mantle.DefineRegister(1, has_ce=False, has_async_reset=True)
        or_ = FromMagma(mantle.DefineOr(self.num_io_channels, 1))
        for i in range(self.num_io_channels):
            pulse_reg = FromMagma(pulse_reg_def)
            self.wire(self.ports.clk, pulse_reg.ports.clk)
            self.wire(self.ports.adgn_cgra_done_pulse[i], pulse_reg.ports.I[0])
            cgra_done_pulse_d1[i] = pulse_reg.ports.O[0]
            self.wire(or_.ports[f"I{i}"], pulse_reg.ports.O)

        self.wire(self.ports.cgra_done_pulse, or_.ports.O[0])


    def name(self):
        return f"IoController_{self.num_banks}"


io_controller = IoController(32, 8)
print (repr(io_controller.circuit()))
m.compile("io_controller", io_controller.circuit(), output="coreir-verilog")
