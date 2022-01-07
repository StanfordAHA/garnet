from kratos import Generator, always_comb, concat, always_ff, posedge, const
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_bank_sram_gen import GlbBankSramGen
from global_buffer.design.glb_bank_sram_stub import GlbBankSramStub


class GlbBankMemory(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_bank_memory")
        self._params = _params

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.ren = self.input("ren", 1)
        self.wen = self.input("wen", 1)
        self.addr = self.input("addr", self._params.bank_addr_width)
        self.data_in = self.input("data_in", self._params.bank_data_width)
        self.data_in_bit_sel = self.input(
            "data_in_bit_sel", self._params.bank_data_width)
        self.data_out = self.output("data_out", self._params.bank_data_width)

        # local variables
        self.sram_wen = self.var("sram_wen", 1)
        self.sram_wen_d = self.var("sram_wen_d", 1)
        self.sram_ren = self.var("sram_ren", 1)
        self.sram_ren_d = self.var("sram_ren_d", 1)
        self.sram_ren_d_vld = self.var("sram_ren_d_vld", 1)
        self.sram_cen = self.var("sram_cen", 1)
        self.sram_cen_d = self.var("sram_cen_d", 1)
        self.sram_addr = self.var(
            "sram_addr", self._params.bank_addr_width - self._params.bank_byte_offset)
        self.sram_addr_d = self.var(
            "sram_addr_d", self._params.bank_addr_width - self._params.bank_byte_offset)
        self.sram_data_in = self.var(
            "sram_data_in", self._params.bank_data_width)
        self.sram_data_in_d = self.var(
            "sram_data_in_d", self._params.bank_data_width)
        self.sram_data_in_bit_sel = self.var(
            "sram_data_in_bit_sel", self._params.bank_data_width)
        self.sram_data_in_bit_sel_d = self.var(
            "sram_data_in_bit_sel_d", self._params.bank_data_width)
        self.sram_data_out = self.var(
            "sram_data_out", self._params.bank_data_width)
        self.data_out_w = self.var(
            "data_out_w", self._params.bank_data_width)
        self.data_out_r = self.var(
            "data_out_r", self._params.bank_data_width)

        self.wire(self.data_out, self.data_out_w)

        self.add_glb_bank_memory_pipeline()
        self.add_glb_bank_sram_gen()
        self.add_always(self.sram_ctrl_logic)
        self.add_always(self.data_out_ff)
        self.add_always(self.data_out_logic)

    def add_glb_bank_memory_pipeline(self):
        sram_signals_in = concat(self.sram_ren, self.sram_wen, self.sram_cen,
                                 self.sram_addr, self.sram_data_in, self.sram_data_in_bit_sel)
        sram_signals_out = concat(self.sram_ren_d, self.sram_wen_d, self.sram_cen_d,
                                  self.sram_addr_d, self.sram_data_in_d, self.sram_data_in_bit_sel_d)

        sram_signals_pipeline = Pipeline(width=sram_signals_in.width,
                                         depth=self._params.glb_bank_memory_pipeline_depth)
        self.add_child(f"sram_signals_pipeline",
                       sram_signals_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=sram_signals_in,
                       out_=sram_signals_out)

        self.sram_ren_rsp_pipeline = Pipeline(width=1,
                                              depth=(self._params.sram_gen_pipeline_depth
                                                     + self._params.sram_gen_output_pipeline_depth
                                                     + 1))
        self.add_child("sram_ren_rsp_pipeline",
                       self.sram_ren_rsp_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.sram_ren_d,
                       out_=self.sram_ren_d_vld)

    def add_glb_bank_sram_gen(self):
        if self._params.is_sram_stub:
            self.glb_bank_sram_stub = GlbBankSramStub(addr_width=(self._params.bank_addr_width
                                                                  - self._params.bank_byte_offset),
                                                      data_width=self._params.bank_data_width,
                                                      _params=self._params)
            self.add_child("glb_bank_sram_stub",
                           self.glb_bank_sram_stub,
                           CLK=self.clk,
                           RESET=self.reset,
                           CEB=(~self.sram_cen_d),
                           WEB=(~self.sram_wen_d),
                           A=self.sram_addr_d,
                           D=self.sram_data_in_d,
                           BWEB=(~self.sram_data_in_bit_sel_d),
                           Q=self.sram_data_out)
        else:
            self.glb_bank_sram_gen = GlbBankSramGen(addr_width=(self._params.bank_addr_width
                                                                - self._params.bank_byte_offset),
                                                    sram_macro_width=self._params.bank_data_width,
                                                    sram_macro_depth=self._params.sram_macro_depth,
                                                    _params=self._params)
            self.add_child("glb_bank_sram_gen",
                           self.glb_bank_sram_gen,
                           CLK=self.clk,
                           RESET=self.reset,
                           CEB=(~self.sram_cen_d),
                           WEB=(~self.sram_wen_d),
                           A=self.sram_addr_d,
                           D=self.sram_data_in_d,
                           BWEB=(~self.sram_data_in_bit_sel_d),
                           Q=self.sram_data_out)

    @always_comb
    def sram_ctrl_logic(self):
        self.sram_wen = self.wen
        self.sram_ren = self.ren
        self.sram_cen = self.wen | self.ren
        self.sram_addr = self.addr[self._params.bank_addr_width - 1,
                                   self._params.bank_byte_offset]
        self.sram_data_in = self.data_in
        self.sram_data_in_bit_sel = self.data_in_bit_sel

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def data_out_ff(self):
        if self.reset:
            self.data_out_r = 0
        else:
            self.data_out_r = self.data_out_w

    @always_comb
    def data_out_logic(self):
        if self.sram_ren_d_vld:
            self.data_out_w = self.sram_data_out
        else:
            self.data_out_w = self.data_out_r
