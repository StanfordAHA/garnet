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
        self.packet_rd_type = self.input("packet_rd_type", self.header.PacketEnumWidth)
        self.packet_rd_src_tile = self.input("packet_rd_src_tile", self._params.tile_sel_addr_width)
        self.packet_rd_addr = self.input("packet_rd_addr", self._params.bank_addr_width)
        self.packet_rd_data = self.output("packet_rd_data", self._params.bank_data_width)
        self.packet_rd_data_valid = self.output("packet_rd_data_valid", 1)
        self.packet_rd_dst_tile = self.output("packet_rd_dst_tile", self._params.tile_sel_addr_width)

        self.mem_rd_en = self.output("mem_rd_en", 1)
        self.mem_wr_en = self.output("mem_wr_en", 1)
        self.mem_addr = self.output("mem_addr", self._params.bank_addr_width)
        self.mem_data_in = self.output("mem_data_in", self._params.bank_data_width)
        self.mem_data_in_bit_sel = self.output("mem_data_in_bit_sel", self._params.bank_data_width)
        self.mem_data_out = self.input("mem_data_out", self._params.bank_data_width)

        self.bank_cfg_ifc = GlbConfigInterface(
            addr_width=self._params.bank_addr_width, data_width=self._params.axi_data_width)

        self.if_sram_cfg_s = self.interface(
            self.bank_cfg_ifc.slave, f"if_sram_cfg_s", is_port=True)

        self.bank_ctrl_pipeline_depth = self._params.glb_bank_memory_pipeline_depth + \
            self._params.sram_gen_pipeline_depth + self._params.sram_gen_output_pipeline_depth + 1

        # local variables
        self.sram_cfg_rd_data_r = self.var("sram_cfg_rd_data_r", self._params.axi_data_width)
        self.sram_cfg_rd_addr_sel_d = self.var("sram_cfg_rd_addr_sel_d", 1)
        self.packet_rd_data_r = self.var("packet_rd_data_r", self._params.bank_data_width)

        self.add_rd_en_pipeline()
        self.add_always(self.mem_signal_logic)
        self.add_always(self.packet_rd_data_ff)
        self.add_always(self.packet_rd_data_logic)
        self.add_sram_cfg_rd_addr_sel_pipeline()
        self.add_always(self.sram_cfg_rd_data_ff)
        self.add_always(self.sram_cfg_rd_data_logic)

    @always_comb
    def mem_signal_logic(self):
        if self.if_sram_cfg_s.wr_en:
            if self.if_sram_cfg_s.wr_addr[self._params.bank_byte_offset - 1] == 0:
                self.mem_wr_en = 1
                self.mem_rd_en_w = 0
                self.mem_addr = self.if_sram_cfg_s.wr_addr
                self.mem_data_in = concat(const(
                    0, self._params.bank_data_width - self._params.axi_data_width), self.if_sram_cfg_s.wr_data)
                self.mem_data_in_bit_sel = concat(const(0, self._params.bank_data_width - self._params.axi_data_width),
                                                  const(2**self._params.axi_data_width - 1,
                                                        self._params.axi_data_width))
            else:
                self.mem_wr_en = 1
                self.mem_rd_en_w = 0
                self.mem_addr = self.if_sram_cfg_s.wr_addr
                self.mem_data_in = concat(self.if_sram_cfg_s.wr_data[self._params.bank_data_width
                                                                     - self._params.axi_data_width - 1, 0],
                                          const(0, self._params.axi_data_width))
                self.mem_data_in_bit_sel = concat(const(2**(self._params.bank_data_width - self._params.axi_data_width)
                                                        - 1,
                                                        self._params.bank_data_width - self._params.axi_data_width),
                                                  const(0, self._params.axi_data_width))
        elif self.if_sram_cfg_s.rd_en:
            self.mem_wr_en = 0
            self.mem_rd_en_w = 1
            self.mem_addr = self.if_sram_cfg_s.rd_addr
            self.mem_data_in = 0
            self.mem_data_in_bit_sel = 0
        elif self.packet_wr_en:
            self.mem_wr_en = 1
            self.mem_rd_en_w = 0
            self.mem_addr = self.packet_wr_addr
            self.mem_data_in = self.packet_wr_data
            self.mem_data_in_bit_sel = self.packet_wr_data_bit_sel
        elif self.packet_rd_en:
            self.mem_wr_en = 0
            self.mem_rd_en_w = 1
            self.mem_addr = self.packet_rd_addr
            self.mem_data_in = 0
            self.mem_data_in_bit_sel = 0
        else:
            self.mem_wr_en = 0
            self.mem_rd_en_w = 0
            self.mem_addr = 0
            self.mem_data_in = 0
            self.mem_data_in_bit_sel = 0

    def add_rd_en_pipeline(self):
        self.mem_rd_en_w = self.var("mem_rd_en_w", 1)
        self.mem_rd_en_d = self.var("mem_rd_en_d", 1)
        self.sram_cfg_rd_en_d = self.var("sram_cfg_rd_en_d", 1)
        self.wire(self.mem_rd_en_w, self.mem_rd_en)

        self.mem_rd_en_pipeline = Pipeline(width=1, depth=self.bank_ctrl_pipeline_depth)
        self.add_child("mem_rd_en_pipeline",
                       self.mem_rd_en_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.mem_rd_en_w,
                       out_=self.mem_rd_en_d)

        self.sram_cfg_rd_en_pipeline = Pipeline(width=1, depth=self.bank_ctrl_pipeline_depth)
        self.add_child("sram_cfg_rd_en_pipeline",
                       self.sram_cfg_rd_en_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.if_sram_cfg_s.rd_en,
                       out_=self.sram_cfg_rd_en_d)

        self.packet_rd_en_d = self.var("packet_rd_en_d", 1)
        self.packet_rd_type_d = self.var("packet_rd_type_d", self.header.PacketEnumWidth)
        self.packet_rd_src_tile_d = self.var("packet_rd_src_tile_d", self._params.tile_sel_addr_width)
        self.packet_pipeline_in = concat(self.packet_rd_en, self.packet_rd_type, self.packet_rd_src_tile)
        self.packet_pipeline_out = concat(self.packet_rd_en_d, self.packet_rd_type_d, self.packet_rd_src_tile_d)
        self.packet_rdrq_pipeline = Pipeline(width=self.packet_pipeline_in.width, depth=self.bank_ctrl_pipeline_depth)
        self.add_child("packet_rdrq_pipeline",
                       self.packet_rdrq_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.packet_pipeline_in,
                       out_=self.packet_pipeline_out)

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
        self.packet_rd_dst_tile = self.packet_rd_src_tile_d

    def add_sram_cfg_rd_addr_sel_pipeline(self):
        self.sram_cfg_rd_addr_sel_d = self.var("sram_cfg_rd_addr_sel_d", 1)
        self.sram_cfg_rd_addr_sel_pipeline = Pipeline(width=1,
                                                      depth=self.bank_ctrl_pipeline_depth)
        self.add_child("sram_cfg_rd_addr_sel_pipeline",
                       self.sram_cfg_rd_addr_sel_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.if_sram_cfg_s.rd_addr[self._params.bank_byte_offset - 1],
                       out_=self.sram_cfg_rd_addr_sel_d)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def sram_cfg_rd_data_ff(self):
        if self.reset:
            self.sram_cfg_rd_data_r = 0
        else:
            self.sram_cfg_rd_data_r = self.if_sram_cfg_s.rd_data

    @always_comb
    def sram_cfg_rd_data_logic(self):
        if self.sram_cfg_rd_en_d:
            if self.sram_cfg_rd_addr_sel_d == 0:
                self.if_sram_cfg_s.rd_data = self.mem_data_out[self._params.axi_data_width - 1, 0]
            else:
                self.if_sram_cfg_s.rd_data = self.mem_data_out[self._params.axi_data_width
                                                               * 2 - 1, self._params.axi_data_width]
        else:
            self.if_sram_cfg_s.rd_data = self.sram_cfg_rd_data_r
        self.if_sram_cfg_s.rd_data_valid = self.mem_rd_en_d & self.sram_cfg_rd_en_d
        # TODO: This can just be simpler as below
        # self.if_sram_cfg_s.rd_data_valid = self.sram_cfg_rd_en_d
