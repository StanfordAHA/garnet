from kratos import Generator, always_comb, concat, const, always_ff, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.pipeline import Pipeline


class GlbBankCtrl(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_bank_ctrl")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        self.packet_wr_en = self.input("packet_wr_en", 1)
        self.packet_wr_addr = self.input("packet_wr_addr", self._params.bank_addr_width)
        self.packet_wr_data = self.input("packet_wr_data", self._params.bank_data_width)
        self.packet_wr_data_bit_sel = self.input("packet_wr_data_bit_sel", self._params.bank_data_width)

        self.packet_rd_en = self.input("packet_rd_en", 1)
        self.packet_rd_addr = self.input("packet_rd_addr", self._params.bank_addr_width)
        self.packet_rd_data = self.output("packet_rd_data", self._params.bank_data_width)
        self.packet_rd_data_valid = self.output("packet_rd_data_valid", 1)

        self.mem_rd_en = self.output("mem_rd_en", 1)
        self.mem_wr_en = self.output("mem_wr_en", 1)
        self.mem_addr = self.output("mem_addr", self._params.bank_addr_width)
        self.mem_data_in = self.output("mem_data_in", self._params.bank_data_width)
        self.mem_data_in_bit_sel = self.output("mem_data_in_bit_sel", self._params.bank_data_width)
        self.mem_data_out = self.input("mem_data_out", self._params.bank_data_width)

        # local variables
        self.packet_rd_data_r = self.var("packet_rd_data_r", self._params.bank_data_width)

        self.add_rd_en_pipeline()
        self.add_always(self.mem_signal_logic)
        self.add_always(self.packet_rd_data_ff)
        self.add_always(self.packet_rd_data_logic)

    @always_comb
    def mem_signal_logic(self):
        if self.packet_wr_en:
            self.mem_wr_en = 1
            self.mem_rd_en = 0
            self.mem_addr = self.packet_wr_addr
            self.mem_data_in = self.packet_wr_data
            self.mem_data_in_bit_sel = self.packet_wr_data_bit_sel
        elif self.packet_rd_en:
            self.mem_wr_en = 0
            self.mem_rd_en = 1
            self.mem_addr = self.packet_rd_addr
            self.mem_data_in = 0
            self.mem_data_in_bit_sel = 0
        else:
            self.mem_wr_en = 0
            self.mem_rd_en = 0
            self.mem_addr = 0
            self.mem_data_in = 0
            self.mem_data_in_bit_sel = 0

    def add_rd_en_pipeline(self):
        self.packet_rd_en_d = self.var("packet_rd_en_d", 1)
        self.packet_rdrq_pipeline = Pipeline(width=1, depth=self.bank_ctrl_pipeline_depth)
        self.add_child("packet_rdrq_pipeline",
                       self.packet_rdrq_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.packet_rd_en,
                       out_=self.packet_rd_en_d)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_rd_data_ff(self):
        if self.reset:
            self.packet_rd_data_r = 0
        else:
            self.packet_rd_data_r = self.packet_rd_data

    @always_comb
    def packet_rd_data_logic(self):
        if self.packet_rd_en_d:
            self.packet_rd_data = self.mem_data_out
        else:
            self.packet_rd_data = self.packet_rd_data_r
        self.packet_rd_data_valid = self.packet_rd_en_d
