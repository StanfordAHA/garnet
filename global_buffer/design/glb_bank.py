from kratos import Generator, always_comb, always_ff, posedge, const
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_bank_memory import GlbBankMemory
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_tile_ifc import GlbTileInterface
from global_buffer.design.glb_header import GlbHeader


class GlbBank(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_bank")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        self.wr_packet = self.input("wr_packet", self.header.wr_bank_packet_t)
        self.rdrq_packet = self.input("rdrq_packet", self.header.rdrq_bank_packet_t)
        self.rdrs_packet = self.output("rdrs_packet", self.header.rdrs_packet_t)

        self.bank_cfg_ifc = GlbTileInterface(
            addr_width=self._params.bank_addr_width, data_width=self._params.axi_data_width)

        # local variables
        self.mem_rd_en = self.var("mem_rd_en", 1)
        self.mem_wr_en = self.var("mem_wr_en", 1)
        self.mem_addr = self.var("mem_addr", self._params.bank_addr_width)
        self.mem_data_in = self.var("mem_data_in", self._params.bank_data_width)
        self.mem_data_in_bit_sel = self.var("mem_data_in_bit_sel", self._params.bank_data_width)
        self.mem_data_out = self.var("mem_data_out", self._params.bank_data_width)
        self.packet_rd_data_r = self.var("packet_rd_data_r", self._params.bank_data_width)

        # memory core declaration
        self.wr_data_bit_sel = self.var("wr_data_bit_sel", self._params.bank_data_width)

        self.wr_data_bit_sel_logic()
        self.add_glb_bank_memory()
        self.add_rd_en_pipeline()
        self.add_always(self.mem_signal_logic)
        self.add_always(self.packet_rd_data_ff)
        self.add_always(self.packet_rd_data_logic)

    def wr_data_bit_sel_logic(self):
        for i in range(self._params.bank_data_width):
            self.wire(self.wr_data_bit_sel[i], self.wr_packet['wr_strb'][i // 8])

    def add_glb_bank_memory(self):
        self.glb_bank_memory = GlbBankMemory(_params=self._params)
        self.add_child("glb_bank_memory", self.glb_bank_memory,
                       clk=self.clk,
                       reset=self.reset,
                       ren=self.mem_rd_en,
                       wen=self.mem_wr_en,
                       addr=self.mem_addr,
                       data_in=self.mem_data_in,
                       data_in_bit_sel=self.mem_data_in_bit_sel,
                       data_out=self.mem_data_out)

    def add_rd_en_pipeline(self):
        self.bank_ctrl_pipeline_depth = self._params.glb_bank_memory_pipeline_depth + \
            self._params.sram_gen_pipeline_depth + self._params.sram_gen_output_pipeline_depth + 1

        self.packet_rd_en_d = self.var("packet_rd_en_d", 1)
        self.packet_rdrq_pipeline = Pipeline(width=1, depth=self.bank_ctrl_pipeline_depth)
        self.add_child("packet_rdrq_pipeline",
                       self.packet_rdrq_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.rdrq_packet['rd_en'],
                       out_=self.packet_rd_en_d)

    @always_comb
    def mem_signal_logic(self):
        if self.wr_packet['wr_en']:
            self.mem_wr_en = 1
            self.mem_rd_en = 0
            self.mem_addr = self.wr_packet['wr_addr']
            self.mem_data_in = self.wr_packet['wr_data']
            self.mem_data_in_bit_sel = self.wr_data_bit_sel
        elif self.rdrq_packet['rd_en']:
            self.mem_wr_en = 0
            self.mem_rd_en = 1
            self.mem_addr = self.rdrq_packet['rd_addr']
            self.mem_data_in = 0
            self.mem_data_in_bit_sel = 0
        else:
            self.mem_wr_en = 0
            self.mem_rd_en = 0
            self.mem_addr = 0
            self.mem_data_in = 0
            self.mem_data_in_bit_sel = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_rd_data_ff(self):
        if self.reset:
            self.packet_rd_data_r = 0
        else:
            self.packet_rd_data_r = self.rdrs_packet['rd_data']

    @always_comb
    def packet_rd_data_logic(self):
        if self.packet_rd_en_d:
            self.rdrs_packet['rd_data'] = self.mem_data_out
        else:
            self.rdrs_packet['rd_data'] = self.packet_rd_data_r
        self.rdrs_packet['rd_data_valid'] = self.packet_rd_en_d
