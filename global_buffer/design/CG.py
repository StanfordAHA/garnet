from kratos import Generator, always_latch
from global_buffer.design.global_buffer_parameter import GlobalBufferParams

# CG for clock-gate, I guess
class CG(Generator):

    # TSMC cell 'CKLNQD1BWP16P90' has ports CP, Q
    # GF cell 'SC7P5T_CKGPRELATNX1_SSC14R' has ports CLK, Z

    def __init__(self, _params: GlobalBufferParams):

      if self._params.process == "TSMC":
        name=_self._params.tsmc_icg_name
        super().__init__(name)
        self.E = self.input("E", 1)
        self.CLK = self.clock("CP")
        self.TE = self.input("TE", 1)
        self.Q = self.output("Q", 1)

        self.enable_latch = self.var("enable_latch", 1)
        self.add_always(self.clk_en_latch)
        self.wire(self.Q, (self.CLK & self.enable_latch))

      elif self._params.process == "GF":
        name=_self._params.gf_icg_name
        super().__init__(name)
        self.E = self.input("E", 1)
        self.CLK = self.clock("CLK")
        self.TE = self.input("TE", 1)
        self.Z = self.output("Z", 1)

        self.enable_latch = self.var("enable_latch", 1)
        self.add_always(self.clk_en_latch)
        self.wire(self.Z, (self.CLK & self.enable_latch))

    @always_latch
    def clk_en_latch(self):
        if (~self.CLK):
            self.enable_latch = self.E
