from kratos import Generator
from global_buffer.design.glb_core_pcfg_router import GlbCorePcfgRouter
from global_buffer.design.glb_core_proc_router import GlbCoreProcRouter
from global_buffer.design.glb_core_sram_cfg_ctrl import GlbCoreSramCfgCtrl
from global_buffer.design.glb_core_strm_mux import GlbCoreStrmMux
from global_buffer.design.glb_core_strm_router import GlbCoreStrmRouter
from global_buffer.design.glb_core_switch import GlbCoreSwitch
from global_buffer.design.glb_bank import GlbBank
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_core_store_dma import GlbCoreStoreDma
from global_buffer.design.glb_core_load_dma import GlbCoreLoadDma
from global_buffer.design.glb_core_pcfg_dma import GlbCorePcfgDma


class GlbCore(Generator):
    def __init__(self, _params: GlobalBufferParams):
        # TODO: configuration wiring to children modules should be a pass
        super().__init__("glb_core")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.clk_en = self.input("clk_en", 1)
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input(
            "glb_tile_id", self._params.tile_sel_addr_width)

        self.proc_packet_w2e_wsti = self.input(
            "proc_packet_w2e_wsti", self.header.packet_t)
        self.proc_packet_e2w_wsto = self.output(
            "proc_packet_e2w_wsto", self.header.packet_t)
        self.proc_packet_e2w_esti = self.input(
            "proc_packet_e2w_esti", self.header.packet_t)
        self.proc_packet_w2e_esto = self.output(
            "proc_packet_w2e_esto", self.header.packet_t)

        self.strm_packet_w2e_wsti = self.input(
            "strm_packet_w2e_wsti", self.header.packet_t)
        self.strm_packet_e2w_wsto = self.output(
            "strm_packet_e2w_wsto", self.header.packet_t)
        self.strm_packet_e2w_esti = self.input(
            "strm_packet_e2w_esti", self.header.packet_t)
        self.strm_packet_w2e_esto = self.output(
            "strm_packet_w2e_esto", self.header.packet_t)

        self.pcfg_packet_w2e_wsti = self.input(
            "pcfg_packet_w2e_wsti", self.header.rd_packet_t)
        self.pcfg_packet_e2w_wsto = self.output(
            "pcfg_packet_e2w_wsto", self.header.rd_packet_t)
        self.pcfg_packet_e2w_esti = self.input(
            "pcfg_packet_e2w_esti", self.header.rd_packet_t)
        self.pcfg_packet_w2e_esto = self.output(
            "pcfg_packet_w2e_esto", self.header.rd_packet_t)

        self.strm_data_f2g = self.input(
            "strm_data_f2g", self._params.cgra_data_width, size=self._params.cgra_per_glb, packed=True)
        self.strm_data_valid_f2g = self.input(
            "strm_data_valid_f2g", 1, size=self._params.cgra_per_glb, packed=True)
        self.strm_data_g2f = self.output(
            "strm_data_g2f", self._params.cgra_data_width, size=self._params.cgra_per_glb, packed=True)
        self.strm_data_valid_g2f = self.output(
            "strm_data_valid_g2f", 1, size=self._params.cgra_per_glb, packed=True)

        # config port
        self.sram_cfg_ifc = GlbConfigInterface(
            addr_width=self._params.glb_addr_width, data_width=self._params.axi_data_width)
        self.if_sram_cfg_est_m = self.interface(
            self.sram_cfg_ifc.master, "if_sram_cfg_est_m", is_port=True)
        self.if_sram_cfg_wst_s = self.interface(
            self.sram_cfg_ifc.slave, "if_sram_cfg_wst_s", is_port=True)

        # configuration registers
        self.cfg_data_network_connected_prev = self.input(
            "cfg_data_network_connected_prev", 1)
        self.cfg_pcfg_network_connected_prev = self.input(
            "cfg_pcfg_network_connected_prev", 1)
        self.cfg_data_network = self.input(
            "cfg_data_network", self.header.cfg_data_network_t)
        self.cfg_pcfg_network = self.input(
            "cfg_pcfg_network", self.header.cfg_pcfg_network_t)

        # st dma
        self.cfg_st_dma_ctrl = self.input(
            "cfg_st_dma_ctrl", self.header.cfg_st_dma_ctrl_t)
        self.cfg_st_dma_header = self.input("cfg_st_dma_header", self.header.cfg_st_dma_header_t,
                                            size=self._params.queue_depth)
        self.st_dma_header_clr = self.output(
            "st_dma_header_clr", width=self._params.queue_depth)
        # ld dma
        self.cfg_ld_dma_ctrl = self.input(
            "cfg_ld_dma_ctrl", self.header.cfg_ld_dma_ctrl_t)
        self.cfg_ld_dma_header = self.input("cfg_ld_dma_header", self.header.cfg_ld_dma_header_t,
                                            size=self._params.queue_depth)
        # pcfg dma
        self.cfg_pcfg_dma_ctrl = self.input(
            "cfg_pcfg_dma_ctrl", self.header.cfg_pcfg_dma_ctrl_t)
        self.cfg_pcfg_dma_header = self.input(
            "cfg_pcfg_dma_header", self.header.cfg_pcfg_dma_header_t)

        self.cgra_cfg_pcfg = self.output(
            "cgra_cfg_pcfg", self.header.cgra_cfg_t)

        self.ld_dma_start_pulse = self.input("ld_dma_start_pulse", 1)
        self.ld_dma_done_pulse = self.output("ld_dma_done_pulse", 1)
        self.st_dma_done_pulse = self.output("st_dma_done_pulse", 1)
        self.pcfg_start_pulse = self.input("pcfg_start_pulse", 1)
        self.pcfg_done_pulse = self.output("pcfg_done_pulse", 1)

        self.strm_data_g2f_dma2mux = self.var(
            "strm_data_g2f_dma2mux", self._params.cgra_data_width)
        self.strm_data_valid_g2f_dma2mux = self.var(
            "strm_data_valid_g2f_dma2mux", 1)
        self.strm_data_f2g_mux2dma = self.var(
            "strm_data_f2g_mux2dma", self._params.cgra_data_width)
        self.strm_data_valid_f2g_mux2dma = self.var(
            "strm_data_valid_f2g_mux2dma", 1)

        self.wr_packet_pr2sw = self.var(
            "wr_packet_pr2sw", self.header.wr_packet_t)
        self.wr_packet_sr2sw = self.var(
            "wr_packet_sr2sw", self.header.wr_packet_t)
        self.wr_packet_sw2sr = self.var(
            "wr_packet_sw2sr", self.header.wr_packet_t)
        self.wr_packet_dma2sw = self.var(
            "wr_packet_dma2sw", self.header.wr_packet_t)
        self.wr_packet_sw2bankarr = self.var(
            "wr_packet_sw2bankarr", self.header.wr_packet_t, size=self._params.banks_per_tile)

        self.rdrq_packet_pr2sw = self.var(
            "rdrq_packet_pr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sr2sw = self.var(
            "rdrq_packet_sr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2sr = self.var(
            "rdrq_packet_sw2sr", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2sw = self.var(
            "rdrq_packet_dma2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgdma2sw = self.var(
            "rdrq_packet_pcfgdma2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgr2sw = self.var(
            "rdrq_packet_pcfgr2sw", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2pcfgr = self.var(
            "rdrq_packet_sw2pcfgr", self.header.rdrq_packet_t)
        self.rdrq_packet_sw2bankarr = self.var(
            "rdrq_packet_sw2bankarr", self.header.rdrq_packet_t, size=self._params.banks_per_tile)

        self.rdrs_packet_sw2pr = self.var(
            "rdrs_packet_sw2pr", self.header.rdrs_packet_t)
        self.rdrs_packet_sr2sw = self.var(
            "rdrs_packet_sr2sw", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2sr = self.var(
            "rdrs_packet_sw2sr", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2dma = self.var(
            "rdrs_packet_sw2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_pcfgr2sw = self.var(
            "rdrs_packet_pcfgr2sw", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2pcfgr = self.var(
            "rdrs_packet_sw2pcfgr", self.header.rdrs_packet_t)
        self.rdrs_packet_sw2pcfgdma = self.var(
            "rdrs_packet_sw2pcfgdma", self.header.rdrs_packet_t)
        self.rdrs_packet_bankarr2sw = self.var(
            "rdrs_packet_bankarr2sw", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        self.packet_sr2sw = self.var(
            "packet_sr2sw", self.header.packet_t)
        self.packet_sw2sr = self.var(
            "packet_sw2sr", self.header.packet_t)

        self.rd_packet_pcfgr2sw = self.var(
            "rd_packet_pcfgr2sw", self.header.rd_packet_t)
        self.rd_packet_sw2pcfgr = self.var(
            "rd_packet_sw2pcfgr", self.header.rd_packet_t)

        self.if_sram_cfg_bank2core = []
        for i in range(self._params.banks_per_tile):
            if_sram_cfg_bank2core = self.interface(GlbConfigInterface(addr_width=self._params.bank_addr_width,
                                                                      data_width=self._params.axi_data_width),
                                                   f"if_sram_cfg_bank2core_{i}")
            self.if_sram_cfg_bank2core.append(if_sram_cfg_bank2core)

        self.glb_bank_arr = []
        for i in range(self._params.banks_per_tile):
            glb_bank = GlbBank(self._params)
            self.add_child(f"glb_bank_{i}",
                           glb_bank,
                           clk=self.clk,
                           reset=self.reset,
                           wr_packet=self.wr_packet_sw2bankarr[i],
                           rdrq_packet=self.rdrq_packet_sw2bankarr[i],
                           rdrs_packet=self.rdrs_packet_bankarr2sw[i],
                           if_sram_cfg_s=self.if_sram_cfg_bank2core[i])
            self.glb_bank_arr.append(glb_bank)

        self.glb_core_sram_cfg_ctrl = GlbCoreSramCfgCtrl(self._params)
        self.add_child("glb_core_sram_cfg_ctrl",
                       self.glb_core_sram_cfg_ctrl,
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       if_sram_cfg_est_m=self.if_sram_cfg_est_m,
                       if_sram_cfg_wst_s=self.if_sram_cfg_wst_s)
        for i in range(self._params.banks_per_tile):
            self.wire(self.glb_core_sram_cfg_ctrl.if_sram_cfg_core2bank_m[i],
                      self.if_sram_cfg_bank2core[i])

        self.add_child("glb_core_store_dma",
                       GlbCoreStoreDma(_params=self._params),
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       data_f2g=self.strm_data_f2g_mux2dma,
                       data_valid_f2g=self.strm_data_valid_f2g_mux2dma,
                       wr_packet=self.wr_packet_dma2sw,
                       # TODO: How to make this automatic
                       cfg_st_dma_ctrl_mode=self.cfg_st_dma_ctrl['mode'],
                       cfg_data_network_latency=self.cfg_data_network['latency'],
                       cfg_st_dma_header=self.cfg_st_dma_header,
                       st_dma_header_clr=self.st_dma_header_clr,
                       st_dma_done_pulse=self.st_dma_done_pulse)

        self.add_child("glb_core_load_dma",
                       GlbCoreLoadDma(_params=self._params),
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       data_g2f=self.strm_data_g2f_dma2mux,
                       data_valid_g2f=self.strm_data_valid_g2f_dma2mux,
                       rdrq_packet=self.rdrq_packet_dma2sw,
                       rdrs_packet=self.rdrs_packet_sw2dma,
                       # TODO: How to make this automatic
                       cfg_ld_dma_ctrl_use_valid=self.cfg_ld_dma_ctrl['use_valid'],
                       cfg_ld_dma_ctrl_mode=self.cfg_ld_dma_ctrl['mode'],
                       cfg_data_network_latency=self.cfg_data_network['latency'],
                       cfg_ld_dma_header=self.cfg_ld_dma_header,
                       ld_dma_start_pulse=self.ld_dma_start_pulse,
                       ld_dma_done_pulse=self.ld_dma_done_pulse)

        self.add_child("glb_core_pcfg_dma",
                       GlbCorePcfgDma(_params=self._params),
                       clk=self.clk,
                       reset=self.reset,
                       cgra_cfg_pcfg=self.cgra_cfg_pcfg,
                       rdrq_packet=self.rdrq_packet_pcfgdma2sw,
                       rdrs_packet=self.rdrs_packet_sw2pcfgdma,
                       # TODO: How to make this automatic
                       cfg_pcfg_dma_ctrl_mode=self.cfg_pcfg_dma_ctrl['mode'],
                       cfg_pcfg_network_latency=self.cfg_pcfg_network['latency'],
                       cfg_pcfg_dma_header=self.cfg_pcfg_dma_header,
                       pcfg_start_pulse=self.pcfg_start_pulse,
                       pcfg_done_pulse=self.pcfg_done_pulse)

        self.add_child("glb_core_strm_mux",
                       GlbCoreStrmMux(_params=self._params),
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       data_g2f_dma=self.strm_data_g2f_dma2mux,
                       data_valid_g2f_dma=self.strm_data_valid_g2f_dma2mux,
                       data_g2f=self.strm_data_g2f,
                       data_valid_g2f=self.strm_data_valid_g2f,
                       data_f2g_dma=self.strm_data_f2g_mux2dma,
                       data_valid_f2g_dma=self.strm_data_valid_f2g_mux2dma,
                       data_f2g=self.strm_data_f2g,
                       data_valid_f2g=self.strm_data_valid_f2g,
                       cfg_data_network_g2f_mux=self.cfg_ld_dma_ctrl['g2f_mux'],
                       cfg_data_network_f2g_mux=self.cfg_st_dma_ctrl['f2g_mux'])

        self.glb_core_switch = GlbCoreSwitch(_params=self._params)
        self.add_child("glb_core_switch",
                       self.glb_core_switch,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       wr_packet_pr2sw=self.wr_packet_pr2sw,
                       wr_packet_dma2sw=self.wr_packet_dma2sw,
                       wr_packet_sw2bankarr=self.wr_packet_sw2bankarr,
                       rdrq_packet_pr2sw=self.rdrq_packet_pr2sw,
                       rdrq_packet_dma2sw=self.rdrq_packet_dma2sw,
                       rdrq_packet_pcfgdma2sw=self.rdrq_packet_pcfgdma2sw,
                       rdrq_packet_sw2bankarr=self.rdrq_packet_sw2bankarr,
                       rdrs_packet_sw2pr=self.rdrs_packet_sw2pr,
                       rdrs_packet_sw2dma=self.rdrs_packet_sw2dma,
                       rdrs_packet_sw2pcfgdma=self.rdrs_packet_sw2pcfgdma,
                       rdrs_packet_bankarr2sw=self.rdrs_packet_bankarr2sw,
                       cfg_st_dma_ctrl_mode=self.cfg_st_dma_ctrl['mode'],
                       cfg_ld_dma_ctrl_mode=self.cfg_ld_dma_ctrl['mode'],
                       cfg_pcfg_dma_ctrl_mode=self.cfg_pcfg_dma_ctrl['mode'])
        for port in self.header.wr_packet_ports:
            self.wire(
                self.glb_core_switch.wr_packet_sr2sw[port], self.packet_sr2sw[port])
            self.wire(
                self.glb_core_switch.wr_packet_sw2sr[port], self.packet_sw2sr[port])
        for port in self.header.rdrq_packet_ports:
            self.wire(
                self.glb_core_switch.rdrq_packet_sr2sw[port], self.packet_sr2sw[port])
            self.wire(
                self.glb_core_switch.rdrq_packet_sw2sr[port], self.packet_sw2sr[port])
            self.wire(
                self.glb_core_switch.rdrq_packet_pcfgr2sw[port], self.rd_packet_pcfgr2sw[port])
            self.wire(
                self.glb_core_switch.rdrq_packet_sw2pcfgr[port], self.rd_packet_sw2pcfgr[port])
        for port in self.header.rdrs_packet_ports:
            self.wire(
                self.glb_core_switch.rdrs_packet_sr2sw[port], self.packet_sr2sw[port])
            self.wire(
                self.glb_core_switch.rdrs_packet_sw2sr[port], self.packet_sw2sr[port])
            self.wire(
                self.glb_core_switch.rdrs_packet_pcfgr2sw[port], self.rd_packet_pcfgr2sw[port])
            self.wire(
                self.glb_core_switch.rdrs_packet_sw2pcfgr[port], self.rd_packet_sw2pcfgr[port])

        self.add_child("glb_core_proc_router",
                       GlbCoreProcRouter(_params=self._params),
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       packet_w2e_wsti=self.proc_packet_w2e_wsti,
                       packet_e2w_wsto=self.proc_packet_e2w_wsto,
                       packet_e2w_esti=self.proc_packet_e2w_esti,
                       packet_w2e_esto=self.proc_packet_w2e_esto,
                       wr_packet_pr2sw=self.wr_packet_pr2sw,
                       rdrq_packet_pr2sw=self.rdrq_packet_pr2sw,
                       rdrs_packet_sw2pr=self.rdrs_packet_sw2pr)

        self.add_child("glb_core_strm_router",
                       GlbCoreStrmRouter(_params=self._params),
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       packet_w2e_wsti=self.strm_packet_w2e_wsti,
                       packet_e2w_wsto=self.strm_packet_e2w_wsto,
                       packet_e2w_esti=self.strm_packet_e2w_esti,
                       packet_w2e_esto=self.strm_packet_w2e_esto,
                       packet_sr2sw=self.packet_sr2sw,
                       packet_sw2sr=self.packet_sw2sr,
                       cfg_tile_connected_prev=self.cfg_data_network_connected_prev,
                       cfg_tile_connected_next=self.cfg_data_network['tile_connected'])

        self.add_child("glb_core_pcfg_router",
                       GlbCorePcfgRouter(_params=self._params),
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       rd_packet_w2e_wsti=self.pcfg_packet_w2e_wsti,
                       rd_packet_e2w_wsto=self.pcfg_packet_e2w_wsto,
                       rd_packet_e2w_esti=self.pcfg_packet_e2w_esti,
                       rd_packet_w2e_esto=self.pcfg_packet_w2e_esto,
                       rd_packet_sw2pcfgr=self.rd_packet_sw2pcfgr,
                       rd_packet_pcfgr2sw=self.rd_packet_pcfgr2sw,
                       cfg_tile_connected_prev=self.cfg_pcfg_network_connected_prev,
                       cfg_tile_connected_next=self.cfg_pcfg_network['tile_connected'])
