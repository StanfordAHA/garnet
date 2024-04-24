from kratos import Generator, always_comb, concat, always_ff, posedge, const, resize
from kratos.util import clog2
from global_buffer.design.SRAM import SRAM
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbBankSramGen(Generator):
    def __init__(self, addr_width, _params: GlobalBufferParams):

        super().__init__(f"glb_bank_sram_gen_{addr_width}")

        self._params = _params
        self.addr_width = addr_width
        self.sram_macro_width = self._params.sram_macro_word_size
        self.sram_macro_depth = self._params.sram_macro_depth

        self.RESET = self.reset("RESET")
        self.CLK = self.clock("CLK")
        self.CEB = self.input("CEB", 1)
        self.WEB = self.input("WEB", 1)
        self.REB = self.input("REB", 1)
        if self._params.process == "TSMC":
            self.BWEB = self.input("BWEB", self.sram_macro_width)
        elif self._params.process == "GF":
            self.BW = self.input("BW", self.sram_macro_width)
        elif self._params.process == "INTEL":
            self.BWEB = self.input("BWEB", self.sram_macro_width)
        else:
            raise Exception("process should be either 'TSMC' or 'GF'")

        self.D = self.input("D", self.sram_macro_width)
        self.A = self.input("A", self.addr_width)
        self.Q = self.output("Q", self.sram_macro_width)

        # local parameter
        self.sram_macro_addr_width = clog2(self.sram_macro_depth)
        self.num_sram_macros = 2 ** (self.addr_width - self.sram_macro_addr_width)

        # local variables
        self.reb_demux = self.var("REB_DEMUX", self.num_sram_macros)
        self.web_demux = self.var("WEB_DEMUX", self.num_sram_macros)
        self.ceb_demux = self.var("CEB_DEMUX", self.num_sram_macros)
        self.a_sram = self.var("A_SRAM", self.sram_macro_addr_width)
        self.q_sram2mux = self.var("Q_SRAM2MUX", self.sram_macro_width, size=self.num_sram_macros)
        self.sram_sel = self.var("SRAM_SEL", self.addr_width - self.sram_macro_addr_width)
        self.Q_w = self.var("Q_w", self.sram_macro_width)
        self.q_sel = self.var("Q_SEL", self.addr_width - self.sram_macro_addr_width)

        self.REB_d = self.var("REB_d", 1)
        self.CEB_d = self.var("CEB_d", 1)
        self.WEB_d = self.var("WEB_d", 1)
        if self._params.process == "TSMC":
            self.BWEB_d = self.var("BWEB_d", self.sram_macro_width)
        elif self._params.process == "GF":
            self.BW_d = self.var("BW_d", self.sram_macro_width)
        elif self._params.process == "INTEL":
            self.BWEB_d = self.var("BWEB_d", self.sram_macro_width)
        else:
            raise Exception("process should be either 'TSMC' or 'GF'")

        self.D_d = self.var("D_d", self.sram_macro_width)
        self.reb_demux_d = self.var("REB_DEMUX_d", self.num_sram_macros)
        self.web_demux_d = self.var("WEB_DEMUX_d", self.num_sram_macros)
        self.ceb_demux_d = self.var("CEB_DEMUX_d", self.num_sram_macros)
        self.sram_sel_d = self.var("SRAM_SEL_d", self.addr_width - self.sram_macro_addr_width)
        self.a_sram_d = self.var("A_SRAM_d", self.sram_macro_addr_width)

        self.wire(self.sram_sel, self.A[self.addr_width - 1, self.sram_macro_addr_width])
        self.wire(self.a_sram, self.A[self.sram_macro_addr_width - 1, 0])

        self.add_pipeline()
        self.add_always(self.q_sel_ff)
        if self._params.process == "INTEL":
            self.add_always(self.sram_ctrl_logic_intel)
        else:
            self.add_always(self.sram_ctrl_logic)
        self.add_sram_macro()
        self.wire(self.Q_w, self.q_sram2mux[self.q_sel])

    def add_pipeline(self):
        if self._params.process == "TSMC":
            sram_signals_reset_high_in = concat(self.WEB, self.CEB, self.web_demux, self.ceb_demux, self.BWEB)
            sram_signals_reset_high_out = concat(
                self.WEB_d, self.CEB_d, self.web_demux_d, self.ceb_demux_d, self.BWEB_d)
        elif self._params.process == "INTEL":
            sram_signals_reset_high_in = concat(self.WEB, self.CEB, self.reb_demux, self.web_demux, self.BWEB)
            sram_signals_reset_high_out = concat(self.WEB_d, self.CEB_d, self.reb_demux_d, self.web_demux_d, self.BWEB_d)
        elif self._params.process == "GF":
            sram_signals_reset_high_in = concat(self.WEB, self.CEB, self.web_demux, self.ceb_demux, self.BW)
            sram_signals_reset_high_out = concat(self.WEB_d, self.CEB_d, self.web_demux_d, self.ceb_demux_d, self.BW_d)
        else:
            raise Exception("process should be either 'TSMC' or 'GF'")
        self.sram_signals_reset_high_pipeline = Pipeline(
            width=sram_signals_reset_high_in.width, depth=self._params.sram_gen_pipeline_depth, reset_high=True)
        self.add_child("sram_signals_reset_high_pipeline",
                       self.sram_signals_reset_high_pipeline,
                       clk=self.CLK,
                       clk_en=const(1, 1),
                       reset=self.RESET,
                       in_=sram_signals_reset_high_in,
                       out_=sram_signals_reset_high_out)

        sram_signals_in = concat(self.a_sram, self.sram_sel, self.D)
        sram_signals_out = concat(self.a_sram_d, self.sram_sel_d, self.D_d)
        self.sram_signals_pipeline = Pipeline(width=sram_signals_in.width, depth=self._params.sram_gen_pipeline_depth)
        self.add_child("sram_signals_pipeline",
                       self.sram_signals_pipeline,
                       clk=self.CLK,
                       clk_en=const(1, 1),
                       reset=self.RESET,
                       in_=sram_signals_in,
                       out_=sram_signals_out)

        self.sram_signals_output_pipeline = Pipeline(
            width=self.sram_macro_width, depth=self._params.sram_gen_output_pipeline_depth)
        self.add_child("sram_signals_output_pipeline",
                       self.sram_signals_output_pipeline,
                       clk=self.CLK,
                       clk_en=const(1, 1),
                       reset=self.RESET,
                       in_=self.Q_w,
                       out_=self.Q)

    @always_ff((posedge, "CLK"), (posedge, "RESET"))
    def q_sel_ff(self):
        if self.RESET:
            self.q_sel = 0
        else:
            if (self.CEB_d == 0) & (self.WEB_d == 1):
                self.q_sel = self.sram_sel_d

    @always_comb
    def sram_ctrl_logic(self):
        if ~self.WEB:
            self.web_demux = ~(const(1, width=self.num_sram_macros) << resize(self.sram_sel, self.num_sram_macros))
        else:
            self.web_demux = const(2**self.num_sram_macros - 1, self.num_sram_macros)

        if ~self.CEB:
            self.ceb_demux = ~(const(1, width=self.num_sram_macros) << resize(self.sram_sel, self.num_sram_macros))
        else:
            self.ceb_demux = const(2**self.num_sram_macros - 1, self.num_sram_macros)

        if ~self.REB:
            self.reb_demux = ~(const(1, width=self.num_sram_macros) << resize(self.sram_sel, self.num_sram_macros))
        else:
            self.reb_demux = const(2**self.num_sram_macros - 1, self.num_sram_macros)

    @always_comb
    def sram_ctrl_logic_intel(self):
        if ~self.WEB:
            self.web_demux = ~(const(1, width=self.num_sram_macros) << resize(self.sram_sel, self.num_sram_macros))
        else:
            self.web_demux = const(2**self.num_sram_macros - 1, self.num_sram_macros)

        if ~self.REB:
            self.reb_demux = ~(const(1, width=self.num_sram_macros) << resize(self.sram_sel, self.num_sram_macros))
        else:
            self.reb_demux = const(2**self.num_sram_macros - 1, self.num_sram_macros)

    def add_sram_macro(self):
        for i in range(self.num_sram_macros):
            if self._params.process == "TSMC":
                self.add_child(f"sram_array_{i}",
                               SRAM(self._params.process, self._params.tsmc_sram_macro_prefix,
                                    self.sram_macro_width, self.sram_macro_depth),
                               CLK=self.CLK,
                               A=self.a_sram_d,
                               BWEB=self.BWEB_d,
                               CEB=self.ceb_demux_d[i],
                               WEB=self.web_demux_d[i],
                               D=self.D_d,
                               Q=self.q_sram2mux[i],
                               RTSEL=const(0b01, 2),
                               WTSEL=const(0b00, 2))
            elif self._params.process == "INTEL":
                sram_name = "ip224uhdlp1p11rf_4096x64m4b2c1s1_t0r0p0d0a1m1h"
                self.add_child(f"sram_array_{i}",
                               SRAM(self._params.process, sram_name,
                                    self.sram_macro_width, self.sram_macro_depth),
                               clk=self.CLK,
                               wen=~self.web_demux_d[i],
                               ren=~self.reb_demux_d[i],
                               adr=self.a_sram_d,
                               din=self.D_d,
                               q=self.q_sram2mux[i],
                               wbeb=self.BWEB_d,
                               fwen=self.RESET,
                               clkbyp=const(0b0, 1),
                               mcen=const(0b0, 1),
                               mc=const(0b000, 3),
                               wpulseen=const(0b0, 1),
                               wpulse=const(0b00, 2),
                               wa=const(0b00, 2))
            else:
                sram_name = (self._params.gf_sram_macro_prefix
                             + f"W{self._params.sram_macro_depth:05d}"
                             + f"B{self._params.sram_macro_word_size:03d}"
                             + f"M{self._params.sram_macro_mux_size:02d}"
                             + f"S{self._params.sram_macro_num_subarrays}"
                             + "_HB"
                             )
                self.add_child(f"sram_array_{i}",
                               SRAM(self._params.process, sram_name,
                                    self.sram_macro_width, self.sram_macro_depth),
                               CLK=self.CLK,
                               CEN=self.ceb_demux_d[i],
                               RDWEN=self.web_demux_d[i],
                               A=self.a_sram_d,
                               D=self.D_d,
                               BW=self.BW_d,
                               Q=self.q_sram2mux[i],
                               T_LOGIC=const(0b0, 1),
                               T_Q_RST=const(0b0, 1),
                               MA_SAWL1=const(0b0, 1),
                               MA_SAWL0=const(0b0, 1),
                               MA_WL1=const(0b0, 1),
                               MA_WL0=const(0b0, 1),
                               MA_WRAS0=const(0b0, 1),
                               MA_WRAS1=const(0b0, 1),
                               MA_VD0=const(0b0, 1),
                               MA_VD1=const(0b0, 1),
                               MA_WRT=const(0b0, 1),
                               MA_STABAS0=const(0b0, 1),
                               MA_STABAS1=const(0b0, 1))
