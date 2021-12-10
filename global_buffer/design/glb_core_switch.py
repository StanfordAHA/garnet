from kratos import Generator, always_ff, always_comb, posedge, concat
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbCoreSwitch(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_core_switch")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.clk_en = self.input("clk_en", 1)
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input(
            "glb_tile_id", self._params.tile_sel_addr_width)

        # wr packet
        self.wr_packet_pr2sw = self.input(
            "wr_packet_pr2sw", self.header.wr_packet_t)
        self.wr_packet_sr2sw = self.input(
            "wr_packet_sr2sw", self.header.wr_packet_t)
        self.wr_packet_sw2sr = self.output(
            "wr_packet_sw2sr", self.header.wr_packet_t)
        self.wr_packet_dma2sw = self.input(
            "wr_packet_dma2sw", self.header.wr_packet_t)
        self.wr_packet_sw2bankarr = self.output(
            "wr_packet_sw2bankarr", self.header.wr_packet_t, size=self._params.banks_per_tile)

        # rdrq packet
        self.rdrq_packet_pr2sw = self.input(
            "rdrq_packet_pr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sr2sw = self.input(
            "rdrq_packet_sr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2sr = self.output(
            "rdrq_packet_sw2sr", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2sw = self.input(
            "rdrq_packet_dma2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgr2sw = self.input(
            "rdrq_packet_pcfgr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2pcfgr = self.output(
            "rdrq_packet_sw2pcfgr", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgdma2sw = self.input(
            "rdrq_packet_pcfgdma2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2bankarr = self.output(
            "rdrq_packet_sw2bankarr", self.header.rdrq_packet_t, size=self._params.banks_per_tile)

        # rdrs packet
        self.rdrs_packet_sw2pr = self.output(
            "rdrs_packet_sw2pr", self.header.rdrs_packet_t)
        self.rdrs_packet_sr2sw = self.input(
            "rdrs_packet_sr2sw", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2sr = self.output(
            "rdrs_packet_sw2sr", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2dma = self.output(
            "rdrs_packet_sw2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_pcfgr2sw = self.input(
            "rdrs_packet_pcfgr2sw", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2pcfgr = self.output(
            "rdrs_packet_sw2pcfgr", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2pcfgdma = self.output(
            "rdrs_packet_sw2pcfgdma", self.header.rdrs_packet_t)
        self.rdrs_packet_bankarr2sw = self.input(
            "rdrs_packet_bankarr2sw", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        # configuration
        self.cfg_st_dma_ctrl_mode = self.input("cfg_st_dma_ctrl_mode", 2)
        self.cfg_ld_dma_ctrl_mode = self.input("cfg_ld_dma_ctrl_mode", 2)
        self.cfg_pcfg_dma_ctrl_mode = self.input("cfg_pcfg_dma_ctrl_mode", 1)
        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)

        # local variables
        assert self._params.glb_switch_pipeline_depth == 1  # switch pipeline depth is fixed to 1
        self.wr_packet_sr2sw_d = self.var(
            "wr_packet_sr2sw_d", self.header.wr_packet_t)
        self.wr_packet_pr2sw_d = self.var(
            "wr_packet_pr2sw_d", self.header.wr_packet_t)
        self.wr_packet_dma2sw_d = self.var(
            "wr_packet_dma2sw_d", self.header.wr_packet_t)
        self.wr_packet_sw2bank_muxed = self.var(
            "wr_packet_sw2bank_muxed", self.header.wr_packet_t)
        self.wr_packet_sw2bank_filtered = self.var(
            "wr_packet_sw2bank_filtered", self.header.wr_packet_t)

        self.rdrq_packet_pr2sw_d = self.var(
            "rdrq_packet_pr2sw_d", self.header.rdrq_packet_t)
        self.rdrq_packet_sr2sw_d = self.var(
            "rdrq_packet_sr2sw_d", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2sw_d = self.var(
            "rdrq_packet_dma2sw_d", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgr2sw_d = self.var(
            "rdrq_packet_pcfgr2sw_d", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgdma2sw_d = self.var(
            "rdrq_packet_pcfgdma2sw_d", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2bank_muxed = self.var(
            "rdrq_packet_sw2bank_muxed", self.header.rdrq_packet_t)

        self.rdrs_packet_pcfgr2sw_d = self.var(
            "rdrs_packet_pcfgr2sw_d", self.header.rdrs_packet_t)
        self.rdrs_packet_sr2sw_d = self.var(
            "rdrs_packet_sr2sw_d", self.header.rdrs_packet_t)

        self.rdrs_packet_bankarr2sw_sr_d = self.var(
            "rdrs_packet_bankarr2sw_sr_d ", self.header.rdrs_packet_t, size=self._params.banks_per_tile)
        self.rdrs_packet_bankarr2sw_pr_d = self.var(
            "rdrs_packet_bankarr2sw_pr_d ", self.header.rdrs_packet_t, size=self._params.banks_per_tile)
        self.rdrs_packet_bankarr2sw_pcfgr_d = self.var(
            "rdrs_packet_bankarr2sw_pcfgr_d ", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        # packet src enum
        self.packet_src_e = self.enum("packet_src_e", {
            "none": 0, "proc": 1, "strm_dma": 2, "strm_rtr": 3, "pcfg_dma": 4, "pcfg_rtr": 5})
        # TODO: Kratos doesn't support array of enum instances yet
        self.rdrq_sel = self.var("rdrq_sel", self.packet_src_e)
        self.rdrq_sel_d = []
        self.rdrq_sel_d_nostall = []
        for i in range(self._params.glb_bank_memory_pipeline_depth
                       + self._params.sram_gen_pipeline_depth
                       + self._params.sram_gen_output_pipeline_depth
                       + self._params.glb_switch_pipeline_depth
                       + 1):
            self.rdrq_sel_d.append(
                self.var(f"rdrq_sel_d{i+1}", self.packet_src_e))
            self.rdrq_sel_d_nostall.append(
                self.var(f"rdrq_sel_d{i+1}_nostall", self.packet_src_e))

        self.rdrq_bank_sel = self.var(
            "rdrq_bank_sel", self._params.bank_sel_addr_width)
        self.rdrq_bank_sel_d = []
        self.rdrq_bank_sel_d_nostall = []
        for i in range(self._params.glb_bank_memory_pipeline_depth
                       + self._params.sram_gen_pipeline_depth
                       + self._params.sram_gen_output_pipeline_depth
                       + self._params.glb_switch_pipeline_depth
                       + 1):
            self.rdrq_bank_sel_d.append(
                self.var(f"rdrq_bank_sel_d{i+1}", self._params.bank_sel_addr_width))
            self.rdrq_bank_sel_d_nostall.append(
                self.var(f"rdrq_bank_sel_d{i+1}_nostall", self._params.bank_sel_addr_width))

        self.wr_bank_sel = self.var(
            "wr_bank_sel", self._params.bank_sel_addr_width)

        # localparam
        self.packet_addr_tile_sel_msb = _params.bank_addr_width + \
            _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1
        self.packet_addr_tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width
        self.packet_addr_bank_sel_msb = _params.bank_addr_width + \
            _params.bank_sel_addr_width - 1
        self.packet_addr_bank_sel_lsb = _params.bank_addr_width

        # Add always statements
        # wr packet
        self.add_always(self.wr_proc_pipeline)
        self.add_always(self.wr_data_pipeline)
        self.add_always(self.wr_sw2bank_logic)
        self.add_always(self.wr_sw2bank_filtered_logic)
        self.add_always(self.wr_sw2bankarr_logic)
        self.add_always(self.wr_sw2sr_logic)

        # rdrq packet
        self.add_always(self.rdrq_proc_pcfg_pipeline)
        self.add_always(self.rdrq_data_pipeline)
        self.add_always(self.rdrq_sel_logic)
        self.add_always(self.rdrq_switch_logic)
        self.add_always(self.rdrq_sw2bank_logic)
        self.add_always(self.rdrq_sw2sr_logic)
        self.add_always(self.rdrq_sw2pcfgr_logic)

        # rdrq_sel pipeline
        for in_, out_ in zip([self.rdrq_sel] + self.rdrq_sel_d[:-1], self.rdrq_sel_d):
            self.add_always(self.rdrq_pipeline, in_=in_, out_=out_,
                            rst=self.packet_src_e.none)
        for in_, out_ in zip([self.rdrq_sel] + self.rdrq_sel_d_nostall[:-1], self.rdrq_sel_d_nostall):
            self.add_always(self.rdrq_pipeline_nostall, in_=in_,
                            out_=out_, rst=self.packet_src_e.none)
        # rdrq_bank_sel pipeline
        for in_, out_ in zip([self.rdrq_bank_sel] + self.rdrq_bank_sel_d[:-1], self.rdrq_bank_sel_d):
            self.add_always(self.rdrq_pipeline, in_=in_, out_=out_, rst=0)
        for in_, out_ in zip([self.rdrq_bank_sel] + self.rdrq_bank_sel_d_nostall[:-1], self.rdrq_bank_sel_d_nostall):
            self.add_always(self.rdrq_pipeline_nostall,
                            in_=in_, out_=out_, rst=0)

        # rdrs packet
        self.add_always(self.rdrs_proc_pcfg_pipeline)
        self.add_always(self.rdrs_data_pipeline)
        self.add_always(self.rdrs_sr2sw_pipieline)
        self.add_always(self.rdrs_sw2dma_logic)
        self.add_always(self.rdrs_sw2sr_logic)
        self.add_always(self.rdrs_sw2pr_logic)
        self.add_always(self.rdrs_pcfgr2sw_pipeline)
        self.add_always(self.rdrs_sw2pcfgdma_logic)
        self.add_always(self.rdrs_sw2pcfgr_logic)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def wr_proc_pipeline(self):
        if self.reset:
            self.wr_packet_pr2sw_d = 0
        else:
            self.wr_packet_pr2sw_d = self.wr_packet_pr2sw

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def wr_data_pipeline(self):
        if self.reset:
            self.wr_packet_dma2sw_d = 0
            self.wr_packet_sr2sw_d = 0
        elif self.clk_en:
            self.wr_packet_dma2sw_d = self.wr_packet_dma2sw
            self.wr_packet_sr2sw_d = self.wr_packet_sr2sw

    @always_comb
    def wr_sw2bank_logic(self):
        if self.wr_packet_pr2sw_d['wr_en']:
            self.wr_packet_sw2bank_muxed = self.wr_packet_pr2sw_d
        elif self.cfg_st_dma_ctrl_mode != 0:
            self.wr_packet_sw2bank_muxed = self.wr_packet_dma2sw_d
        else:
            self.wr_packet_sw2bank_muxed = self.wr_packet_sr2sw_d

    @always_comb
    def wr_sw2bank_filtered_logic(self):
        if self.wr_packet_sw2bank_muxed['wr_addr'][self.packet_addr_tile_sel_msb,
                                                   self.packet_addr_tile_sel_lsb] == self.glb_tile_id:
            self.wr_packet_sw2bank_filtered = self.wr_packet_sw2bank_muxed
        else:
            self.wr_packet_sw2bank_filtered = 0

        self.wr_bank_sel = self.wr_packet_sw2bank_filtered['wr_addr'][
            self.packet_addr_bank_sel_msb, self.packet_addr_bank_sel_lsb]

    @always_comb
    def wr_sw2bankarr_logic(self):
        for i in range(self._params.banks_per_tile):
            if self.wr_bank_sel == i:
                self.wr_packet_sw2bankarr[i] = self.wr_packet_sw2bank_filtered
            else:
                self.wr_packet_sw2bankarr[i] = 0

    @always_comb
    def wr_sw2sr_logic(self):
        if self.cfg_st_dma_ctrl_mode != 0:
            self.wr_packet_sw2sr = self.wr_packet_dma2sw
        else:
            self.wr_packet_sw2sr = self.wr_packet_sr2sw

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_proc_pcfg_pipeline(self):
        if self.reset:
            self.rdrq_packet_pr2sw_d = 0
            self.rdrq_packet_pcfgr2sw_d = 0
            self.rdrq_packet_pcfgdma2sw_d = 0
        else:
            self.rdrq_packet_pr2sw_d = self.rdrq_packet_pr2sw
            self.rdrq_packet_pcfgr2sw_d = self.rdrq_packet_pcfgr2sw
            self.rdrq_packet_pcfgdma2sw_d = self.rdrq_packet_pcfgdma2sw

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_data_pipeline(self):
        if self.reset:
            self.rdrq_packet_dma2sw_d = 0
            self.rdrq_packet_sr2sw_d = 0
        elif self.clk_en:
            self.rdrq_packet_dma2sw_d = self.rdrq_packet_dma2sw
            self.rdrq_packet_sr2sw_d = self.rdrq_packet_sr2sw

    @always_comb
    def rdrq_sel_logic(self):
        if ((self.rdrq_packet_pr2sw_d['rd_en'] == 1)
            & (self.rdrq_packet_pr2sw_d['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
               == self.glb_tile_id)):
            self.rdrq_sel = self.packet_src_e.proc
        elif ((self.cfg_pcfg_dma_ctrl_mode == 1)
              & (self.rdrq_packet_pcfgdma2sw_d['rd_en'] == 1)
              & (self.rdrq_packet_pcfgdma2sw_d['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                 == self.glb_tile_id)):
            self.rdrq_sel = self.packet_src_e.pcfg_dma
        elif ((self.cfg_pcfg_dma_ctrl_mode == 0)
              & (self.rdrq_packet_pcfgr2sw_d['rd_en'] == 1)
              & (self.rdrq_packet_pcfgr2sw_d['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                 == self.glb_tile_id)):
            self.rdrq_sel = self.packet_src_e.pcfg_rtr
        elif ((self.cfg_ld_dma_ctrl_mode != 0)
              & (self.rdrq_packet_dma2sw_d['rd_en'] == 1)
              & (self.rdrq_packet_dma2sw_d['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                 == self.glb_tile_id)):
            self.rdrq_sel = self.packet_src_e.strm_dma
        elif ((self.cfg_ld_dma_ctrl_mode == 0)
              & (self.rdrq_packet_sr2sw_d['rd_en'] == 1)
              & (self.rdrq_packet_sr2sw_d['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                 == self.glb_tile_id)):
            self.rdrq_sel = self.packet_src_e.strm_rtr
        else:
            self.rdrq_sel = self.packet_src_e.none

    @always_comb
    def rdrq_switch_logic(self):
        if self.rdrq_sel == self.packet_src_e.proc:
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_pr2sw_d
        elif self.rdrq_sel == self.packet_src_e.pcfg_dma:
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_pcfgdma2sw_d
        elif self.rdrq_sel == self.packet_src_e.pcfg_rtr:
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_pcfgr2sw_d
        elif self.rdrq_sel == self.packet_src_e.strm_dma:
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_dma2sw_d
        elif self.rdrq_sel == self.packet_src_e.strm_rtr:
            self.rdrq_packet_sw2bank_muxed = self.rdrq_packet_sr2sw_d
        else:
            self.rdrq_packet_sw2bank_muxed = 0
        self.rdrq_bank_sel = self.rdrq_packet_sw2bank_muxed['rd_addr'][
            self.packet_addr_bank_sel_msb, self.packet_addr_bank_sel_lsb]

    @always_comb
    def rdrq_sw2bank_logic(self):
        for i in range(self._params.banks_per_tile):
            if self.rdrq_bank_sel == i:
                self.rdrq_packet_sw2bankarr[i] = self.rdrq_packet_sw2bank_muxed
            else:
                self.rdrq_packet_sw2bankarr[i] = 0

    @always_comb
    def rdrq_sw2sr_logic(self):
        if self.cfg_ld_dma_ctrl_mode != 0:
            self.rdrq_packet_sw2sr = self.rdrq_packet_dma2sw
        else:
            self.rdrq_packet_sw2sr = self.rdrq_packet_sr2sw

    @always_comb
    def rdrq_sw2pcfgr_logic(self):
        if self.cfg_pcfg_dma_ctrl_mode != 0:
            self.rdrq_packet_sw2pcfgr = self.rdrq_packet_pcfgdma2sw
        else:
            self.rdrq_packet_sw2pcfgr = self.rdrq_packet_pcfgr2sw

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrs_proc_pcfg_pipeline(self):
        if self.reset:
            for i in range(self._params.banks_per_tile):
                self.rdrs_packet_bankarr2sw_pr_d[i] = 0
                self.rdrs_packet_bankarr2sw_pcfgr_d[i] = 0
        else:
            for i in range(self._params.banks_per_tile):
                self.rdrs_packet_bankarr2sw_pr_d[i] = self.rdrs_packet_bankarr2sw[i]
                self.rdrs_packet_bankarr2sw_pcfgr_d[i] = self.rdrs_packet_bankarr2sw[i]

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrs_data_pipeline(self):
        if self.reset:
            for i in range(self._params.banks_per_tile):
                self.rdrs_packet_bankarr2sw_sr_d[i] = 0
        elif self.clk_en:
            for i in range(self._params.banks_per_tile):
                self.rdrs_packet_bankarr2sw_sr_d[i] = self.rdrs_packet_bankarr2sw[i]

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_pipeline_nostall(self, in_, out_, rst):
        if self.reset:
            out_ = rst
        else:
            out_ = in_

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_pipeline(self, in_, out_, rst):
        if self.reset:
            out_ = rst
        elif self.clk_en:
            out_ = in_

    # rdrs strm
    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrs_sr2sw_pipieline(self):
        if self.reset:
            self.rdrs_packet_sr2sw_d = 0
        elif self.clk_en:
            self.rdrs_packet_sr2sw_d = self.rdrs_packet_sr2sw

    @always_comb
    def rdrs_sw2dma_logic(self):
        if self.cfg_ld_dma_ctrl_mode != 0:
            if (~self.cfg_tile_connected_next) & (~self.cfg_tile_connected_prev):
                self.rdrs_packet_sw2dma = self.rdrs_packet_bankarr2sw_sr_d[self.rdrq_bank_sel_d[-1]]
            else:
                self.rdrs_packet_sw2dma = self.rdrs_packet_sr2sw_d
        else:
            self.rdrs_packet_sw2dma = 0

    @always_comb
    def rdrs_sw2sr_logic(self):
        if (self.rdrq_sel_d[-1] == self.packet_src_e.strm_rtr) | (self.rdrq_sel_d[-1] == self.packet_src_e.strm_dma):
            if (self.cfg_ld_dma_ctrl_mode != 0) & (~self.cfg_tile_connected_next) & (~self.cfg_tile_connected_prev):
                self.rdrs_packet_sw2sr = 0
            else:
                self.rdrs_packet_sw2sr = self.rdrs_packet_bankarr2sw_sr_d[self.rdrq_bank_sel_d[-1]]
        else:
            if self.cfg_ld_dma_ctrl_mode != 0:
                self.rdrs_packet_sw2sr = 0
            else:
                self.rdrs_packet_sw2sr = self.rdrs_packet_sr2sw

    # rdrs proc
    @always_comb
    def rdrs_sw2pr_logic(self):
        if self.rdrq_sel_d_nostall[-1] == self.packet_src_e.proc:
            self.rdrs_packet_sw2pr = self.rdrs_packet_bankarr2sw_pr_d[self.rdrq_bank_sel_d_nostall[-1]]
        else:
            self.rdrs_packet_sw2pr = 0

    # rdrs pcfg
    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrs_pcfgr2sw_pipeline(self):
        if self.reset:
            self.rdrs_packet_pcfgr2sw_d = 0
        else:
            self.rdrs_packet_pcfgr2sw_d = self.rdrs_packet_pcfgr2sw

    @always_comb
    def rdrs_sw2pcfgdma_logic(self):
        if self.cfg_pcfg_dma_ctrl_mode != 0:
            self.rdrs_packet_sw2pcfgdma = self.rdrs_packet_pcfgr2sw_d
        else:
            self.rdrs_packet_sw2pcfgdma = 0

    @always_comb
    def rdrs_sw2pcfgr_logic(self):
        if ((self.rdrq_sel_d_nostall[-1] == self.packet_src_e.pcfg_rtr)
                | (self.rdrq_sel_d_nostall[-1] == self.packet_src_e.pcfg_dma)):
            self.rdrs_packet_sw2pcfgr = self.rdrs_packet_bankarr2sw_pcfgr_d[
                self.rdrq_bank_sel_d_nostall[-1]]
        else:
            if self.cfg_pcfg_dma_ctrl_mode != 0:
                self.rdrs_packet_sw2pcfgr = 0
            else:
                self.rdrs_packet_sw2pcfgr = self.rdrs_packet_pcfgr2sw
