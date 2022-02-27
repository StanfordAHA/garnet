from kratos import Generator, always_comb, concat, const
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
        self.data_in_bit_sel = self.input("data_in_bit_sel", self._params.bank_data_width)
        self.data_out = self.output("data_out", self._params.bank_data_width)

        # local variables
        self.sram_wen = self.var("sram_wen", 1)
        self.sram_wen_d = self.var("sram_wen_d", 1)
        self.sram_cen = self.var("sram_cen", 1)
        self.sram_cen_d = self.var("sram_cen_d", 1)
        self.sram_addr = self.var("sram_addr", self._params.bank_addr_width - self._params.bank_byte_offset)
        self.sram_addr_d = self.var("sram_addr_d", self._params.bank_addr_width - self._params.bank_byte_offset)
        self.sram_data_in = self.var("sram_data_in", self._params.bank_data_width)
        self.sram_data_in_d = self.var("sram_data_in_d", self._params.bank_data_width)
        self.sram_data_in_bit_sel = self.var("sram_data_in_bit_sel", self._params.bank_data_width)
        self.sram_data_in_bit_sel_d = self.var("sram_data_in_bit_sel_d", self._params.bank_data_width)
        self.sram_data_out = self.var("sram_data_out", self._params.bank_data_width)

        self.add_glb_bank_memory_pipeline()
        self.add_glb_bank_sram_gen()
        self.add_always(self.sram_ctrl_logic)

    def add_glb_bank_memory_pipeline(self):
        sram_signals_in = concat(self.sram_wen, self.sram_cen,
                                 self.sram_addr, self.sram_data_in, self.sram_data_in_bit_sel)
        sram_signals_out = concat(self.sram_wen_d, self.sram_cen_d,
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
        self.sram_cen = self.wen | self.ren
        self.sram_addr = self.addr[self._params.bank_addr_width - 1, self._params.bank_byte_offset]
        self.sram_data_in = self.data_in
        self.sram_data_in_bit_sel = self.data_in_bit_sel
        self.data_out = self.sram_data_out
