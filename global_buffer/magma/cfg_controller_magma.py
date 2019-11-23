import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.common.mux_with_default import MuxWithDefaultWrapper
from global_buffer.magma.cfg_address_generator_magma import CfgAddressGenerator

GLB_ADDR_WIDTH = 32
BANK_ADDR_WIDTH = 17
BANK_DATA_WIDTH = 64
CFG_DATA_WIDTH = 32
CFG_ADDR_WIDTH = 32

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


class CfgController(Generator):
    def __init__(self, num_banks, num_cfg_channels):

        self.num_banks = num_banks
        self.num_cfg_channels = num_cfg_channels
        self.banks_per_cfg = int(num_banks / num_cfg_channels)
        super().__init__()

        self.add_ports(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),
            config_start_pulse=m.In(m.Bit),
            config_done_pulse=m.Out(m.Bit),

            # configuration
            config_en=m.In(m.Bit),
            config_wr=m.In(m.Bit),
            config_rd=m.In(m.Bit),
            config_addr=m.In(m.Bits[8]),
            config_wr_data=m.In(m.Bits[32]),
            config_rd_data=m.Out(m.Bits[32]),

            glc_to_cgra_cfg_wr=m.In(m.Bit),
            glc_to_cgra_cfg_rd=m.In(m.Bit),
            glc_to_cgra_cfg_addr=m.In(m.Bits[CFG_ADDR_WIDTH]),
            glc_to_cgra_cfg_data=m.In(m.Bits[CFG_DATA_WIDTH]),

            cfg_to_bank_rd_en=m.Out(m.Array[self.num_banks, m.Bits[1]]),
            cfg_to_bank_rd_addr=m.Out(m.Array[self.num_banks, m.Bits[BANK_ADDR_WIDTH]]),
            bank_to_cfg_rd_data=m.In(m.Array[self.num_banks, m.Bits[BANK_DATA_WIDTH]]),

            glb_to_cgra_cfg_wr=m.Out(m.Array[self.num_cfg_channels, m.Bit]),
            glb_to_cgra_cfg_rd=m.Out(m.Array[self.num_cfg_channels, m.Bit]),
            glb_to_cgra_cfg_addr=m.Out(m.Array[self.num_cfg_channels, m.Bits[CFG_ADDR_WIDTH]]),
            glb_to_cgra_cfg_data=m.Out(m.Array[self.num_cfg_channels, m.Bits[CFG_DATA_WIDTH]]),
        )

        self.channel_insts = [[] for channel_num in range(self.num_cfg_channels)]
        # configuration
        # configuration feature
        config_feature=self.ports.config_addr[4:8]
        config_en_cfg_ctrl=[m.Bit]*self.num_cfg_channels
        eq_def = mantle.DefineEQ(4)
        and_def = mantle.DefineAnd(2, 1)
        for i in range(self.num_cfg_channels):
            eq = FromMagma(eq_def)
            and_ = FromMagma(and_def)
            self.wire(Const(i), eq.ports.I0)
            self.wire(config_feature, eq.ports.I1)
            self.wire(and_.ports.I1[0], eq.ports.O)
            self.wire(and_.ports.I0[0], self.ports.config_en)
            config_en_cfg_ctrl[i]=and_.ports.O
            self.channel_insts[i].extend([eq, and_])

        # configuration reg
        config_reg=self.ports.config_addr[0:4]
        for i in range(3):
            eq = FromMagma(eq_def)
            self.wire(Const(i), eq.ports.I0)
            self.wire(config_reg, eq.ports.I1)
            if (i==0):
                cfg_ctrl_start_addr_en=eq.ports.O
            elif (i==1):
                cfg_ctrl_num_words_en=eq.ports.O
            else:
                cfg_ctrl_switch_sel_en=eq.ports.O

        # cfg_ctrl_start_addr
        cfg_ctrl_start_addr=[m.Bits[32]]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            reg_ = FromMagma(mantle.DefineRegister(32, has_ce=True, has_async_reset=True))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(and_.ports.I0, config_en_cfg_ctrl[i])
            self.wire(and_.ports.I1[0], self.ports.config_wr)
            self.wire(cfg_ctrl_start_addr_en, reg_.ports.CE)
            self.wire(self.ports.clk, reg_.ports.CLK)
            self.wire(self.ports.config_wr_data[0:32], reg_.ports.I)
            cfg_ctrl_start_addr[i]=reg_.ports.O
            self.channel_insts[i].extend([reg_, and_])

        # cfg_ctrl_num_words
        cfg_ctrl_num_words=[m.Bits[32]]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            reg_ = FromMagma(mantle.DefineRegister(32, has_ce=True, has_async_reset=True))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(and_.ports.I0, config_en_cfg_ctrl[i])
            self.wire(and_.ports.I1[0], self.ports.config_wr)
            self.wire(cfg_ctrl_num_words_en, reg_.ports.CE)
            self.wire(self.ports.clk, reg_.ports.CLK)
            self.wire(self.ports.config_wr_data[0:32], reg_.ports.I)
            cfg_ctrl_num_words[i]=reg_.ports.O
            self.channel_insts[i].extend([reg_, and_])

        # cfg_ctrl_switch_sel
        cfg_ctrl_switch_sel=[m.Array[self.banks_per_cfg, m.Bits[1]]]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            reg_ = FromMagma(mantle.DefineRegister(4, has_ce=True, has_async_reset=True))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(and_.ports.I0, config_en_cfg_ctrl[i])
            self.wire(and_.ports.I1[0], self.ports.config_wr)
            self.wire(cfg_ctrl_switch_sel_en, reg_.ports.CE)
            self.wire(self.ports.clk, reg_.ports.CLK)
            self.wire(self.ports.config_wr_data[0:4], reg_.ports.I)
            cfg_ctrl_switch_sel[i]=reg_.ports.O
            self.channel_insts[i].extend([reg_, and_])

        # configuration reg read
        config_rd_reg=[m.Bits[32]]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            reg_read_data_mux = MuxWithDefaultWrapper(3, 32, 4, 0)
            self.wire(Const(1), reg_read_data_mux.ports.EN)
            self.wire(config_reg, reg_read_data_mux.ports.S)
            self.wire(reg_read_data_mux.ports.I[0], cfg_ctrl_start_addr[i])
            self.wire(reg_read_data_mux.ports.I[1], cfg_ctrl_num_words[i])
            self.wire(reg_read_data_mux.ports.I[2][0:4], cfg_ctrl_switch_sel[i])
            self.wire(reg_read_data_mux.ports.I[2][4:32], Const(0))
            config_rd_reg[i]=reg_read_data_mux.ports.O
            self.channel_insts[i].append(reg_read_data_mux)

        # configuration feature read
        encoder = FromMagma(mantle.DefineEncoder(self.num_cfg_channels))
        for i in range(self.num_cfg_channels):
            self.wire(encoder.ports.I[i], config_en_cfg_ctrl[i][0])

        # replace 3 with clog(self.num_cfg_channels)
        feat_read_data_mux = MuxWithDefaultWrapper(self.num_cfg_channels, 32, 4, 0)
        for i in range(self.num_cfg_channels):
            self.wire(encoder.ports.O, feat_read_data_mux.ports.S[0:3])
            self.wire(Const(0), feat_read_data_mux.ports.S[3])
            self.wire(self.ports.config_rd, feat_read_data_mux.ports.EN[0])
            self.wire(feat_read_data_mux.ports.I[i], config_rd_reg[i])

        self.wire(feat_read_data_mux.ports.O, self.ports.config_rd_data)

        # address generator output
        cfg_adgn = [None]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            cfg_adgn[i] = CfgAddressGenerator()
            self.channel_insts[i].append(cfg_adgn[i])

        adgn_rd_en = [m.Bits[1]]*self.num_cfg_channels
        adgn_addr= [m.Bits[GLB_ADDR_WIDTH]]*self.num_cfg_channels
        adgn_config_wr = [m.Bit]*self.num_cfg_channels
        adgn_config_addr = [m.Bits[CFG_ADDR_WIDTH]]*self.num_cfg_channels
        adgn_config_data = [m.Bits[CFG_DATA_WIDTH]]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            adgn_rd_en[i]=cfg_adgn[i].ports.cfg_to_bank_rd_en
            adgn_addr[i]=cfg_adgn[i].ports.cfg_to_bank_addr
            adgn_config_wr[i]=cfg_adgn[i].ports.cfg_to_cgra_config_wr
            adgn_config_addr[i]=cfg_adgn[i].ports.cfg_to_cgra_config_addr
            adgn_config_data[i]=cfg_adgn[i].ports.cfg_to_cgra_config_data

        # address channel chain mux
        bank_addr_int = [m.Bits[GLB_ADDR_WIDTH]]*self.num_banks
        for j in range(self.num_cfg_channels):
            for k in range(self.banks_per_cfg):
                idx = j * self.banks_per_cfg + k
                if j == 0 and k == 0:
                    bank_addr_int[0] = _ternary(self, GLB_ADDR_WIDTH,
                                                adgn_addr[0],
                                                Const(0),
                                                cfg_ctrl_switch_sel[0][0])
                else:
                    bank_addr_int[idx] = _ternary(self,
                                                  GLB_ADDR_WIDTH,
                                                  adgn_addr[j],
                                                  bank_addr_int[idx-1],
                                                  cfg_ctrl_switch_sel[j][k])
                self.channel_insts[j].append(bank_addr_int[idx].owner())

        # rd_en channel chain mux
        bank_rd_en_int = [m.Bit]*self.num_banks
        for j in range(self.num_cfg_channels):
            for k in range(self.banks_per_cfg):
                idx = j * self.banks_per_cfg + k
                if j == 0 and k == 0:
                    bank_rd_en_int[0] = _ternary(self, 1,
                                                 adgn_rd_en[0],
                                                 Const(0),
                                                 cfg_ctrl_switch_sel[0][0])
                else:
                    bank_rd_en_int[idx] = _ternary(self, 1,
                                                   adgn_rd_en[j],
                                                   bank_rd_en_int[idx - 1],
                                                   cfg_ctrl_switch_sel[j][k])

                self.channel_insts[j].append(bank_rd_en_int[idx].owner())

        # cfg_to_cgra_config_wr chain mux
        int_cfg_to_cgra_config_wr = [m.Bit]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            if i==0:
                int_cfg_to_cgra_config_wr[0] = adgn_config_wr[0]
            else:
                mux = MuxWrapper(2, 1,)
                eq = FromMagma(mantle.DefineEQ(self.banks_per_cfg))
                self.wire(Const(0), eq.ports.I0)
                self.wire(cfg_ctrl_switch_sel[i], eq.ports.I1)
                self.wire(adgn_config_wr[i], mux.ports.I[0][0])
                self.wire(int_cfg_to_cgra_config_wr[i-1], mux.ports.I[1][0])
                self.wire(eq.ports.O, mux.ports.S[0])
                int_cfg_to_cgra_config_wr[i]=mux.ports.O[0]
                self.channel_insts[i].extend([mux, eq])

        # cfg_to_cgra_config_addr chain mux
        int_cfg_to_cgra_config_addr = [m.Bits[CFG_ADDR_WIDTH]]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            if i==0:
                int_cfg_to_cgra_config_addr[0] = adgn_config_addr[0]
            else:
                mux = MuxWrapper(2, CFG_ADDR_WIDTH,)
                eq = FromMagma(mantle.DefineEQ(self.banks_per_cfg))
                self.wire(Const(0), eq.ports.I0)
                self.wire(cfg_ctrl_switch_sel[i], eq.ports.I1)
                self.wire(adgn_config_addr[i], mux.ports.I[0])
                self.wire(int_cfg_to_cgra_config_addr[i-1], mux.ports.I[1])
                self.wire(eq.ports.O, mux.ports.S[0])
                int_cfg_to_cgra_config_addr[i]=mux.ports.O
                self.channel_insts[i].extend([mux, eq])

        # cfg_to_cgra_config_data chain mux
        int_cfg_to_cgra_config_data = [m.Bits[CFG_DATA_WIDTH]]*self.num_cfg_channels
        for i in range(self.num_cfg_channels):
            if i==0:
                int_cfg_to_cgra_config_data[0] = adgn_config_data[0]
            else:
                mux = MuxWrapper(2, CFG_DATA_WIDTH,)
                eq = FromMagma(mantle.DefineEQ(self.banks_per_cfg))
                self.wire(Const(0), eq.ports.I0)
                self.wire(cfg_ctrl_switch_sel[i], eq.ports.I1)
                self.wire(adgn_config_data[i], mux.ports.I[0])
                self.wire(int_cfg_to_cgra_config_data[i-1], mux.ports.I[1])
                self.wire(eq.ports.O, mux.ports.S[0])
                int_cfg_to_cgra_config_data[i]=mux.ports.O
                self.channel_insts[i].extend([mux, eq])

        # config_rd
        for i in range(self.num_cfg_channels):
            self.wire(self.ports.glb_to_cgra_cfg_rd[i], self.ports.glc_to_cgra_cfg_rd)

        # config_wr
        for i in range(self.num_cfg_channels):
            or_ = FromMagma(mantle.DefineOr(2, 1))
            self.wire(or_.ports.I0[0], self.ports.glc_to_cgra_cfg_wr)
            self.wire(or_.ports.I1[0], int_cfg_to_cgra_config_wr[i])
            self.wire(self.ports.glb_to_cgra_cfg_wr[i], or_.ports.O[0])
            self.channel_insts[i].append(or_)

        # config_addr
        for i in range(self.num_cfg_channels):
            mux = MuxWrapper(2, CFG_ADDR_WIDTH,)
            or_ = FromMagma(mantle.DefineOr(2, 1))
            self.wire(or_.ports.I0[0], self.ports.glc_to_cgra_cfg_wr)
            self.wire(or_.ports.I1[0], self.ports.glc_to_cgra_cfg_rd)
            self.wire(int_cfg_to_cgra_config_addr[i], mux.ports.I[0])
            self.wire(self.ports.glc_to_cgra_cfg_addr, mux.ports.I[1])
            self.wire(or_.ports.O, mux.ports.S)
            self.wire(self.ports.glb_to_cgra_cfg_addr[i], mux.ports.O)
            self.channel_insts[i].extend([mux, or_])

        # config_data
        for i in range(self.num_cfg_channels):
            mux = MuxWrapper(2, CFG_DATA_WIDTH,)
            or_ = FromMagma(mantle.DefineOr(2, 1))
            self.wire(or_.ports.I0[0], self.ports.glc_to_cgra_cfg_wr)
            self.wire(or_.ports.I1[0], self.ports.glc_to_cgra_cfg_rd)
            self.wire(int_cfg_to_cgra_config_data[i], mux.ports.I[0])
            self.wire(self.ports.glc_to_cgra_cfg_data, mux.ports.I[1])
            self.wire(or_.ports.O, mux.ports.S)
            self.wire(self.ports.glb_to_cgra_cfg_data[i], mux.ports.O)
            self.channel_insts[i].extend([mux, or_])

        # output rd_en
        cfg_to_bank_rd_en = [m.Bits[1]]*self.num_banks
        for i in range(self.num_banks):
            eq = FromMagma(mantle.DefineEQ(GLB_ADDR_WIDTH-BANK_ADDR_WIDTH))
            and_ = FromMagma(mantle.DefineAnd(2, 1))
            self.wire(bank_addr_int[i][BANK_ADDR_WIDTH:GLB_ADDR_WIDTH], eq.ports.I1)
            self.wire(Const(i), eq.ports.I0)
            self.wire(and_.ports.I0, bank_rd_en_int[i])
            self.wire(and_.ports.I1[0], eq.ports.O)
            self.wire(self.ports.cfg_to_bank_rd_en[i], and_.ports.O)
            cfg_to_bank_rd_en[i] = and_.ports.O
            cfg_channel_idx = i // self.banks_per_cfg
            self.channel_insts[cfg_channel_idx].extend([eq, and_])

        # rd_en pipeline
        cfg_to_bank_rd_en_d2 = [m.Bit]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(1, has_ce=False, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
            self.wire(cfg_to_bank_rd_en[i], pipeline_reg_d1.ports.I)

            pipeline_reg_d2 = FromMagma(mantle.DefineRegister(1, has_ce=False, has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d2.ports.clk)
            self.wire(pipeline_reg_d1.ports.O, pipeline_reg_d2.ports.I)
            cfg_to_bank_rd_en_d2[i] = pipeline_reg_d2.ports.O
            cfg_channel_idx = i // self.banks_per_cfg
            self.channel_insts[cfg_channel_idx].extend([pipeline_reg_d1, pipeline_reg_d2])

        # output rd_addr
        for i in range(self.num_banks):
            self.wire(self.ports.cfg_to_bank_rd_addr[i], bank_addr_int[i][0:BANK_ADDR_WIDTH])

        # rd_data channel pipeline
        bank_to_cfg_rd_data_d1 = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for i in range(self.num_banks):
            pipeline_reg_d1 = FromMagma(mantle.DefineRegister(BANK_DATA_WIDTH,
                                                              has_ce=False,
                                                              has_async_reset=False))
            self.wire(self.ports.clk, pipeline_reg_d1.ports.clk)
            self.wire(self.ports.bank_to_cfg_rd_data[i], pipeline_reg_d1.ports.I)
            bank_to_cfg_rd_data_d1[i] = pipeline_reg_d1.ports.O
            cfg_channel_idx = i // self.banks_per_cfg
            self.channel_insts[cfg_channel_idx].append(pipeline_reg_d1)

        # rd_data channel
        bank_rd_data_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for i in reversed(range(self.num_banks)):
            if i == (self.num_banks - 1):
                bank_rd_data_int[self.num_banks-1] = _ternary(self, BANK_DATA_WIDTH,
                                             bank_to_cfg_rd_data_d1[self.num_banks-1],
                                             Const(0),
                                             cfg_to_bank_rd_en_d2[self.num_banks-1][0])
            else:
                bank_rd_data_int[i] = _ternary(self, BANK_DATA_WIDTH,
                                             bank_to_cfg_rd_data_d1[i],
                                             bank_rd_data_int[i+1],
                                             cfg_to_bank_rd_en_d2[i][0])
            cfg_channel_idx = i // self.banks_per_cfg
            self.channel_insts[cfg_channel_idx].append(bank_rd_data_int[i].owner())

        # rd_data_valid
        bank_rd_data_valid_int = [m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        for i in reversed(range(self.num_banks)):
            if i == (self.num_banks - 1):
                bank_rd_data_valid_int[self.num_banks-1] = _ternary(self, 1,
                                             cfg_to_bank_rd_en_d2[self.num_banks-1],
                                             Const(0),
                                             cfg_to_bank_rd_en_d2[self.num_banks-1][0])
            else:
                bank_rd_data_valid_int[i] = _ternary(self, 1,
                                             cfg_to_bank_rd_en_d2[i],
                                             bank_rd_data_valid_int[i+1],
                                             cfg_to_bank_rd_en_d2[i][0])
            cfg_channel_idx = i // self.banks_per_cfg
            self.channel_insts[cfg_channel_idx].append(bank_rd_data_valid_int[i].owner())

        # output rd_data
        priority_encoder_def=m.DeclareFromVerilogFile("./global_buffer/magma/priority_encoder.sv")[0]
        adgn_rd_data=[m.Bits[BANK_DATA_WIDTH]]*self.num_cfg_channels
        for j in range(self.num_cfg_channels):
            priority_encoder = FromMagma(priority_encoder_def)
            self.wire(priority_encoder.ports.data_0, bank_rd_data_int[self.banks_per_cfg*j])
            self.wire(priority_encoder.ports.data_1, bank_rd_data_int[self.banks_per_cfg*j+1])
            self.wire(priority_encoder.ports.data_2, bank_rd_data_int[self.banks_per_cfg*j+2])
            self.wire(priority_encoder.ports.data_3, bank_rd_data_int[self.banks_per_cfg*j+3])
            for k in range(self.banks_per_cfg):
                self.wire(priority_encoder.ports.sel[k], cfg_ctrl_switch_sel[j][k])
            adgn_rd_data[j]=priority_encoder.ports.data_out
            self.channel_insts[j].append(priority_encoder)

        # output rd_data_valid
        priority_encoder_def=m.DeclareFromVerilogFile("./global_buffer/magma/priority_encoder_0.sv")[0]
        adgn_rd_data_valid=[m.Bit]*self.num_cfg_channels
        for j in range(self.num_cfg_channels):
            priority_encoder = FromMagma(priority_encoder_def)
            self.wire(priority_encoder.ports.data_0, bank_rd_data_valid_int[self.banks_per_cfg*j])
            self.wire(priority_encoder.ports.data_1, bank_rd_data_valid_int[self.banks_per_cfg*j+1])
            self.wire(priority_encoder.ports.data_2, bank_rd_data_valid_int[self.banks_per_cfg*j+2])
            self.wire(priority_encoder.ports.data_3, bank_rd_data_valid_int[self.banks_per_cfg*j+3])
            for k in range(self.banks_per_cfg):
                self.wire(priority_encoder.ports.sel[k], cfg_ctrl_switch_sel[j][k])
            adgn_rd_data_valid[j]= priority_encoder.ports.data_out[0]
            self.channel_insts[j].append(priority_encoder)

        pulse_reg_def = mantle.DefineRegister(1, has_ce=False, has_async_reset=True)
        or_ = FromMagma(mantle.DefineOr(self.num_cfg_channels, 1))

        # address generator
        for i in range(self.num_cfg_channels):
            self.wire(cfg_adgn[i].ports.clk, self.ports.clk)
            self.wire(cfg_adgn[i].ports.reset, self.ports.reset)
            self.wire(cfg_adgn[i].ports.config_start_pulse, self.ports.config_start_pulse)

            self.wire(cfg_adgn[i].ports.start_addr, cfg_ctrl_start_addr[i])
            self.wire(cfg_adgn[i].ports.num_words, cfg_ctrl_num_words[i])

            self.wire(cfg_adgn[i].ports.bank_to_cfg_rd_data, adgn_rd_data[i])
            self.wire(cfg_adgn[i].ports.bank_to_cfg_rd_data_valid, adgn_rd_data_valid[i])

            # config_done_pulse
            pulse_reg = FromMagma(pulse_reg_def)
            self.wire(self.ports.clk, pulse_reg.ports.clk)
            self.wire(cfg_adgn[i].ports.config_done_pulse, pulse_reg.ports.I[0])
            self.wire(or_.ports[f"I{i}"], pulse_reg.ports.O)
            self.channel_insts[i].append(pulse_reg)

        self.wire(self.ports.config_done_pulse, or_.ports.O[0])


    def name(self):
        return f"CfgController_{self.num_banks}"
