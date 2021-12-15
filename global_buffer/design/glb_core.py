from kratos import Generator, const
from global_buffer.design.glb_core_router import GlbCoreRouter
from global_buffer.design.glb_core_proc_router import GlbCoreProcRouter
from global_buffer.design.glb_core_strm_mux import GlbCoreStrmMux
from global_buffer.design.glb_core_switch import GlbCoreSwitch
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
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
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.proc_wr_packet_w2e_wsti = self.input("proc_wr_packet_w2e_wsti", self.header.wr_packet_t)
        self.proc_wr_packet_w2e_esto = self.output("proc_wr_packet_w2e_esto", self.header.wr_packet_t)

        self.proc_rdrq_packet_w2e_wsti = self.input("proc_rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
        self.proc_rdrq_packet_w2e_esto = self.output("proc_rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

        self.proc_rdrs_packet_w2e_wsti = self.input("proc_rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
        self.proc_rdrs_packet_e2w_wsto = self.output("proc_rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)
        self.proc_rdrs_packet_e2w_esti = self.input("proc_rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
        self.proc_rdrs_packet_w2e_esto = self.output("proc_rdrs_packet_w2e_esto", self.header.rdrs_packet_t)

        self.strm_wr_packet_w2e_wsti = self.input("strm_wr_packet_w2e_wsti", self.header.wr_packet_t)
        self.strm_wr_packet_e2w_wsto = self.output("strm_wr_packet_e2w_wsto", self.header.wr_packet_t)
        self.strm_wr_packet_e2w_esti = self.input("strm_wr_packet_e2w_esti", self.header.wr_packet_t)
        self.strm_wr_packet_w2e_esto = self.output("strm_wr_packet_w2e_esto", self.header.wr_packet_t)

        self.strm_rdrq_packet_w2e_wsti = self.input("strm_rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_e2w_wsto = self.output("strm_rdrq_packet_e2w_wsto", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_e2w_esti = self.input("strm_rdrq_packet_e2w_esti", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_w2e_esto = self.output("strm_rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

        self.strm_rdrs_packet_w2e_wsti = self.input("strm_rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_e2w_wsto = self.output("strm_rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_e2w_esti = self.input("strm_rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_w2e_esto = self.output("strm_rdrs_packet_w2e_esto", self.header.rdrs_packet_t)

        self.pcfg_rdrq_packet_w2e_wsti = self.input("pcfg_rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_e2w_wsto = self.output("pcfg_rdrq_packet_e2w_wsto", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_e2w_esti = self.input("pcfg_rdrq_packet_e2w_esti", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_w2e_esto = self.output("pcfg_rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

        self.pcfg_rdrs_packet_w2e_wsti = self.input("pcfg_rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_e2w_wsto = self.output("pcfg_rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_e2w_esti = self.input("pcfg_rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_w2e_esto = self.output("pcfg_rdrs_packet_w2e_esto", self.header.rdrs_packet_t)

        self.strm_data_f2g = self.input("strm_data_f2g", self._params.cgra_data_width,
                                        size=self._params.cgra_per_glb, packed=True)
        self.strm_data_valid_f2g = self.input("strm_data_valid_f2g", 1, size=self._params.cgra_per_glb, packed=True)
        self.strm_data_g2f = self.output("strm_data_g2f", self._params.cgra_data_width,
                                         size=self._params.cgra_per_glb, packed=True)
        self.strm_data_valid_g2f = self.output("strm_data_valid_g2f", 1, size=self._params.cgra_per_glb, packed=True)

        # configuration registers
        self.cfg_data_network_connected_prev = self.input("cfg_data_network_connected_prev", 1)
        self.cfg_pcfg_network_connected_prev = self.input("cfg_pcfg_network_connected_prev", 1)
        self.cfg_data_network = self.input("cfg_data_network", self.header.cfg_data_network_t)
        self.cfg_pcfg_network = self.input("cfg_pcfg_network", self.header.cfg_pcfg_network_t)

        # st dma
        self.cfg_st_dma_ctrl = self.input("cfg_st_dma_ctrl", self.header.cfg_dma_ctrl_t)
        self.cfg_st_dma_header = self.input("cfg_st_dma_header", self.header.cfg_dma_header_t,
                                            size=self._params.queue_depth)
        # ld dma
        self.cfg_ld_dma_ctrl = self.input("cfg_ld_dma_ctrl", self.header.cfg_dma_ctrl_t)
        self.cfg_ld_dma_header = self.input("cfg_ld_dma_header", self.header.cfg_dma_header_t,
                                            size=self._params.queue_depth)
        # pcfg dma
        self.cfg_pcfg_dma_ctrl = self.input("cfg_pcfg_dma_ctrl", self.header.cfg_pcfg_dma_ctrl_t)
        self.cfg_pcfg_dma_header = self.input("cfg_pcfg_dma_header", self.header.cfg_pcfg_dma_header_t)

        self.cgra_cfg_pcfg = self.output("cgra_cfg_pcfg", self.header.cgra_cfg_t)

        self.ld_dma_start_pulse = self.input("ld_dma_start_pulse", 1)
        self.ld_dma_done_pulse = self.output("ld_dma_done_pulse", 1)
        self.st_dma_start_pulse = self.input("st_dma_start_pulse", 1)
        self.st_dma_done_pulse = self.output("st_dma_done_pulse", 1)
        self.pcfg_start_pulse = self.input("pcfg_start_pulse", 1)
        self.pcfg_done_pulse = self.output("pcfg_done_pulse", 1)

        # bank
        self.wr_packet_sw2bankarr = self.output(
            "wr_packet_sw2bankarr", self.header.wr_packet_t, size=self._params.banks_per_tile)
        self.rdrq_packet_sw2bankarr = self.output(
            "rdrq_packet_sw2bankarr", self.header.rdrq_packet_t, size=self._params.banks_per_tile)
        self.rdrs_packet_bankarr2sw = self.input(
            "rdrs_packet_bankarr2sw", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        self.strm_data_g2f_dma2mux = self.var("strm_data_g2f_dma2mux", self._params.cgra_data_width)
        self.strm_data_valid_g2f_dma2mux = self.var("strm_data_valid_g2f_dma2mux", 1)
        self.strm_data_f2g_mux2dma = self.var("strm_data_f2g_mux2dma", self._params.cgra_data_width)
        self.strm_data_valid_f2g_mux2dma = self.var("strm_data_valid_f2g_mux2dma", 1)

        self.proc_wr_packet_r2sw = self.var("proc_wr_packet_r2sw", self.header.wr_packet_t)
        self.strm_wr_packet_r2sw = self.var("strm_wr_packet_sr2sw", self.header.wr_packet_t)
        self.strm_wr_packet_sw2r = self.var("strm_wr_packet_sw2r", self.header.wr_packet_t)
        self.strm_wr_packet_dma2sw = self.var("strm_wr_packet_dma2sw", self.header.wr_packet_t)

        self.proc_rdrq_packet_r2sw = self.var("proc_rdrq_packet_r2sw", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_r2sw = self.var("strm_rdrq_packet_r2sw", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_sw2r = self.var("strm_rdrq_packet_sw2r", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_dma2sw = self.var("strm_rdrq_packet_dma2sw", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_dma2sw = self.var("pcfg_rdrq_packet_dma2sw", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_r2sw = self.var("pcfg_rdrq_packet_r2sw", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_sw2r = self.var("pcfg_rdrq_packet_sw2r", self.header.rdrq_packet_t)

        self.proc_rdrs_packet_sw2r = self.var("proc_rdrs_packet_sw2r", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_r2sw = self.var("strm_rdrs_packet_r2sw", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_sw2r = self.var("strm_rdrs_packet_sw2r", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_sw2dma = self.var("strm_rdrs_packet_sw2dma", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_r2sw = self.var("pcfg_rdrs_packet_r2sw", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_sw2r = self.var("pcfg_rdrs_packet_sw2r", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_sw2dma = self.var("pcfg_rdrs_packet_sw2dma", self.header.rdrs_packet_t)

        self.add_child("glb_core_store_dma",
                       GlbCoreStoreDma(_params=self._params),
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       data_f2g=self.strm_data_f2g_mux2dma,
                       data_valid_f2g=self.strm_data_valid_f2g_mux2dma,
                       wr_packet=self.strm_wr_packet_dma2sw,
                       # TODO: How to make this automatic
                       cfg_st_dma_num_repeat=self.cfg_st_dma_ctrl['num_repeat'],
                       cfg_st_dma_ctrl_use_valid=self.cfg_st_dma_ctrl['use_valid'],
                       cfg_st_dma_ctrl_mode=self.cfg_st_dma_ctrl['mode'],
                       cfg_data_network_latency=self.cfg_data_network['latency'],
                       cfg_st_dma_header=self.cfg_st_dma_header,
                       st_dma_start_pulse=self.st_dma_start_pulse,
                       st_dma_done_pulse=self.st_dma_done_pulse)

        self.add_child("glb_core_load_dma",
                       GlbCoreLoadDma(_params=self._params),
                       clk=self.clk,
                       clk_en=self.clk_en,
                       glb_tile_id=self.glb_tile_id,
                       reset=self.reset,
                       data_g2f=self.strm_data_g2f_dma2mux,
                       data_valid_g2f=self.strm_data_valid_g2f_dma2mux,
                       rdrq_packet=self.strm_rdrq_packet_dma2sw,
                       rdrs_packet=self.strm_rdrs_packet_sw2dma,
                       # TODO: How to make this automatic
                       cfg_ld_dma_num_repeat=self.cfg_ld_dma_ctrl['num_repeat'],
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
                       glb_tile_id=self.glb_tile_id,
                       cgra_cfg_pcfg=self.cgra_cfg_pcfg,
                       rdrq_packet=self.pcfg_rdrq_packet_dma2sw,
                       rdrs_packet=self.pcfg_rdrs_packet_sw2dma,
                       # TODO: How to make this automatic
                       cfg_pcfg_dma_ctrl_mode=self.cfg_pcfg_dma_ctrl['mode'],
                       cfg_pcfg_network_latency=self.cfg_pcfg_network['latency'],
                       cfg_pcfg_dma_header=self.cfg_pcfg_dma_header,
                       pcfg_start_pulse=self.pcfg_start_pulse,
                       pcfg_done_pulse=self.pcfg_done_pulse)

        self.add_child("glb_core_strm_mux",
                       GlbCoreStrmMux(_params=self._params),
                       data_g2f_dma=self.strm_data_g2f_dma2mux,
                       data_valid_g2f_dma=self.strm_data_valid_g2f_dma2mux,
                       data_g2f=self.strm_data_g2f,
                       data_valid_g2f=self.strm_data_valid_g2f,
                       data_f2g_dma=self.strm_data_f2g_mux2dma,
                       data_valid_f2g_dma=self.strm_data_valid_f2g_mux2dma,
                       data_f2g=self.strm_data_f2g,
                       data_valid_f2g=self.strm_data_valid_f2g,
                       cfg_data_network_g2f_mux=self.cfg_ld_dma_ctrl['data_mux'],
                       cfg_data_network_f2g_mux=self.cfg_st_dma_ctrl['data_mux'])

        self.glb_core_switch = GlbCoreSwitch(_params=self._params)
        self.add_child("glb_core_switch",
                       self.glb_core_switch,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       wr_packet_pr2sw=self.proc_wr_packet_r2sw,
                       wr_packet_dma2sw=self.strm_wr_packet_dma2sw,
                       wr_packet_sw2bankarr=self.wr_packet_sw2bankarr,
                       rdrq_packet_pr2sw=self.proc_rdrq_packet_r2sw,
                       rdrq_packet_dma2sw=self.strm_rdrq_packet_dma2sw,
                       rdrq_packet_pcfgdma2sw=self.pcfg_rdrq_packet_dma2sw,
                       rdrq_packet_sw2bankarr=self.rdrq_packet_sw2bankarr,
                       rdrs_packet_sw2pr=self.proc_rdrs_packet_sw2r,
                       rdrs_packet_sw2dma=self.strm_rdrs_packet_sw2dma,
                       rdrs_packet_sw2pcfgdma=self.pcfg_rdrs_packet_sw2dma,
                       rdrs_packet_bankarr2sw=self.rdrs_packet_bankarr2sw,
                       # cfg
                       cfg_st_dma_ctrl_mode=self.cfg_st_dma_ctrl['mode'],
                       cfg_ld_dma_ctrl_mode=self.cfg_ld_dma_ctrl['mode'],
                       cfg_pcfg_dma_ctrl_mode=self.cfg_pcfg_dma_ctrl['mode'],
                       cfg_tile_connected_prev=self.cfg_data_network_connected_prev,
                       cfg_tile_connected_next=self.cfg_data_network['tile_connected'],
                       cfg_pcfg_tile_connected_prev=self.cfg_pcfg_network_connected_prev,
                       cfg_pcfg_tile_connected_next=self.cfg_pcfg_network['tile_connected'],
                       # strm
                       wr_packet_sr2sw=self.strm_wr_packet_r2sw,
                       wr_packet_sw2sr=self.strm_wr_packet_sw2r,
                       rdrq_packet_sr2sw=self.strm_rdrq_packet_r2sw,
                       rdrq_packet_sw2sr=self.strm_rdrq_packet_sw2r,
                       rdrs_packet_sr2sw=self.strm_rdrs_packet_r2sw,
                       rdrs_packet_sw2sr=self.strm_rdrs_packet_sw2r,
                       # pcfg
                       rdrq_packet_pcfgr2sw=self.pcfg_rdrq_packet_r2sw,
                       rdrq_packet_sw2pcfgr=self.pcfg_rdrq_packet_sw2r,
                       rdrs_packet_pcfgr2sw=self.pcfg_rdrs_packet_r2sw,
                       rdrs_packet_sw2pcfgr=self.pcfg_rdrs_packet_sw2r)

        self.add_child("glb_core_proc_router",
                       GlbCoreProcRouter(_params=self._params),
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       wr_packet_w2e_wsti=self.proc_wr_packet_w2e_wsti,
                       wr_packet_w2e_esto=self.proc_wr_packet_w2e_esto,
                       rdrq_packet_w2e_wsti=self.proc_rdrq_packet_w2e_wsti,
                       rdrq_packet_w2e_esto=self.proc_rdrq_packet_w2e_esto,
                       rdrs_packet_w2e_wsti=self.proc_rdrs_packet_w2e_wsti,
                       rdrs_packet_e2w_wsto=self.proc_rdrs_packet_e2w_wsto,
                       rdrs_packet_e2w_esti=self.proc_rdrs_packet_e2w_esti,
                       rdrs_packet_w2e_esto=self.proc_rdrs_packet_w2e_esto,
                       wr_packet_pr2sw=self.proc_wr_packet_r2sw,
                       rdrq_packet_pr2sw=self.proc_rdrq_packet_r2sw,
                       rdrs_packet_sw2pr=self.proc_rdrs_packet_sw2r)

        self.add_child("glb_core_strm_router",
                       GlbCoreRouter(_params=self._params, wr_channel=True, rd_channel=True),
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       wr_packet_w2e_wsti=self.strm_wr_packet_w2e_wsti,
                       wr_packet_e2w_wsto=self.strm_wr_packet_e2w_wsto,
                       wr_packet_e2w_esti=self.strm_wr_packet_e2w_esti,
                       wr_packet_w2e_esto=self.strm_wr_packet_w2e_esto,
                       rdrq_packet_w2e_wsti=self.strm_rdrq_packet_w2e_wsti,
                       rdrq_packet_e2w_wsto=self.strm_rdrq_packet_e2w_wsto,
                       rdrq_packet_e2w_esti=self.strm_rdrq_packet_e2w_esti,
                       rdrq_packet_w2e_esto=self.strm_rdrq_packet_w2e_esto,
                       rdrs_packet_w2e_wsti=self.strm_rdrs_packet_w2e_wsti,
                       rdrs_packet_e2w_wsto=self.strm_rdrs_packet_e2w_wsto,
                       rdrs_packet_e2w_esti=self.strm_rdrs_packet_e2w_esti,
                       rdrs_packet_w2e_esto=self.strm_rdrs_packet_w2e_esto,
                       wr_packet_r2sw=self.strm_wr_packet_r2sw,
                       wr_packet_sw2r=self.strm_wr_packet_sw2r,
                       rdrq_packet_r2sw=self.strm_rdrq_packet_r2sw,
                       rdrq_packet_sw2r=self.strm_rdrq_packet_sw2r,
                       rdrs_packet_r2sw=self.strm_rdrs_packet_r2sw,
                       rdrs_packet_sw2r=self.strm_rdrs_packet_sw2r,
                       cfg_tile_connected_prev=self.cfg_data_network_connected_prev,
                       cfg_tile_connected_next=self.cfg_data_network['tile_connected'])

        self.add_child("glb_core_pcfg_router",
                       GlbCoreRouter(_params=self._params, wr_channel=False, rd_channel=True),
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       rdrq_packet_w2e_wsti=self.pcfg_rdrq_packet_w2e_wsti,
                       rdrq_packet_e2w_wsto=self.pcfg_rdrq_packet_e2w_wsto,
                       rdrq_packet_e2w_esti=self.pcfg_rdrq_packet_e2w_esti,
                       rdrq_packet_w2e_esto=self.pcfg_rdrq_packet_w2e_esto,
                       rdrs_packet_w2e_wsti=self.pcfg_rdrs_packet_w2e_wsti,
                       rdrs_packet_e2w_wsto=self.pcfg_rdrs_packet_e2w_wsto,
                       rdrs_packet_e2w_esti=self.pcfg_rdrs_packet_e2w_esti,
                       rdrs_packet_w2e_esto=self.pcfg_rdrs_packet_w2e_esto,
                       rdrq_packet_sw2r=self.pcfg_rdrq_packet_sw2r,
                       rdrq_packet_r2sw=self.pcfg_rdrq_packet_r2sw,
                       rdrs_packet_r2sw=self.pcfg_rdrs_packet_r2sw,
                       rdrs_packet_sw2r=self.pcfg_rdrs_packet_sw2r,
                       cfg_tile_connected_prev=self.cfg_pcfg_network_connected_prev,
                       cfg_tile_connected_next=self.cfg_pcfg_network['tile_connected'])
