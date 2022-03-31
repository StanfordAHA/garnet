from kratos import Generator, always_ff, posedge, concat, const, resize, clog2
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbBankSramStub(Generator):
    def __init__(self, addr_width, data_width, _params: GlobalBufferParams):
        super().__init__("glb_bank_sram_stub")
        self._params = _params
        self.addr_width = addr_width
        self.data_width = data_width
        assert self.data_width == 4 * self._params.cgra_data_width

        self.RESET = self.reset("RESET")
        self.CLK = self.clock("CLK")
        self.CEB = self.input("CEB", 1)
        self.WEB = self.input("WEB", 1)
        self.BWEB = self.input("BWEB", self.data_width)
        self.D = self.input("D", self.data_width)
        self.A = self.input("A", self.addr_width)
        self.Q = self.output("Q", self.data_width)

        self.Q_w = self.var("Q_w", self.data_width)
        self.mem = self.var("mem", self._params.cgra_data_width, size=2**(self.addr_width + 2), explicit_array=True)

        self.add_always(self.mem_ff)
        self.add_pipeline()

    @always_ff((posedge, "CLK"))
    def mem_ff(self):
        if self.CEB == 0:
            self.Q_w = concat(self.mem[resize((self.A << 2) + 3, self.addr_width + 2)],
                              self.mem[resize((self.A << 2) + 2, self.addr_width + 2)],
                              self.mem[resize((self.A << 2) + 1, self.addr_width + 2)],
                              self.mem[resize((self.A << 2), self.addr_width + 2)])
            if self.WEB == 0:
                for i in range(self.data_width):
                    if self.BWEB[i] == 0:
                        self.mem[resize((self.A << 2) + i // 16,
                                        self.addr_width + 2)][resize(i % 16,
                                                                     clog2(self._params.cgra_data_width))] = self.D[i]

    def add_pipeline(self):
        self.mem_pipeline = Pipeline(width=self.data_width,
                                     depth=(self._params.sram_gen_pipeline_depth
                                            + self._params.sram_gen_output_pipeline_depth))
        self.add_child("mem_pipeline",
                       self.mem_pipeline,
                       clk=self.CLK,
                       clk_en=const(1, 1),
                       reset=self.RESET,
                       in_=self.Q_w,
                       out_=self.Q)
