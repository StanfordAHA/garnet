from kratos import Generator, always_comb, const, concat
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_header import GlbHeader


class GlbBankMux(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_bank_mux")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        # wr packet
        self.wr_packet_procsw2bank = self.input("wr_packet_procsw2bank", self.header.wr_packet_t)
        self.wr_packet_ring2bank = self.input("wr_packet_ring2bank", self.header.wr_packet_t)
        self.wr_packet_dma2bank = self.input("wr_packet_dma2bank", self.header.wr_packet_t)
        self.wr_packet_sw2bankarr = self.output(
            "wr_packet_sw2bankarr", self.header.wr_bank_packet_t, size=self._params.banks_per_tile)

        # rdrq packet
        self.rdrq_packet_procsw2bank = self.input("rdrq_packet_procsw2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_ring2bank = self.input("rdrq_packet_ring2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2bank = self.input("rdrq_packet_dma2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgring2bank = self.input("rdrq_packet_pcfgring2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgdma2bank = self.input("rdrq_packet_pcfgdma2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2bankarr = self.output(
            "rdrq_packet_sw2bankarr", self.header.rdrq_bank_packet_t, size=self._params.banks_per_tile)

        # rdrs packet
        self.rdrs_packet_bankarr2sw = self.input(
            "rdrs_packet_bankarr2sw", self.header.rdrs_packet_t, size=self._params.banks_per_tile)
        self.rdrs_packet_bank2procsw = self.output("rdrs_packet_bank2procsw", self.header.rdrs_packet_t)
        self.rdrs_packet_bank2ring = self.output("rdrs_packet_bank2ring", self.header.rdrs_packet_t)
        self.rdrs_packet_bank2dma = self.output("rdrs_packet_bank2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_bank2pcfgring = self.output("rdrs_packet_bank2pcfgring", self.header.rdrs_packet_t)
        self.rdrs_packet_bank2pcfgdma = self.output("rdrs_packet_bank2pcfgdma", self.header.rdrs_packet_t)

        # configuration
        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)
        self.cfg_pcfg_tile_connected_prev = self.input("cfg_pcfg_tile_connected_prev", 1)
        self.cfg_pcfg_tile_connected_next = self.input("cfg_pcfg_tile_connected_next", 1)

        # local variables
        self.wr_packet_sw2bankarr_w = self.var(
            "wr_packet_sw2bankarr_w", self.header.wr_bank_packet_t, size=self._params.banks_per_tile)

        self.rdrq_packet_sw2bankarr_w = self.var(
            "rdrq_packet_sw2bankarr_w", self.header.rdrq_bank_packet_t, size=self._params.banks_per_tile)

        self.rdrs_packet_bankarr2sw_d = self.var(
            "rdrs_packet_bankarr2sw_d", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        self.rd_type_e = self.enum("rd_type_e", {"none": 0, "proc": 1, "strm": 2, "pcfg": 3})
        # FIXME: Kratos does not support array of enum type
        # Just use python array
        self.rd_type = []
        self.rd_type_d = []
        for i in range(self._params.banks_per_tile):
            self.rd_type.append(self.var(f"rd_type_{i}", self.rd_type_e))
            self.rd_type_d.append(self.var(f"rd_type_d_{i}", self.rd_type_e))

        # wr pipeline
        for i in range(self._params.banks_per_tile):
            self.wr_sw2bank_pipeline = Pipeline(
                width=self.wr_packet_sw2bankarr_w[i].width, depth=self._params.glb_sw2bank_pipeline_depth)
            self.add_child(f"wr_sw2bank_pipeline_{i}",
                           self.wr_sw2bank_pipeline,
                           clk=self.clk,
                           clk_en=const(1, 1),
                           reset=self.reset,
                           in_=self.wr_packet_sw2bankarr_w[i],
                           out_=self.wr_packet_sw2bankarr[i])

        # rdrq pipeline
        for i in range(self._params.banks_per_tile):
            self.rdrq_sw2bank_pipeline = Pipeline(
                width=self.rdrq_packet_sw2bankarr_w[i].width, depth=self._params.glb_sw2bank_pipeline_depth)
            self.add_child(f"rdrq_sw2bank_pipeline_{i}",
                           self.rdrq_sw2bank_pipeline,
                           clk=self.clk,
                           clk_en=const(1, 1),
                           reset=self.reset,
                           in_=self.rdrq_packet_sw2bankarr_w[i],
                           out_=self.rdrq_packet_sw2bankarr[i])

        rd_type_pipeline_in = concat(*self.rd_type)
        rd_type_pipeline_out = concat(*self.rd_type_d)
        self.rd_type_pipeline = Pipeline(width=rd_type_pipeline_in.width, depth=self._params.bankmux2sram_rd_delay)
        self.add_child(f"rd_type_pipeline_{i}",
                       self.rd_type_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=rd_type_pipeline_in,
                       out_=rd_type_pipeline_out)

        # rdrs pipeline
        for i in range(self._params.banks_per_tile):
            self.rdrs_bank2sw_pipeline = Pipeline(
                width=self.rdrs_packet_bankarr2sw[i].width, depth=self._params.glb_bank2sw_pipeline_depth)
            self.add_child(f"rdrs_bank2sw_pipeline_{i}",
                           self.rdrs_bank2sw_pipeline,
                           clk=self.clk,
                           clk_en=const(1, 1),
                           reset=self.reset,
                           in_=self.rdrs_packet_bankarr2sw[i],
                           out_=self.rdrs_packet_bankarr2sw_d[i])

        # localparam
        self.tile_sel_msb = _params.bank_addr_width + _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1
        self.tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width
        self.bank_sel_msb = _params.bank_addr_width + _params.bank_sel_addr_width - 1
        self.bank_sel_lsb = _params.bank_addr_width

        # Add always statements
        # wr packet
        for i in range(self._params.banks_per_tile):
            self.add_always(self.wr_sw2bankarr_logic, i=i)

        # rdrq packet
        for i in range(self._params.banks_per_tile):
            self.add_always(self.rdrq_sw2bankarr_logic, i=i)

        # rdrs packet
        self.add_always(self.rdrs_sw2dma_logic)
        self.add_always(self.rdrs_sw2sr_logic)
        self.add_always(self.rdrs_sw2pr_logic)
        self.add_always(self.rdrs_sw2pcfgdma_logic)
        self.add_always(self.rdrs_sw2pcfgr_logic)

    @always_comb
    def wr_sw2bankarr_logic(self, i):
        if ((self.wr_packet_procsw2bank['wr_en'] == 1)
                & (self.wr_packet_procsw2bank['wr_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id)
                & (self.wr_packet_procsw2bank['wr_addr'][self.bank_sel_msb, self.bank_sel_lsb] == i)):
            self.wr_packet_sw2bankarr_w[i]['wr_en'] = self.wr_packet_procsw2bank['wr_en']
            self.wr_packet_sw2bankarr_w[i]['wr_addr'] = self.wr_packet_procsw2bank['wr_addr'][(
                self._params.bank_addr_width - 1), 0]
            self.wr_packet_sw2bankarr_w[i]['wr_strb'] = self.wr_packet_procsw2bank['wr_strb']
            self.wr_packet_sw2bankarr_w[i]['wr_data'] = self.wr_packet_procsw2bank['wr_data']
        elif ((self.wr_packet_dma2bank['wr_en'] == 1)
                & ((~self.cfg_tile_connected_prev) & (~self.cfg_tile_connected_next))
                & (self.wr_packet_dma2bank['wr_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id)
                & (self.wr_packet_dma2bank['wr_addr'][self.bank_sel_msb, self.bank_sel_lsb] == i)):
            self.wr_packet_sw2bankarr_w[i]['wr_en'] = self.wr_packet_dma2bank['wr_en']
            self.wr_packet_sw2bankarr_w[i]['wr_addr'] = self.wr_packet_dma2bank['wr_addr'][(
                self._params.bank_addr_width - 1), 0]
            self.wr_packet_sw2bankarr_w[i]['wr_strb'] = self.wr_packet_dma2bank['wr_strb']
            self.wr_packet_sw2bankarr_w[i]['wr_data'] = self.wr_packet_dma2bank['wr_data']
        elif ((self.wr_packet_ring2bank['wr_en'] == 1)
                & (self.wr_packet_ring2bank['wr_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id)
                & (self.wr_packet_ring2bank['wr_addr'][self.bank_sel_msb, self.bank_sel_lsb] == i)):
            self.wr_packet_sw2bankarr_w[i]['wr_en'] = self.wr_packet_ring2bank['wr_en']
            self.wr_packet_sw2bankarr_w[i]['wr_addr'] = self.wr_packet_ring2bank['wr_addr'][(
                self._params.bank_addr_width - 1), 0]
            self.wr_packet_sw2bankarr_w[i]['wr_strb'] = self.wr_packet_ring2bank['wr_strb']
            self.wr_packet_sw2bankarr_w[i]['wr_data'] = self.wr_packet_ring2bank['wr_data']
        else:
            self.wr_packet_sw2bankarr_w[i] = 0

    @ always_comb
    def rdrq_sw2bankarr_logic(self, i):
        if ((self.rdrq_packet_procsw2bank['rd_en'] == 1)
                & (self.rdrq_packet_procsw2bank['rd_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id)
                & (self.rdrq_packet_procsw2bank['rd_addr'][self.bank_sel_msb, self.bank_sel_lsb] == i)):
            self.rdrq_packet_sw2bankarr_w[i]['rd_en'] = self.rdrq_packet_procsw2bank['rd_en']
            self.rdrq_packet_sw2bankarr_w[i]['rd_addr'] = self.rdrq_packet_procsw2bank['rd_addr'][(
                self._params.bank_addr_width - 1), 0]
            self.rd_type[i] = self.rd_type_e.proc
        elif ((self.rdrq_packet_pcfgdma2bank['rd_en'] == 1)
                & ((~self.cfg_pcfg_tile_connected_prev) & (~self.cfg_pcfg_tile_connected_next))
                & (self.rdrq_packet_pcfgdma2bank['rd_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id)
                & (self.rdrq_packet_pcfgdma2bank['rd_addr'][self.bank_sel_msb, self.bank_sel_lsb] == i)):
            self.rdrq_packet_sw2bankarr_w[i]['rd_en'] = self.rdrq_packet_pcfgdma2bank['rd_en']
            self.rdrq_packet_sw2bankarr_w[i]['rd_addr'] = self.rdrq_packet_pcfgdma2bank['rd_addr'][(
                self._params.bank_addr_width - 1), 0]
            self.rd_type[i] = self.rd_type_e.pcfg
        elif ((self.rdrq_packet_pcfgring2bank['rd_en'] == 1)
                & (self.rdrq_packet_pcfgring2bank['rd_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id)
                & (self.rdrq_packet_pcfgring2bank['rd_addr'][self.bank_sel_msb, self.bank_sel_lsb] == i)):
            self.rdrq_packet_sw2bankarr_w[i]['rd_en'] = self.rdrq_packet_pcfgring2bank['rd_en']
            self.rdrq_packet_sw2bankarr_w[i]['rd_addr'] = self.rdrq_packet_pcfgring2bank['rd_addr'][(
                self._params.bank_addr_width - 1), 0]
            self.rd_type[i] = self.rd_type_e.pcfg
        elif ((self.rdrq_packet_dma2bank['rd_en'] == 1)
                & ((~self.cfg_tile_connected_prev) & (~self.cfg_tile_connected_next))
                & (self.rdrq_packet_dma2bank['rd_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id)
                & (self.rdrq_packet_dma2bank['rd_addr'][self.bank_sel_msb, self.bank_sel_lsb] == i)):
            self.rdrq_packet_sw2bankarr_w[i]['rd_en'] = self.rdrq_packet_dma2bank['rd_en']
            self.rdrq_packet_sw2bankarr_w[i]['rd_addr'] = self.rdrq_packet_dma2bank['rd_addr'][(
                self._params.bank_addr_width - 1), 0]
            self.rd_type[i] = self.rd_type_e.strm
        elif ((self.rdrq_packet_ring2bank['rd_en'] == 1)
                & (self.rdrq_packet_ring2bank['rd_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id)
                & (self.rdrq_packet_ring2bank['rd_addr'][self.bank_sel_msb, self.bank_sel_lsb] == i)):
            self.rdrq_packet_sw2bankarr_w[i]['rd_en'] = self.rdrq_packet_ring2bank['rd_en']
            self.rdrq_packet_sw2bankarr_w[i]['rd_addr'] = self.rdrq_packet_ring2bank['rd_addr'][(
                self._params.bank_addr_width - 1), 0]
            self.rd_type[i] = self.rd_type_e.strm
        else:
            self.rdrq_packet_sw2bankarr_w[i] = 0
            self.rd_type[i] = self.rd_type_e.none

    @ always_comb
    def rdrs_sw2dma_logic(self):
        self.rdrs_packet_bank2dma = 0
        if ((~self.cfg_tile_connected_next) & (~self.cfg_tile_connected_prev)):
            for i in range(self._params.banks_per_tile):
                if self.rd_type_d[i] == self.rd_type_e.strm:
                    self.rdrs_packet_bank2dma = self.rdrs_packet_bankarr2sw_d[i]

    @ always_comb
    def rdrs_sw2sr_logic(self):
        self.rdrs_packet_bank2ring = 0
        if (self.cfg_tile_connected_next | self.cfg_tile_connected_prev):
            for i in range(self._params.banks_per_tile):
                if self.rd_type_d[i] == self.rd_type_e.strm:
                    self.rdrs_packet_bank2ring = self.rdrs_packet_bankarr2sw_d[i]

    @ always_comb
    def rdrs_sw2pr_logic(self):
        self.rdrs_packet_bank2procsw = 0
        for i in range(self._params.banks_per_tile):
            if self.rd_type_d[i] == self.rd_type_e.proc:
                self.rdrs_packet_bank2procsw = self.rdrs_packet_bankarr2sw_d[i]

    @ always_comb
    def rdrs_sw2pcfgdma_logic(self):
        self.rdrs_packet_bank2pcfgdma = 0
        if (~self.cfg_pcfg_tile_connected_next) & (~self.cfg_pcfg_tile_connected_prev):
            for i in range(self._params.banks_per_tile):
                if self.rd_type_d[i] == self.rd_type_e.pcfg:
                    self.rdrs_packet_bank2pcfgdma = self.rdrs_packet_bankarr2sw_d[i]

    @ always_comb
    def rdrs_sw2pcfgr_logic(self):
        self.rdrs_packet_bank2pcfgring = 0
        if (self.cfg_pcfg_tile_connected_next | self.cfg_pcfg_tile_connected_prev):
            for i in range(self._params.banks_per_tile):
                if self.rd_type_d[i] == self.rd_type_e.pcfg:
                    self.rdrs_packet_bank2pcfgring = self.rdrs_packet_bankarr2sw_d[i]
