from kratos import Generator, always_ff, always_comb, posedge, const, concat
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_header import GlbHeader


class GlbSwitch(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_switch")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        # wr packet
        self.wr_packet_pr2sw = self.input("wr_packet_pr2sw", self.header.wr_packet_t)
        self.wr_packet_sr2sw = self.input("wr_packet_sr2sw", self.header.wr_packet_t)
        self.wr_packet_sw2sr = self.output("wr_packet_sw2sr", self.header.wr_packet_t)
        self.wr_packet_dma2sw = self.input("wr_packet_dma2sw", self.header.wr_packet_t)
        self.wr_packet_sw2bankarr = self.output(
            "wr_packet_sw2bankarr", self.header.wr_packet_t, size=self._params.banks_per_tile)

        # rdrq packet
        self.rdrq_packet_pr2sw = self.input("rdrq_packet_pr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sr2sw = self.input("rdrq_packet_sr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2sr = self.output("rdrq_packet_sw2sr", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2sw = self.input("rdrq_packet_dma2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgr2sw = self.input("rdrq_packet_pcfgr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2pcfgr = self.output("rdrq_packet_sw2pcfgr", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgdma2sw = self.input("rdrq_packet_pcfgdma2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2bankarr = self.output(
            "rdrq_packet_sw2bankarr", self.header.rdrq_packet_t, size=self._params.banks_per_tile)

        # rdrs packet
        self.rdrs_packet_sw2pr = self.output("rdrs_packet_sw2pr", self.header.rdrs_packet_t)
        self.rdrs_packet_sr2sw = self.input("rdrs_packet_sr2sw", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2sr = self.output("rdrs_packet_sw2sr", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2dma = self.output("rdrs_packet_sw2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_pcfgr2sw = self.input("rdrs_packet_pcfgr2sw", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2pcfgr = self.output("rdrs_packet_sw2pcfgr", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2pcfgdma = self.output("rdrs_packet_sw2pcfgdma", self.header.rdrs_packet_t)
        self.rdrs_packet_bankarr2sw = self.input(
            "rdrs_packet_bankarr2sw", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        # configuration
        self.cfg_st_dma_ctrl_mode = self.input("cfg_st_dma_ctrl_mode", 2)
        self.cfg_ld_dma_ctrl_mode = self.input("cfg_ld_dma_ctrl_mode", 2)
        self.cfg_pcfg_dma_ctrl_mode = self.input("cfg_pcfg_dma_ctrl_mode", 1)
        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)
        self.cfg_pcfg_tile_connected_prev = self.input("cfg_pcfg_tile_connected_prev", 1)
        self.cfg_pcfg_tile_connected_next = self.input("cfg_pcfg_tile_connected_next", 1)

        # local variables
        self.wr_packet_sw2bankarr_w = self.var(
            "wr_packet_sw2bankarr_w", self.header.wr_packet_t, size=self._params.banks_per_tile)
        self.wr_packet_sw2sr_w = self.var("wr_packet_sw2sr_w", self.header.wr_packet_t)
        self.wr_packet_sw2bank_muxed = self.var("wr_packet_sw2bank_muxed", self.header.wr_packet_t)

        self.rdrq_packet_sw2bankarr_w = self.var(
            "rdrq_packet_sw2bankarr_w", self.header.rdrq_packet_t, size=self._params.banks_per_tile)
        self.rdrq_packet_sw2bank_muxed = self.var("rdrq_packet_sw2bank_muxed", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2sr_w = self.var("rdrq_packet_sw2sr_w", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2pcfgr_w = self.var("rdrq_packet_sw2pcfgr_w", self.header.rdrq_packet_t)

        self.rdrs_packet_pcfgr2sw_d = self.var("rdrs_packet_pcfgr2sw_d", self.header.rdrs_packet_t)
        self.rdrs_packet_sr2sw_d = self.var("rdrs_packet_sr2sw_d", self.header.rdrs_packet_t)

        self.rdrs_packet_bankarr2sw_d = self.var(
            "rdrs_packet_bankarr2sw_d", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        self.rd_type_e = self.enum("rd_type_e", {"none": 0, "proc": 1, "strm": 2, "pcfg": 3})
        self.rd_type = self.var("rd_type", self.rd_type_e)
        self.rd_type_d = self.var("rd_type_d", self.rd_type_e)
        self.rdrq_bank_sel = self.var("rdrq_bank_sel", self._params.bank_sel_addr_width)
        self.rdrq_bank_sel_d = self.var("rdrq_bank_sel_d", self._params.bank_sel_addr_width)
        self.wr_bank_sel = self.var("wr_bank_sel", self._params.bank_sel_addr_width)

        # wr pipeline
        for i in range(self._params.banks_per_tile):
            self.wr_sw2bank_pipeline = Pipeline(width=self.wr_packet_sw2bankarr_w[i].width, depth=self._params.glb_sw2bank_pipeline_depth)
            self.add_child(f"wr_sw2bank_pipeline_{i}",
                           self.wr_sw2bank_pipeline,
                           clk=self.clk,
                           clk_en=const(1, 1),
                           reset=self.reset,
                           in_=self.wr_packet_sw2bankarr_w[i],
                           out_=self.wr_packet_sw2bankarr[i])

        # rdrq pipeline
        for i in range(self._params.banks_per_tile):
            self.rdrq_sw2bank_pipeline = Pipeline(width=self.rdrq_packet_sw2bankarr_w[i].width, depth=self._params.glb_sw2bank_pipeline_depth)
            self.add_child(f"rdrq_sw2bank_pipeline_{i}",
                           self.rdrq_sw2bank_pipeline,
                           clk=self.clk,
                           clk_en=const(1, 1),
                           reset=self.reset,
                           in_=self.rdrq_packet_sw2bankarr_w[i],
                           out_=self.rdrq_packet_sw2bankarr[i])

        pipeline_depth = (self._params.glb_bank_memory_pipeline_depth
                          + self._params.sram_gen_pipeline_depth
                          + self._params.sram_gen_output_pipeline_depth
                          + self._params.glb_sw2bank_pipeline_depth
                          + self._params.glb_bank2sw_pipeline_depth
                          + 1)

        self.rdrq_pipeline_in = concat(self.rd_type, self.rdrq_bank_sel)
        self.rdrq_pipeline_out = concat(self.rd_type_d, self.rdrq_bank_sel_d)
        self.rdrq_pipeline = Pipeline(width=self.rdrq_pipeline_in.width, depth=pipeline_depth)
        self.add_child("rdrq_pipeline",
                       self.rdrq_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.rdrq_pipeline_in,
                       out_=self.rdrq_pipeline_out)


        # rdrs pipeline
        for i in range(self._params.banks_per_tile):
            self.rdrs_bank2sw_pipeline = Pipeline(width=self.rdrs_packet_bankarr2sw[i].width, depth=self._params.glb_bank2sw_pipeline_depth)
            self.add_child(f"rdrs_bank2sw_pipeline_{i}",
                           self.rdrs_bank2sw_pipeline,
                           clk=self.clk,
                           clk_en=const(1, 1),
                           reset=self.reset,
                           in_=self.rdrs_packet_bankarr2sw[i],
                           out_=self.rdrs_packet_bankarr2sw_d[i])

        self.rdrs_sr2sw_pipeline = Pipeline(width=self.rdrs_packet_sr2sw.width, depth=self._params.glb_bank2sw_pipeline_depth)
        self.add_child(f"rdrs_sr2sw_pipeline",
                       self.rdrs_sr2sw_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.rdrs_packet_sr2sw,
                       out_=self.rdrs_packet_sr2sw_d)

        self.rdrs_pcfgr2sw_pipeline = Pipeline(width=self.rdrs_packet_pcfgr2sw.width, depth=self._params.glb_bank2sw_pipeline_depth)
        self.add_child(f"rdrs_pcfgr2sw_pipeline",
                       self.rdrs_pcfgr2sw_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.rdrs_packet_pcfgr2sw,
                       out_=self.rdrs_packet_pcfgr2sw_d)

        # localparam
        self.packet_addr_tile_sel_msb = (_params.bank_addr_width
                                         + _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1)
        self.packet_addr_tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width
        self.packet_addr_bank_sel_msb = _params.bank_addr_width + _params.bank_sel_addr_width - 1
        self.packet_addr_bank_sel_lsb = _params.bank_addr_width

        # Add always statements
        # wr packet
        self.add_always(self.wr_sw2bank_muxed_logic)
        self.add_always(self.wr_sw2bankarr_logic)
        self.add_always(self.wr_sw2sr_logic)
        self.add_always(self.wr_sw2sr_pipeline)

        # rdrq packet
        self.add_always(self.rdrq_sw2bank_muxed_logic)
        self.add_always(self.rdrq_sw2bankarr_logic)
        self.add_always(self.rdrq_sw2sr_logic)
        self.add_always(self.rdrq_sw2sr_pipeline)
        self.add_always(self.rdrq_sw2pcfgr_logic)
        self.add_always(self.rdrq_sw2pcfgr_pipeline)

        # rdrs packet
        self.add_always(self.rdrs_sw2dma_logic)
        self.add_always(self.rdrs_sw2sr_logic)
        self.add_always(self.rdrs_sw2pr_logic)
        self.add_always(self.rdrs_sw2pcfgdma_logic)
        self.add_always(self.rdrs_sw2pcfgr_logic)

    @always_comb
    def wr_sw2bank_muxed_logic(self):
        if ((self.wr_packet_pr2sw['wr_en'] == 1)
                & (self.wr_packet_pr2sw['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                   == self.glb_tile_id)):
            self.wr_packet_sw2bank_muxed = self.wr_packet_pr2sw
        elif ((self.wr_packet_dma2sw['wr_en'] == 1)
              & (~self.cfg_tile_connected_prev) & (~self.cfg_tile_connected_next)
              & (self.wr_packet_dma2sw['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
              == self.glb_tile_id)):
            self.wr_packet_sw2bank_muxed = self.wr_packet_dma2sw
        elif ((self.wr_packet_sr2sw['wr_en'] == 1)
                & (self.wr_packet_sr2sw['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                   == self.glb_tile_id)):
            self.wr_packet_sw2bank_muxed = self.wr_packet_sr2sw
        else:
            self.wr_packet_sw2bank_muxed = 0
        self.wr_bank_sel = self.wr_packet_sw2bank_muxed['wr_addr'][
            self.packet_addr_bank_sel_msb, self.packet_addr_bank_sel_lsb]

    @always_comb
    def wr_sw2bankarr_logic(self):
        for i in range(self._params.banks_per_tile):
            if self.wr_bank_sel == i:
                self.wr_packet_sw2bankarr_w[i] = self.wr_packet_sw2bank_muxed
            else:
                self.wr_packet_sw2bankarr_w[i] = 0

    @always_comb
    def wr_sw2sr_logic(self):
        if (self.cfg_st_dma_ctrl_mode != 0) & ((self.cfg_tile_connected_next) | (self.cfg_tile_connected_prev)):
            self.wr_packet_sw2sr_w = self.wr_packet_dma2sw
        else:
            self.wr_packet_sw2sr_w = 0

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def wr_sw2sr_pipeline(self):
        if self.reset:
            self.wr_packet_sw2sr = 0
        else:
            self.wr_packet_sw2sr = self.wr_packet_sw2sr_w

    @ always_comb
    def rdrq_sw2bank_muxed_logic(self):
        if ((self.rdrq_packet_pr2sw['rd_en'] == 1)
            & (self.rdrq_packet_pr2sw['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
               == self.glb_tile_id)):
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_pr2sw
            self.rd_type = self.rd_type_e.proc
        elif ((self.rdrq_packet_pcfgdma2sw['rd_en'] == 1)
              & (~self.cfg_pcfg_tile_connected_prev) & (~self.cfg_pcfg_tile_connected_next)
              & (self.rdrq_packet_pcfgdma2sw['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                 == self.glb_tile_id)):
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_pcfgdma2sw
            self.rd_type = self.rd_type_e.pcfg
        elif ((self.rdrq_packet_pcfgr2sw['rd_en'] == 1)
              & (self.rdrq_packet_pcfgr2sw['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                 == self.glb_tile_id)):
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_pcfgr2sw
            self.rd_type = self.rd_type_e.pcfg
        elif ((self.rdrq_packet_dma2sw['rd_en'] == 1)
              & (~self.cfg_tile_connected_prev) & (~self.cfg_tile_connected_next)
              & (self.rdrq_packet_dma2sw['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                 == self.glb_tile_id)):
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_dma2sw
            self.rd_type = self.rd_type_e.strm
        elif ((self.rdrq_packet_sr2sw['rd_en'] == 1)
              & (self.rdrq_packet_sr2sw['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                 == self.glb_tile_id)):
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_sr2sw
            self.rd_type = self.rd_type_e.strm
        else:
            self.rdrq_packet_sw2bank_muxed = 0
            self.rd_type = self.rd_type_e.none
        self.rdrq_bank_sel = self.rdrq_packet_sw2bank_muxed['rd_addr'][self.packet_addr_bank_sel_msb,
                                                                       self.packet_addr_bank_sel_lsb]

    @ always_comb
    def rdrq_sw2bankarr_logic(self):
        for i in range(self._params.banks_per_tile):
            if self.rdrq_bank_sel == i:
                self.rdrq_packet_sw2bankarr_w[i] = self.rdrq_packet_sw2bank_muxed
            else:
                self.rdrq_packet_sw2bankarr_w[i] = 0

    @ always_comb
    def rdrq_sw2sr_logic(self):
        if (self.cfg_ld_dma_ctrl_mode != 0) & ((self.cfg_tile_connected_next) | (self.cfg_tile_connected_prev)):
            self.rdrq_packet_sw2sr_w = self.rdrq_packet_dma2sw
        else:
            self.rdrq_packet_sw2sr_w = 0

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_sw2sr_pipeline(self):
        if self.reset:
            self.rdrq_packet_sw2sr = 0
        else:
            self.rdrq_packet_sw2sr = self.rdrq_packet_sw2sr_w

    @ always_comb
    def rdrq_sw2pcfgr_logic(self):
        if ((self.cfg_pcfg_dma_ctrl_mode != 0)
            & ((self.cfg_pcfg_tile_connected_next) | (self.cfg_pcfg_tile_connected_prev))
                & (self.rdrq_packet_pcfgdma2sw['rd_addr'][self.packet_addr_tile_sel_msb,
                                                          self.packet_addr_tile_sel_lsb]
                   != self.glb_tile_id)):
            self.rdrq_packet_sw2pcfgr_w = self.rdrq_packet_pcfgdma2sw
        else:
            self.rdrq_packet_sw2pcfgr_w = 0

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_sw2pcfgr_pipeline(self):
        if self.reset:
            self.rdrq_packet_sw2pcfgr = 0
        else:
            self.rdrq_packet_sw2pcfgr = self.rdrq_packet_sw2pcfgr_w

    @ always_comb
    def rdrs_sw2dma_logic(self):
        if self.cfg_ld_dma_ctrl_mode != 0:
            if (~self.cfg_tile_connected_next) & (~self.cfg_tile_connected_prev):
                if self.rd_type_d == self.rd_type_e.strm:
                    self.rdrs_packet_sw2dma = self.rdrs_packet_bankarr2sw_d[self.rdrq_bank_sel_d]
                else:
                    self.rdrs_packet_sw2dma = 0
            else:
                self.rdrs_packet_sw2dma = self.rdrs_packet_sr2sw_d
        else:
            self.rdrs_packet_sw2dma = 0

    @ always_comb
    def rdrs_sw2sr_logic(self):
        if (~self.cfg_tile_connected_next) & (~self.cfg_tile_connected_prev):
            self.rdrs_packet_sw2sr = 0
        else:
            if self.rd_type_d == self.rd_type_e.strm:
                self.rdrs_packet_sw2sr = self.rdrs_packet_bankarr2sw_d[self.rdrq_bank_sel_d]
            else:
                self.rdrs_packet_sw2sr = 0

    # rdrs proc
    @ always_comb
    def rdrs_sw2pr_logic(self):
        if self.rd_type_d == self.rd_type_e.proc:
            self.rdrs_packet_sw2pr = self.rdrs_packet_bankarr2sw_d[self.rdrq_bank_sel_d]
        else:
            self.rdrs_packet_sw2pr = 0

    @ always_comb
    def rdrs_sw2pcfgdma_logic(self):
        if self.cfg_pcfg_dma_ctrl_mode != 0:
            if (~self.cfg_pcfg_tile_connected_next) & (~self.cfg_pcfg_tile_connected_prev):
                if self.rd_type_d == self.rd_type_e.pcfg:
                    self.rdrs_packet_sw2pcfgdma = self.rdrs_packet_bankarr2sw_d[self.rdrq_bank_sel_d]
                else:
                    self.rdrs_packet_sw2pcfgdma = 0
            else:
                self.rdrs_packet_sw2pcfgdma = self.rdrs_packet_pcfgr2sw_d
        else:
            self.rdrs_packet_sw2pcfgdma = 0

    @ always_comb
    def rdrs_sw2pcfgr_logic(self):
        if (~self.cfg_pcfg_tile_connected_next) & (~self.cfg_pcfg_tile_connected_prev):
            self.rdrs_packet_sw2pcfgr = 0
        else:
            if self.rd_type_d == self.rd_type_e.pcfg:
                self.rdrs_packet_sw2pcfgr = self.rdrs_packet_bankarr2sw_d[self.rdrq_bank_sel_d]
            else:
                self.rdrs_packet_sw2pcfgr = 0
