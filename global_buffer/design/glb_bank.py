from kratos import Generator, always_comb
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_header import GlbHeader


class GlbBank(Generator):
    def __init__(self, params: GlobalBufferParams):
        super().__init__("glb_bank")
        self.params = params
        self.header = GlbHeader(self.params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        self.wr_packet = self.input(
            "wr_packet", self.header.wr_packet_t)
        self.rdrq_packet = self.input(
            "rdrq_packet", self.header.rdrq_packet_t)
        self.rdrs_packet = self.output(
            "rdrs_packet", self.header.rdrs_packet_t)

        self.bank_cfg_ifc = GlbConfigInterface(
            addr_width=self.params.bank_addr_width, data_width=self.params.axi_data_width)

        self.if_sram_cfg_s = self.interface(
            self.bank_cfg_ifc.slave, f"if_sram_cfg_s", is_port=True)

        # local variables
        self.mem_rd_en = self.var("mem_rd_en", 1)
        self.mem_wr_en = self.var("mem_wr_en", 1)
        self.mem_addr = self.var("mem_addr", self.params.bank_addr_width)
        self.mem_data_in = self.var("mem_data_in", self.params.bank_data_width)
        self.mem_data_in_bit_sel = self.var(
            "mem_data_in_bit_sel", self.params.bank_data_width)
        self.mem_data_out = self.var(
            "mem_data_out", self.params.bank_data_width)

        # memory core declaration
        self.wr_data_bit_sel = self.var(
            "wr_data_bit_sel", self.params.bank_data_width)

        self.wr_data_bit_sel_logic()
        self.add_glb_bank_memory()
        self.add_glb_bank_ctrl()

    # TODO: Is there a better way to connect?
    def wr_data_bit_sel_logic(self):
        for i in range(self.params.bank_data_width):
            self.wire(self.wr_data_bit_sel[i], self.wr_packet['wr_strb'][i//8])

    def add_glb_bank_memory(self):
        pass

    def add_glb_bank_ctrl(self):
        pass
