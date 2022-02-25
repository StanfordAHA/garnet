from kratos import Generator, always_ff, always_comb, posedge, concat, const
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_tile_ifc import GlbTileInterface
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen


class GlbSwitch(Generator):
    def __init__(self, _params: GlobalBufferParams, ifc: GlbTileInterface):
        super().__init__("glb_switch")
        self._params = _params
        self.header = GlbHeader(self._params)
        self.mclk = self.clock("mclk")
        self.gclk = self.clock("gclk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.ifc = ifc
        self.addr_width = self.ifc.addr_width
        self.data_width = self.ifc.data_width
        # It only works when data_width of interface is same as or half of the bank_data_width
        assert ((self.data_width == self._params.bank_data_width)
                | (self.data_width * 2 == self._params.bank_data_width))

        self.bank_lsb_data_width = self.data_width
        self.bank_msb_data_width = self._params.bank_data_width - self.data_width

        # port to switch
        self.clk_en_sw2bank = self.output("clk_en_sw2bank", 1)
        self.wr_packet = self.output("wr_packet", self.header.wr_packet_t)
        self.rdrq_packet = self.output("rdrq_packet", self.header.rdrq_packet_t)
        self.rdrs_packet = self.input("rdrs_packet", self.header.rdrs_packet_t)

        # config port
        self.if_est_m = self.interface(self.ifc.master, "if_est_m", is_port=True)
        self.if_wst_s = self.interface(self.ifc.slave, "if_wst_s", is_port=True)

        # local variables
        self.if_wst_s_wr_clk_en_d = self.var("if_wst_s_wr_clk_en_d", 1)
        self.if_wst_s_rd_clk_en_d = self.var("if_wst_s_rd_clk_en_d", 1)
        self.if_est_m_wr_clk_en_sel_first_cycle = self.var("if_est_m_wr_clk_en_sel_first_cycle", 1)
        self.if_est_m_rd_clk_en_sel_first_cycle = self.var("if_est_m_rd_clk_en_sel_first_cycle", 1)
        self.if_est_m_wr_clk_en_sel_latch = self.var("if_est_m_wr_clk_en_sel_latch", 1)
        self.if_est_m_rd_clk_en_sel_latch = self.var("if_est_m_rd_clk_en_sel_latch", 1)
        self.if_est_m_wr_clk_en_sel = self.var("if_est_m_wr_clk_en_sel", 1)
        self.if_est_m_rd_clk_en_sel = self.var("if_est_m_rd_clk_en_sel", 1)
        self.clk_en_wst_s_d = self.var("clk_en_wst_s_d", 1)
        self.clk_en_est_m = self.var("clk_en_est_m", 1)
        self.if_est_m_wr_en_w = self.var("if_est_m_wr_en_w", 1)
        self.if_est_m_wr_addr_w = self.var("if_est_m_wr_addr_w", self.addr_width)
        self.if_est_m_wr_data_w = self.var("if_est_m_wr_data_w", self.data_width)
        self.if_est_m_wr_strb_w = self.var("if_est_m_wr_strb_w", self.data_width // 8)
        self.if_est_m_rd_en_w = self.var("if_est_m_rd_en_w", 1)
        self.if_est_m_rd_addr_w = self.var("if_est_m_rd_addr_w", self.addr_width)
        self.bank_wr_en = self.var("bank_wr_en", 1)
        self.bank_wr_strb = self.var("bank_wr_strb", self._params.bank_strb_width)
        self.bank_wr_addr = self.var("bank_wr_addr", self._params.glb_addr_width)
        self.bank_wr_data = self.var("bank_wr_data", self._params.bank_data_width)
        self.bank_rd_en = self.var("bank_rd_en", 1)
        self.bank_rd_addr = self.var("bank_rd_addr", self._params.glb_addr_width)
        self.rd_data_valid_w = self.var("rd_data_valid_w", 1)
        self.rd_data_w = self.var("rd_data_w", self.data_width)

        self.wr_tile_id_match = self.var("wr_tile_id_match", 1)
        self.rd_tile_id_match = self.var("rd_tile_id_match", 1)

        # local pararmeters
        self.tile_id_lsb = self._params.bank_addr_width + self._params.bank_sel_addr_width
        self.tile_id_msb = self.tile_id_lsb + self._params.tile_sel_addr_width - 1

        if self.data_width != self._params.bank_data_width:
            self.add_bank_rd_addr_sel_pipeline()
        self.add_always(self.tile_id_match)
        self.add_always(self.wr_logic, is_partial=(self.data_width != self._params.bank_data_width))
        self.add_always(self.rdrq_logic)
        self.add_always(self.rdrs_logic, is_partial=(self.data_width != self._params.bank_data_width))
        self.add_always(self.pipeline)
        self.add_always(self.clk_en_pipeline)
        self.add_always(self.est_m_clk_en_sel_first_cycle_comb)
        self.add_always(self.est_m_wr_clk_en_sel_latch)
        self.add_always(self.est_m_rd_clk_en_sel_latch)
        self.add_always(self.est_m_clk_en_sel_comb)
        self.add_always(self.est_m_wr_clk_en_mux)
        self.add_always(self.est_m_rd_clk_en_mux)
        self.add_sw2bank_clk_en()

    @always_comb
    def tile_id_match(self):
        self.wr_tile_id_match = self.glb_tile_id == self.if_wst_s.wr_addr[self.tile_id_msb, self.tile_id_lsb]
        self.rd_tile_id_match = self.glb_tile_id == self.if_wst_s.rd_addr[self.tile_id_msb, self.tile_id_lsb]

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def clk_en_pipeline(self):
        if self.reset:
            self.if_wst_s_wr_clk_en_d = 0
            self.if_wst_s_rd_clk_en_d = 0
        else:
            self.if_wst_s_wr_clk_en_d = self.if_wst_s.wr_clk_en
            self.if_wst_s_rd_clk_en_d = self.if_wst_s.rd_clk_en

    @always_comb
    def est_m_clk_en_sel_first_cycle_comb(self):
        self.if_est_m_wr_clk_en_sel_first_cycle = self.if_wst_s.wr_en & (~self.wr_tile_id_match)
        self.if_est_m_rd_clk_en_sel_first_cycle = self.if_wst_s.rd_en & (~self.rd_tile_id_match)

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def est_m_wr_clk_en_sel_latch(self):
        if self.reset:
            self.if_est_m_wr_clk_en_sel_latch = 0
        else:
            if self.if_wst_s.wr_en == 1:
                # If tile id matches, it does not feedthrough clk_en to the east
                if self.wr_tile_id_match:
                    self.if_est_m_wr_clk_en_sel_latch = 0
                else:
                    self.if_est_m_wr_clk_en_sel_latch = 1
            else:
                if self.if_wst_s.wr_clk_en == 0:
                    self.if_est_m_wr_clk_en_sel_latch = 0

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def est_m_rd_clk_en_sel_latch(self):
        if self.reset:
            self.if_est_m_rd_clk_en_sel_latch = 0
        else:
            if self.if_wst_s.rd_en == 1:
                # If tile id matches, it does not feedthrough clk_en to the east
                if self.rd_tile_id_match:
                    self.if_est_m_rd_clk_en_sel_latch = 0
                else:
                    self.if_est_m_rd_clk_en_sel_latch = 1
            else:
                if self.if_wst_s.rd_clk_en == 0:
                    self.if_est_m_rd_clk_en_sel_latch = 0

    @always_comb
    def est_m_clk_en_sel_comb(self):
        self.if_est_m_wr_clk_en_sel = (
            self.if_est_m_wr_clk_en_sel_first_cycle | self.if_est_m_wr_clk_en_sel_latch)
        self.if_est_m_rd_clk_en_sel = (
            self.if_est_m_rd_clk_en_sel_first_cycle | self.if_est_m_rd_clk_en_sel_latch)

    @always_comb
    def est_m_wr_clk_en_mux(self):
        if self.if_est_m_wr_clk_en_sel:
            self.if_est_m.wr_clk_en = self.if_wst_s_wr_clk_en_d
        else:
            self.if_est_m.wr_clk_en = 0

    @always_comb
    def est_m_rd_clk_en_mux(self):
        if self.if_est_m_rd_clk_en_sel:
            self.if_est_m.rd_clk_en = self.if_wst_s_rd_clk_en_d
        else:
            self.if_est_m.rd_clk_en = 0

    def add_sw2bank_clk_en(self):
        self.wr_clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_wr_delay + self._params.wr_clk_en_margin)
        self.sw2bank_wr_clk_en = self.var("sw2bank_wr_clk_en", 1)
        self.add_child("sw2bank_wr_clk_en_gen",
                       self.wr_clk_en_gen,
                       clk=self.mclk,
                       reset=self.reset,
                       enable=(self.if_wst_s.wr_en & self.wr_tile_id_match),
                       clk_en=self.sw2bank_wr_clk_en
                       )
        self.rd_clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_rd_delay + self._params.rd_clk_en_margin)
        self.sw2bank_rd_clk_en = self.var("sw2bank_rd_clk_en", 1)
        self.add_child("sw2bank_rd_clk_en_gen",
                       self.rd_clk_en_gen,
                       clk=self.mclk,
                       reset=self.reset,
                       enable=(self.if_wst_s.rd_en & self.rd_tile_id_match),
                       clk_en=self.sw2bank_rd_clk_en
                       )
        self.wire(self.clk_en_sw2bank, self.sw2bank_wr_clk_en | self.sw2bank_rd_clk_en)

    @always_comb
    def wr_logic(self, is_partial: bool):
        if self.if_wst_s.wr_en:
            if self.wr_tile_id_match:
                # Do not feedthrough to the east
                self.if_est_m_wr_en_w = 0
                self.if_est_m_wr_addr_w = 0
                self.if_est_m_wr_data_w = 0
                if self.ifc.is_strb is True:
                    self.if_est_m_wr_strb_w = 0
                # Send wr packet to switch
                if is_partial is True:
                    if self.if_wst_s.wr_addr[self._params.bank_byte_offset - 1] == 0:
                        self.bank_wr_en = 1
                        self.bank_wr_addr = self.if_wst_s.wr_addr
                        self.bank_wr_data = concat(const(0, self.bank_msb_data_width), self.if_wst_s.wr_data)
                        self.bank_wr_strb = concat(const(0, self.bank_msb_data_width // 8),
                                                   const(2**(self.bank_lsb_data_width // 8) - 1,
                                                         self.bank_lsb_data_width // 8))
                    else:
                        self.bank_wr_en = 1
                        self.bank_wr_addr = self.if_wst_s.wr_addr
                        self.bank_wr_data = concat(
                            self.if_wst_s.wr_data[self.bank_msb_data_width - 1, 0],
                            const(0, self.bank_lsb_data_width))
                        self.bank_wr_strb = concat(const(2**(self.bank_msb_data_width // 8) - 1,
                                                         self.bank_msb_data_width // 8),
                                                   const(0, self.bank_lsb_data_width // 8))
                else:
                    self.bank_wr_en = 1
                    self.bank_wr_addr = self.if_wst_s.wr_addr
                    self.bank_wr_data = self.if_wst_s.wr_data
                    self.bank_wr_strb = self.if_wst_s.wr_strb
            else:
                # Feedthrough to the east
                self.if_est_m_wr_en_w = self.if_wst_s.wr_en
                self.if_est_m_wr_addr_w = self.if_wst_s.wr_addr
                self.if_est_m_wr_data_w = self.if_wst_s.wr_data
                if self.ifc.is_strb is True:
                    self.if_est_m_wr_strb_w = self.if_wst_s.wr_strb
                # Gate packet to switch
                self.bank_wr_en = 0
                self.bank_wr_addr = 0
                self.bank_wr_data = 0
                self.bank_wr_strb = 0
        else:
            self.if_est_m_wr_en_w = 0
            self.if_est_m_wr_addr_w = 0
            self.if_est_m_wr_data_w = 0
            if self.ifc.is_strb is True:
                self.if_est_m_wr_strb_w = 0
            self.bank_wr_en = 0
            self.bank_wr_addr = 0
            self.bank_wr_data = 0
            self.bank_wr_strb = 0

    @ always_comb
    def rdrq_logic(self):
        if self.if_wst_s.rd_en:
            if self.rd_tile_id_match:
                # Do not feedthrough to the east
                self.if_est_m_rd_en_w = 0
                self.if_est_m_rd_addr_w = 0
                # Send rdrq packet to switch
                self.bank_rd_en = 1
                self.bank_rd_addr = self.if_wst_s.rd_addr
            else:
                # Feedthrough to the east
                self.if_est_m_rd_en_w = self.if_wst_s.rd_en
                self.if_est_m_rd_addr_w = self.if_wst_s.rd_addr
                self.bank_rd_en = 0
                self.bank_rd_addr = 0
        else:
            self.if_est_m_rd_en_w = 0
            self.if_est_m_rd_addr_w = 0
            self.bank_rd_en = 0
            self.bank_rd_addr = 0

    @ always_comb
    def rdrs_logic(self, is_partial: bool):
        self.rd_data_w = 0
        self.rd_data_valid_w = 0
        if self.rdrs_packet['rd_data_valid'] == 1:
            if is_partial:
                if self.bank_rd_addr_sel_d == 0:
                    self.rd_data_w = self.rdrs_packet['rd_data'][self.data_width - 1, 0]
                else:
                    self.rd_data_w = self.rdrs_packet['rd_data'][self.data_width * 2 - 1, self.data_width]
                self.rd_data_valid_w = 1
            else:
                self.rd_data_w = self.rdrs_packet['rd_data']
                self.rd_data_valid_w = 1
        elif self.if_est_m.rd_data_valid == 1:
            self.rd_data_w = self.if_est_m.rd_data
            self.rd_data_valid_w = 1

    def add_bank_rd_addr_sel_pipeline(self):
        self.bank_rd_latency = self._params.tile2sram_rd_delay + 1  # rdrq latency
        self.bank_rd_addr_sel_d = self.var("bank_rd_addr_sel_d", 1)
        self.bank_rd_addr_sel_pipeline = Pipeline(width=1, depth=self.bank_rd_latency)
        self.add_child("bank_rd_addr_sel_pipeline",
                       self.bank_rd_addr_sel_pipeline,
                       clk=self.gclk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.bank_rd_addr[self._params.bank_byte_offset - 1],
                       out_=self.bank_rd_addr_sel_d)

    @ always_ff((posedge, "gclk"), (posedge, "reset"))
    def pipeline(self):
        if self.reset:
            self.if_est_m.wr_en = 0
            if self.ifc.is_strb is True:
                self.if_est_m.wr_strb = 0
            self.if_est_m.wr_addr = 0
            self.if_est_m.wr_data = 0
            self.if_est_m.rd_en = 0
            self.if_est_m.rd_addr = 0
            self.if_wst_s.rd_data = 0
            self.if_wst_s.rd_data_valid = 0
            self.wr_packet['wr_en'] = 0
            self.wr_packet['wr_strb'] = 0
            self.wr_packet['wr_addr'] = 0
            self.wr_packet['wr_data'] = 0
            self.rdrq_packet['rd_en'] = 0
            self.rdrq_packet['rd_addr'] = 0
        else:
            self.if_est_m.wr_en = self.if_est_m_wr_en_w
            if self.ifc.is_strb is True:
                self.if_est_m.wr_strb = self.if_est_m_wr_strb_w
            self.if_est_m.wr_addr = self.if_est_m_wr_addr_w
            self.if_est_m.wr_data = self.if_est_m_wr_data_w
            self.if_est_m.rd_en = self.if_est_m_rd_en_w
            self.if_est_m.rd_addr = self.if_est_m_rd_addr_w
            self.if_wst_s.rd_data = self.rd_data_w
            self.if_wst_s.rd_data_valid = self.rd_data_valid_w
            self.wr_packet['wr_en'] = self.bank_wr_en
            self.wr_packet['wr_strb'] = self.bank_wr_strb
            self.wr_packet['wr_addr'] = self.bank_wr_addr
            self.wr_packet['wr_data'] = self.bank_wr_data
            self.rdrq_packet['rd_en'] = self.bank_rd_en
            self.rdrq_packet['rd_addr'] = self.bank_rd_addr
