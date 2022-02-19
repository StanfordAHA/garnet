from kratos import Generator, always_comb, concat, always_ff, posedge, const, resize
from kratos.util import clog2
from global_buffer.design.SRAM import SRAM
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbBankSramGen(Generator):
    def __init__(self, addr_width, sram_macro_width, sram_macro_depth, _params: GlobalBufferParams):
        super().__init__("glb_bank_sram_gen")
        self._params = _params
        self.addr_width = addr_width
        self.sram_macro_width = sram_macro_width
        self.sram_macro_depth = sram_macro_depth

        self.RESET = self.reset("RESET")
        self.CLK = self.clock("CLK")
        self.CEB = self.input("CEB", 1)
        self.WEB = self.input("WEB", 1)
        self.BWEB = self.input("BWEB", self.sram_macro_width)
        self.D = self.input("D", self.sram_macro_width)
        self.A = self.input("A", self.addr_width)
        self.Q = self.output("Q", self.sram_macro_width)

        # local parameter
        self.sram_macro_addr_width = clog2(self.sram_macro_depth)
        self.num_sram_macros = 2 ** (self.addr_width - self.sram_macro_addr_width)

        # local variables
        self.web_demux = self.var("WEB_DEMUX", self.num_sram_macros)
        self.ceb_demux = self.var("CEB_DEMUX", self.num_sram_macros)
        self.a_sram = self.var("A_SRAM", self.sram_macro_addr_width)
        self.q_sram2mux = self.var("Q_SRAM2MUX", self.sram_macro_width, size=self.num_sram_macros)
        self.sram_sel = self.var("SRAM_SEL", self.addr_width - self.sram_macro_addr_width)
        self.Q_w = self.var("Q_w", self.sram_macro_width)
        self.q_sel = self.var("Q_SEL", self.addr_width - self.sram_macro_addr_width)

        self.CEB_d = self.var("CEB_d", 1)
        self.WEB_d = self.var("WEB_d", 1)
        self.BWEB_d = self.var("BWEB_d", self.sram_macro_width)
        self.D_d = self.var("D_d", self.sram_macro_width)
        self.web_demux_d = self.var("WEB_DEMUX_d", self.num_sram_macros)
        self.ceb_demux_d = self.var("CEB_DEMUX_d", self.num_sram_macros)
        self.sram_sel_d = self.var("SRAM_SEL_d", self.addr_width - self.sram_macro_addr_width)
        self.a_sram_d = self.var("A_SRAM_d", self.sram_macro_addr_width)

        self.wire(self.sram_sel, self.A[self.addr_width - 1, self.sram_macro_addr_width])
        self.wire(self.a_sram, self.A[self.sram_macro_addr_width - 1, 0])

        self.add_pipeline()
        self.add_always(self.q_sel_ff)
        self.add_always(self.sram_ctrl_logic)
        self.add_sram_macro()
        self.wire(self.Q_w, self.q_sram2mux[self.q_sel])

    def add_pipeline(self):
        sram_signals_reset_high_in = concat(self.WEB, self.CEB, self.web_demux, self.ceb_demux, self.BWEB)
        sram_signals_reset_high_out = concat(self.WEB_d, self.CEB_d, self.web_demux_d, self.ceb_demux_d, self.BWEB_d)
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

    def add_sram_macro(self):
        for i in range(self.num_sram_macros):
            self.add_child(f"sram_array_{i}",
                           SRAM(self._params.sram_macro_name),
                           CLK=self.CLK,
                           A=self.a_sram_d,
                           BWEB=self.BWEB_d,
                           CEB=self.ceb_demux_d[i],
                           WEB=self.web_demux_d[i],
                           D=self.D_d,
                           Q=self.q_sram2mux[i],
                           RTSEL=const(0b01, 2),
                           WTSEL=const(0b00, 2))
