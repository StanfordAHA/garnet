from kratos import Generator, const
from global_buffer.design.CG import CG
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class ClkGate(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("clk_gate")
        self._params = _params
        self.clk = self.clock("clk")
        self.enable = self.input("enable", 1)
        self.gclk = self.output("gclk", 1)

        self.add_clk_gate_cell()

    # TSMC cell 'CKLNQD1BWP16P90' has ports CP, Q
    # GF cell 'SC7P5T_CKGPRELATNX1_SSC14R' has ports CLK, Z


    def add_clk_gate_cell(self):

        if self._params.process == "TSMC":
            self.add_child(f"CG_CELL",
                       CG(self._params),
                       E=self.enable,
                       CP=self.clk,
                       TE=const(0, 1),
                       Q=self.gclk)


        elif self._params.process == "GF":
            icg_name = self._params.gf_icg_name
            self.add_child(f"CG_CELL",
                       CG(self._params),
                       E=self.enable,
                       CLK=self.clk,
                       TE=const(0, 1),
                       Z=self.gclk)

        else:
            raise Exception("process should be either 'TSMC' or 'GF'")

