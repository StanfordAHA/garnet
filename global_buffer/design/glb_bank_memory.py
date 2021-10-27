from kratos import Generator, always_comb, concat, const, always_ff, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.pipeline import Pipeline


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

        self.is_stub = True
