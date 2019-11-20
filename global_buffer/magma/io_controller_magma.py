import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.common.mux_with_default import MuxWithDefaultWrapper
from global_buffer.magma.io_address_generator_magma import IoAddressGenerator

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
            select=m.In(m.Bit),
            out=m.Out(T)
        )

        mux = MuxWrapper(2, self.width,)
        self.wire(self.ports.first, mux.ports.I[0])
        self.wire(self.ports.second, mux.ports.I[1])
        self.wire(self.ports.select, mux.ports.S[0])
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

        self.num_banks = num_banks
        self.num_io_channels = num_io_channels
        self.banks_per_io = int(num_banks / num_io_channels)
        super().__init__()

        self.add_ports(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),
            stall=m.In(m.Bits[1]),
            cgra_start_pulse=m.In(m.Bit),
            cgra_done_pulse=m.Out(m.Bit),

            # configuration
            config_en=m.In(m.Bit),
            config_wr=m.In(m.Bit),
            config_rd=m.In(m.Bit),
            config_addr=m.In(m.Bits[8]),
            config_wr_data=m.In(m.Bits[32]),
            config_rd_data=m.Out(m.Bits[32]),

            io_to_bank_wr_en=m.Out(m.Array[self.num_banks, m.Bits[1]]),
            io_to_bank_wr_data=m.Out(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
            io_to_bank_wr_data_bit_sel=m.Out(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),
            io_to_bank_wr_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),

            io_to_bank_rd_en=m.Out(m.Array[self.num_banks, m.Bits[1]]),
            io_to_bank_rd_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),
            bank_to_io_rd_data=m.In(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),

            cgra_to_io_wr_en=m.In(m.Array[self.num_io_channels, m.Bit]),
            cgra_to_io_rd_en=m.In(m.Array[self.num_io_channels, m.Bit]),
            io_to_cgra_rd_data_valid=m.Out(m.Array[self.num_io_channels, m.Bit]),
            cgra_to_io_wr_data=m.In(m.Array[self.num_io_channels, m.Bits[16]]),
            io_to_cgra_rd_data=m.Out(m.Array[self.num_io_channels, m.Bits[16]]),
            cgra_to_io_addr_high=m.In(m.Array[self.num_io_channels, m.Bits[16]]),
            cgra_to_io_addr_low=m.In(m.Array[self.num_io_channels, m.Bits[16]]),
        )

        # configuration
        # configuration feature
        config_feature=self.ports.config_addr[4:8]
        config_en_io_ctrl=[m.Bit]*self.num_io_channels
        for i in range(self.num_io_channels):
            eq = FromMagma(mantle.DefineEQ(4))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(Const(i), eq.ports.I0)
            self.wire(config_feature, eq.ports.I1)
            self.wire(and_.ports.I1[0], eq.ports.O)
            self.wire(and_.ports.I0[0], self.ports.config_en)
            config_en_io_ctrl[i]=and_.ports.O

        # configuration reg
        config_reg=self.ports.config_addr[0:4]
        for i in range(5):
            eq = FromMagma(mantle.DefineEQ(4))
            self.wire(Const(i), eq.ports.I0)
            self.wire(config_reg, eq.ports.I1)
            if (i==0):
                io_ctrl_mode_en=eq.ports.O
            elif (i==1):
                io_ctrl_start_addr_en=eq.ports.O
            elif (i==2):
                io_ctrl_num_words_en=eq.ports.O
            elif (i==3):
                io_ctrl_switch_sel_en=eq.ports.O
            else:
                io_ctrl_done_delay_en=eq.ports.O

        # io_ctrl_mode
        io_ctrl_mode=[m.Bits[2]]*self.num_io_channels
        for i in range(self.num_io_channels):
            reg_ = FromMagma(mantle.DefineRegister(2, has_ce=True, has_async_reset=True))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(and_.ports.I0, config_en_io_ctrl[i])
            self.wire(and_.ports.I1[0], self.ports.config_wr)
            self.wire(io_ctrl_mode_en, reg_.ports.CE)
            self.wire(self.ports.clk, reg_.ports.CLK)
            self.wire(self.ports.config_wr_data[0:2], reg_.ports.I)
            io_ctrl_mode[i] = reg_.ports.O

        # io_ctrl_start_addr
        io_ctrl_start_addr=[m.Bits[32]]*self.num_io_channels
        for i in range(self.num_io_channels):
            reg_ = FromMagma(mantle.DefineRegister(32, has_ce=True, has_async_reset=True))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(and_.ports.I0, config_en_io_ctrl[i])
            self.wire(and_.ports.I1[0], self.ports.config_wr)
            self.wire(io_ctrl_start_addr_en, reg_.ports.CE)
            self.wire(self.ports.clk, reg_.ports.CLK)
            self.wire(self.ports.config_wr_data[0:32], reg_.ports.I)
            io_ctrl_start_addr[i]=reg_.ports.O

        # io_ctrl_num_words
        io_ctrl_num_words=[m.Bits[32]]*self.num_io_channels
        for i in range(self.num_io_channels):
            reg_ = FromMagma(mantle.DefineRegister(32, has_ce=True, has_async_reset=True))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(and_.ports.I0, config_en_io_ctrl[i])
            self.wire(and_.ports.I1[0], self.ports.config_wr)
            self.wire(io_ctrl_num_words_en, reg_.ports.CE)
            self.wire(self.ports.clk, reg_.ports.CLK)
            self.wire(self.ports.config_wr_data[0:32], reg_.ports.I)
            io_ctrl_num_words[i]=reg_.ports.O

        # io_ctrl_switch_sel
        io_ctrl_switch_sel=[m.Array[self.banks_per_io, m.Bits[1]]]*self.num_io_channels
        for i in range(self.num_io_channels):
            reg_ = FromMagma(mantle.DefineRegister(4, has_ce=True, has_async_reset=True))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(and_.ports.I0, config_en_io_ctrl[i])
            self.wire(and_.ports.I1[0], self.ports.config_wr)
            self.wire(io_ctrl_switch_sel_en, reg_.ports.CE)
            self.wire(self.ports.clk, reg_.ports.CLK)
            self.wire(self.ports.config_wr_data[0:4], reg_.ports.I)
            io_ctrl_switch_sel[i]=reg_.ports.O

        # io_ctrl_done_delay
        io_ctrl_done_delay=[m.Bits[32]]*self.num_io_channels
        for i in range(self.num_io_channels):
            reg_ = FromMagma(mantle.DefineRegister(32, has_ce=True, has_async_reset=True))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(and_.ports.I0, config_en_io_ctrl[i])
            self.wire(and_.ports.I1[0], self.ports.config_wr)
            self.wire(io_ctrl_done_delay_en, reg_.ports.CE)
            self.wire(self.ports.clk, reg_.ports.CLK)
            self.wire(self.ports.config_wr_data[0:32], reg_.ports.I)
            io_ctrl_done_delay[i]=reg_.ports.O

        # configuration reg read
        config_rd_reg=[m.Bits[32]]*self.num_io_channels
        for i in range(self.num_io_channels):
            reg_read_data_mux = MuxWithDefaultWrapper(5, 32, 4, 0)
            self.wire(Const(1), reg_read_data_mux.ports.EN)
            self.wire(config_reg, reg_read_data_mux.ports.S)
            self.wire(reg_read_data_mux.ports.I[0][0:2], io_ctrl_mode[i])
            self.wire(reg_read_data_mux.ports.I[0][2:32], Const(0))
            self.wire(reg_read_data_mux.ports.I[1], io_ctrl_start_addr[i])
            self.wire(reg_read_data_mux.ports.I[2], io_ctrl_num_words[i])
            self.wire(reg_read_data_mux.ports.I[3][0:4], io_ctrl_switch_sel[i])
            self.wire(reg_read_data_mux.ports.I[3][4:32], Const(0))
            self.wire(reg_read_data_mux.ports.I[4], io_ctrl_done_delay[i])
            config_rd_reg[i]=reg_read_data_mux.ports.O

        # configuration feature read
        encoder = FromMagma(mantle.DefineEncoder(self.num_io_channels))
        for i in range(self.num_io_channels):
            self.wire(encoder.ports.I[i], config_en_io_ctrl[i][0])

        # replace 3 with clog(self.num_io_channels)
        feat_read_data_mux = MuxWithDefaultWrapper(self.num_io_channels, 32, 4, 0)
        for i in range(self.num_io_channels):
            self.wire(encoder.ports.O, feat_read_data_mux.ports.S[0:3])
            self.wire(Const(0), feat_read_data_mux.ports.S[3])
            self.wire(self.ports.config_rd, feat_read_data_mux.ports.EN[0])
            self.wire(feat_read_data_mux.ports.I[i], config_rd_reg[i])

        self.wire(feat_read_data_mux.ports.O, self.ports.config_rd_data)

        # address generator output
        io_adgn = [None]*self.num_io_channels
        for i in range(self.num_io_channels):
            io_adgn[i] = IoAddressGenerator()

        adgn_wr_en = [m.Bits[1]]*self.num_io_channels
        adgn_rd_en = [m.Bits[1]]*self.num_io_channels
        adgn_addr= [m.Bits[GLB_ADDR_WIDTH]]*self.num_io_channels
        adgn_wr_data=[m.Bits[BANK_DATA_WIDTH]]*self.num_io_channels
        adgn_wr_data_bit_sel=[m.Bits[BANK_DATA_WIDTH]]*self.num_io_channels
        for i in range(self.num_io_channels):
            adgn_wr_en[i]=io_adgn[i].ports.io_to_bank_wr_en
            adgn_addr[i]=io_adgn[i].ports.io_to_bank_addr
            adgn_wr_data[i]=io_adgn[i].ports.io_to_bank_wr_data
            adgn_wr_data_bit_sel[i]=io_adgn[i].ports.io_to_bank_wr_data_bit_sel
            adgn_rd_en[i]=io_adgn[i].ports.io_to_bank_rd_en

        # wr_en, wr_data, wr_data_bit_sel channels chain mux
        bank_wr_en_int = [m.Bit]*self.num_banks
        bank_wr_data_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        bank_wr_data_bit_sel_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_wr_en_int[0] = _ternary(self, 1,
                                                 adgn_wr_en[0],
                                                 Const(0),
                                                 io_ctrl_switch_sel[0][0])
                    bank_wr_data_int[0] = _ternary(self,
                                                   BANK_DATA_WIDTH,
                                                   adgn_wr_data[0],
                                                   Const(0),
                                                   io_ctrl_switch_sel[0][0])
                    bank_wr_data_bit_sel_int[0] = _ternary(self,
                                                           BANK_DATA_WIDTH,
                                                           adgn_wr_data_bit_sel[0],
                                                           Const(0),
                                                           io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_wr_en_int[idx] = _ternary(self, 1,
                                                   adgn_wr_en[j],
                                                   bank_wr_en_int[idx - 1],
                                                   io_ctrl_switch_sel[j][k])
                    bank_wr_data_int[idx] = _ternary(self, BANK_DATA_WIDTH,
                                                     adgn_wr_data[j],
                                                     bank_wr_data_int[idx-1],
                                                     io_ctrl_switch_sel[j][k])
                    bank_wr_data_bit_sel_int[idx] = _ternary(self,
                                                             BANK_DATA_WIDTH,
                                                             adgn_wr_data_bit_sel[j],
                                                             bank_wr_data_bit_sel_int[idx-1],
                                                             io_ctrl_switch_sel[j][k])

        # address channel chain mux
        bank_addr_int = [m.Bits[GLB_ADDR_WIDTH]]*self.num_banks
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_addr_int[0] = _ternary(self, GLB_ADDR_WIDTH,
                                                adgn_addr[0],
                                                Const(0),
                                                io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_addr_int[idx] = _ternary(self,
                                                  GLB_ADDR_WIDTH,
                                                  adgn_addr[j],
                                                  bank_addr_int[idx-1],
                                                  io_ctrl_switch_sel[j][k])

        # rd_en channel chain mux
        bank_rd_en_int = [m.Bit]*self.num_banks
        for j in range(self.num_io_channels):
            for k in range(self.banks_per_io):
                if j == 0 and k == 0:
                    bank_rd_en_int[0] = _ternary(self, 1,
                                                 adgn_rd_en[0],
                                                 Const(0),
                                                 io_ctrl_switch_sel[0][0])
                else:
                    idx = j * self.banks_per_io + k
                    bank_rd_en_int[idx] = _ternary(self, 1,
                                                   adgn_rd_en[j],
                                                   bank_rd_en_int[idx - 1],
                                                   io_ctrl_switch_sel[j][k])

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
        io_to_bank_rd_en_d2 = [m.Bit]*self.num_banks
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
                                             io_to_bank_rd_en_d2[self.num_banks-1][0])
            else:
                bank_rd_data_int[i] = _ternary(self, BANK_DATA_WIDTH,
                                             bank_to_io_rd_data_d1[i],
                                             bank_rd_data_int[i+1],
                                             io_to_bank_rd_en_d2[i][0])

        # rd_data_valid
        bank_rd_data_valid_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for i in reversed(range(self.num_banks)):
            if i == (self.num_banks - 1):
                bank_rd_data_valid_int[self.num_banks-1] = _ternary(self, 1,
                                             io_to_bank_rd_en_d2[self.num_banks-1],
                                             Const(0),
                                             io_to_bank_rd_en_d2[self.num_banks-1][0])
            else:
                bank_rd_data_valid_int[i] = _ternary(self, 1,
                                             io_to_bank_rd_en_d2[i],
                                             bank_rd_data_valid_int[i+1],
                                             io_to_bank_rd_en_d2[i][0])

        # output rd_data
        priority_encoder_def=m.DefineFromVerilogFile("./global_buffer/magma/priority_encoder.sv")[0]
        adgn_rd_data=[m.Bits[BANK_DATA_WIDTH]]*self.num_io_channels
        for j in range(self.num_io_channels):
            priority_encoder = FromMagma(priority_encoder_def)
            self.wire(priority_encoder.ports.data_0, bank_rd_data_int[self.banks_per_io*j])
            self.wire(priority_encoder.ports.data_1, bank_rd_data_int[self.banks_per_io*j+1])
            self.wire(priority_encoder.ports.data_2, bank_rd_data_int[self.banks_per_io*j+2])
            self.wire(priority_encoder.ports.data_3, bank_rd_data_int[self.banks_per_io*j+3])
            for k in range(self.banks_per_io):
                self.wire(priority_encoder.ports.sel[k], io_ctrl_switch_sel[j][k])
            adgn_rd_data[j]=priority_encoder.ports.data_out

        # output rd_data_valid
        priority_encoder_def=m.DefineFromVerilogFile("./global_buffer/magma/priority_encoder_0.sv")[0]
        adgn_rd_data_valid=[m.Bit]*self.num_io_channels
        for j in range(self.num_io_channels):
            priority_encoder = FromMagma(priority_encoder_def)
            self.wire(priority_encoder.ports.data_0, bank_rd_data_valid_int[self.banks_per_io*j])
            self.wire(priority_encoder.ports.data_1, bank_rd_data_valid_int[self.banks_per_io*j+1])
            self.wire(priority_encoder.ports.data_2, bank_rd_data_valid_int[self.banks_per_io*j+2])
            self.wire(priority_encoder.ports.data_3, bank_rd_data_valid_int[self.banks_per_io*j+3])
            for k in range(self.banks_per_io):
                self.wire(priority_encoder.ports.sel[k], io_ctrl_switch_sel[j][k])
            adgn_rd_data_valid[j]= priority_encoder.ports.data_out

        pulse_reg_def = mantle.DefineRegister(1, has_ce=False, has_async_reset=True)
        or_ = FromMagma(mantle.DefineOr(self.num_io_channels, 1))

        # address generator
        for i in range(self.num_io_channels):
            self.wire(io_adgn[i].ports.clk, self.ports.clk)
            self.wire(io_adgn[i].ports.reset, self.ports.reset)
            self.wire(io_adgn[i].ports.clk_en, clk_en)
            self.wire(io_adgn[i].ports.cgra_start_pulse, self.ports.cgra_start_pulse)

            self.wire(io_adgn[i].ports.start_addr, io_ctrl_start_addr[i])
            self.wire(io_adgn[i].ports.num_words, io_ctrl_num_words[i])
            self.wire(io_adgn[i].ports.mode, io_ctrl_mode[i])
            self.wire(io_adgn[i].ports.done_delay, io_ctrl_done_delay[i])

            self.wire(io_adgn[i].ports.cgra_to_io_wr_en, self.ports.cgra_to_io_wr_en[i])
            self.wire(io_adgn[i].ports.cgra_to_io_rd_en, self.ports.cgra_to_io_wr_en[i])
            self.wire(io_adgn[i].ports.io_to_cgra_rd_data_valid, self.ports.io_to_cgra_rd_data_valid[i])
            self.wire(io_adgn[i].ports.cgra_to_io_addr_high, self.ports.cgra_to_io_addr_high[i])
            self.wire(io_adgn[i].ports.cgra_to_io_addr_low, self.ports.cgra_to_io_addr_low[i])
            self.wire(io_adgn[i].ports.cgra_to_io_wr_data, self.ports.cgra_to_io_wr_data[i])
            self.wire(io_adgn[i].ports.io_to_cgra_rd_data, self.ports.io_to_cgra_rd_data[i])

            self.wire(io_adgn[i].ports.bank_to_io_rd_data, adgn_rd_data[i])
            self.wire(io_adgn[i].ports.bank_to_io_rd_data_valid, adgn_rd_data_valid[i])

            # cgra_done_pulse
            pulse_reg = FromMagma(pulse_reg_def)
            self.wire(self.ports.clk, pulse_reg.ports.clk)
            self.wire(io_adgn[i].ports.cgra_done_pulse, pulse_reg.ports.I[0])
            self.wire(or_.ports[f"I{i}"], pulse_reg.ports.O)

        self.wire(self.ports.cgra_done_pulse, or_.ports.O[0])


    def name(self):
        return f"IoController_{self.num_banks}"


io_controller = IoController(32, 8)
m.compile("io_controller", io_controller.circuit(), output="coreir-verilog")
