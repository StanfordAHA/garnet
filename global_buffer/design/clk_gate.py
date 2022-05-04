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

    def add_clk_gate_cell(self):
        if self._params.process == "TSMC":
            icg_name = self._params.tsmc_icg_name
        elif self._params.process == "GF":
            icg_name = self._params.gf_icg_name
        else:
            raise Exception("process should be either 'TSMC' or 'GF'")

        self.add_child(f"CG_CELL",
                       CG(icg_name),
                       E=self.enable,
                       CP=self.clk,
                       TE=const(0, 1),
                       Q=self.gclk)
