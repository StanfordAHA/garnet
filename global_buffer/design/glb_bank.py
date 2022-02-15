from kratos import Generator
from global_buffer.design.glb_bank_memory import GlbBankMemory
from global_buffer.design.glb_bank_ctrl import GlbBankCtrl
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_header import GlbHeader


class GlbBank(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_bank")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        self.wr_packet = self.input("wr_packet", self.header.wr_packet_t)
        self.rdrq_packet = self.input("rdrq_packet", self.header.rdrq_packet_t)
        self.rdrs_packet = self.output("rdrs_packet", self.header.rdrs_packet_t)

        self.bank_cfg_ifc = GlbConfigInterface(
            addr_width=self._params.bank_addr_width, data_width=self._params.axi_data_width)

        # local variables
        self.mem_rd_en = self.var("mem_rd_en", 1)
        self.mem_wr_en = self.var("mem_wr_en", 1)
        self.mem_addr = self.var("mem_addr", self._params.bank_addr_width)
        self.mem_data_in = self.var("mem_data_in", self._params.bank_data_width)
        self.mem_data_in_bit_sel = self.var("mem_data_in_bit_sel", self._params.bank_data_width)
        self.mem_data_out = self.var("mem_data_out", self._params.bank_data_width)

        # memory core declaration
        self.wr_data_bit_sel = self.var("wr_data_bit_sel", self._params.bank_data_width)

        self.wr_data_bit_sel_logic()
        self.add_glb_bank_ctrl()
        self.add_glb_bank_memory()

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

    def add_glb_bank_ctrl(self):
        self.glb_bank_ctrl = GlbBankCtrl(_params=self._params)
        self.add_child("glb_bank_ctrl", self.glb_bank_ctrl,
                       clk=self.clk,
                       reset=self.reset,
                       packet_wr_en=self.wr_packet['wr_en'],
                       packet_wr_addr=self.wr_packet['wr_addr'][self._params.bank_addr_width - 1, 0],
                       packet_wr_data=self.wr_packet['wr_data'],
                       packet_wr_data_bit_sel=self.wr_data_bit_sel,
                       packet_rd_en=self.rdrq_packet['rd_en'],
                       packet_rd_src_tile=self.rdrq_packet['rd_src_tile'],
                       packet_rd_addr=self.rdrq_packet['rd_addr'][self._params.bank_addr_width - 1, 0],
                       packet_rd_data=self.rdrs_packet['rd_data'],
                       packet_rd_data_valid=self.rdrs_packet['rd_data_valid'],
                       packet_rd_dst_tile=self.rdrs_packet['rd_dst_tile'],
                       mem_rd_en=self.mem_rd_en,
                       mem_wr_en=self.mem_wr_en,
                       mem_addr=self.mem_addr,
                       mem_data_in=self.mem_data_in,
                       mem_data_in_bit_sel=self.mem_data_in_bit_sel,
                       mem_data_out=self.mem_data_out)
