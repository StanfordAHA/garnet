from kratos import Generator, always_latch
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class CG(Generator):
    # TSMC cell 'CKLNQD1BWP16P90' has ports CP, Q
    # GF cell 'SC7P5T_CKGPRELATNX1_SSC14R' has ports CLK, Z
    def __init__(self, _params: GlobalBufferParams):
        if _params.process == "TSMC":
            super().__init__(_params.tsmc_icg_name)
            self.E = self.input("E", 1)
            self.CLK = self.clock("CP")
            self.TE = self.input("TE", 1)
            self.Q = self.output("Q", 1)

            self.enable_latch = self.var("enable_latch", 1)
            self.add_always(self.clk_en_latch)
            self.wire(self.Q, (self.CLK & self.enable_latch))

        elif _params.process == "GF":
            super().__init__(_params.gf_icg_name)
            self.E = self.input("E", 1)
            self.CLK = self.clock("CLK")
            self.TE = self.input("TE", 1)
            self.Z = self.output("Z", 1)

            self.enable_latch = self.var("enable_latch", 1)
            self.add_always(self.clk_en_latch)
            self.wire(self.Z, (self.CLK & self.enable_latch))

        elif _params.process == "INTEL":
            super().__init__(_params.intel_icg_name)
            self.en = self.input("en", 1)
            self.clk = self.clock("clk")
            self.te = self.input("te", 1)
            self.clkout = self.output("clkout", 1)

            self.enable_latch = self.var("enable_latch", 1)
            self.add_always(self.clk_en_latch)
            self.wire(self.clkout, (self.clk & self.enable_latch))

        else:
            super().__init__("clk_gate")
            self.E = self.input("E", 1)
            self.CLK = self.clock("CLK")
            self.TE = self.input("TE", 1)
            self.Z = self.output("Z", 1)
            self.enable_latch = self.var("enable_latch", 1)
            self.add_always(self.clk_en_latch)
            self.wire(self.Z, (self.CLK & self.enable_latch))

    @always_latch
    def clk_en_latch(self):
        if (~self.clk):
            self.enable_latch = self.en
