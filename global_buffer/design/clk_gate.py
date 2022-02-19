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
        self.add_child(f"CG_CELL",
                       CG(self._params.cg_cell_name),
                       E=self.enable,
                       CP=self.clk,
                       TE=const(0, 1),
                       Q=self.gclk)
