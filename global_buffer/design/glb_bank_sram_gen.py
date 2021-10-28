from kratos import Generator, always_comb, concat, always_ff, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.pipeline import Pipeline


class GlbBankSramGen(Generator):
    def __init__(self):
        super().__init__("glb_bank_sram_gen")
        self.p_data_width = self.param("DATA_WIDTH", 16, initial_value=64)
        self.p_addr_width = self.param("ADDR_WIDTH", 16, initial_value=14)

        self.RESET = self.reset("RESET")
        self.CLK = self.clock("CLK")
        self.CEB = self.input("CEB", 1)
        self.WEB = self.input("WEB", 1)
        self.BWEB = self.input("BWEB", self.p_data_width)
        self.D = self.input("D", self.p_data_width)
        self.A = self.input("A", self.p_addr_width)
        self.Q = self.output("Q", self.p_data_width)

        self.is_stub = True
