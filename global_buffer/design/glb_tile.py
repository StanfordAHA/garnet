from kratos import Generator, RawStringStmt, const
from kratos.util import clock
from global_buffer.design.glb_store_dma import GlbStoreDma
from global_buffer.design.glb_load_dma import GlbLoadDma
from global_buffer.design.glb_pcfg_dma import GlbPcfgDma
from global_buffer.design.glb_cfg import GlbCfg
from global_buffer.design.glb_strm_mux import GlbStrmMux
from global_buffer.design.glb_switch import GlbSwitch
from global_buffer.design.glb_router import GlbRouter
from global_buffer.design.glb_proc_router import GlbProcRouter
from global_buffer.design.glb_pcfg_broadcast import GlbPcfgBroadcast
from global_buffer.design.glb_sram_cfg_ctrl import GlbSramCfgCtrl
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_bank import GlbBank
from global_buffer.design.clk_gate import ClkGate


class GlbTile(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_tile")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.proc_w2e_wsti_dict = {}
        for port, size in self.header.packet_ports:
            name = f"proc_{port}_w2e_wsti"
            self.proc_w2e_wsti_dict[port] = self.input(name, size)

        self.proc_w2e_esto_dict = {}
        for port, size in self.header.packet_ports:
            name = f"proc_{port}_w2e_esto"
            self.proc_w2e_esto_dict[port] = self.output(name, size)

        self.proc_e2w_esti_dict = {}
        for port, size in self.header.rdrs_packet_ports:
            name = f"proc_{port}_e2w_esti"
            self.proc_e2w_esti_dict[port] = self.input(name, size)

        self.proc_e2w_wsto_dict = {}
        for port, size in self.header.rdrs_packet_ports:
            name = f"proc_{port}_e2w_wsto"
            self.proc_e2w_wsto_dict[port] = self.output(name, size)

        self.strm_w2e_wsti_dict = {}
        for port, size in self.header.packet_ports:
            name = f"strm_{port}_w2e_wsti"
            self.strm_w2e_wsti_dict[port] = self.input(name, size)

        self.strm_w2e_esto_dict = {}
        for port, size in self.header.packet_ports:
            name = f"strm_{port}_w2e_esto"
            self.strm_w2e_esto_dict[port] = self.output(name, size)

        self.strm_e2w_esti_dict = {}
        for port, size in self.header.packet_ports:
            name = f"strm_{port}_e2w_esti"
            self.strm_e2w_esti_dict[port] = self.input(name, size)

        self.strm_e2w_wsto_dict = {}
        for port, size in self.header.packet_ports:
            name = f"strm_{port}_e2w_wsto"
            self.strm_e2w_wsto_dict[port] = self.output(name, size)

        self.pcfg_w2e_wsti_dict = {}
        for port, size in self.header.rd_packet_ports:
            name = f"pcfg_{port}_w2e_wsti"
            self.pcfg_w2e_wsti_dict[port] = self.input(name, size)

        self.pcfg_w2e_esto_dict = {}
        for port, size in self.header.rd_packet_ports:
            name = f"pcfg_{port}_w2e_esto"
            self.pcfg_w2e_esto_dict[port] = self.output(name, size)

        self.pcfg_e2w_esti_dict = {}
        for port, size in self.header.rd_packet_ports:
            name = f"pcfg_{port}_e2w_esti"
            self.pcfg_e2w_esti_dict[port] = self.input(name, size)

        self.pcfg_e2w_wsto_dict = {}
        for port, size in self.header.rd_packet_ports:
            name = f"pcfg_{port}_e2w_wsto"
            self.pcfg_e2w_wsto_dict[port] = self.output(name, size)

        self.if_cfg_est_m_wr_en = self.output("if_cfg_est_m_wr_en", 1)
        self.if_cfg_est_m_wr_addr = self.output("if_cfg_est_m_wr_addr", self._params.axi_addr_width)
        self.if_cfg_est_m_wr_data = self.output("if_cfg_est_m_wr_data", self._params.axi_data_width)
        self.if_cfg_est_m_rd_en = self.output("if_cfg_est_m_rd_en", 1)
        self.if_cfg_est_m_rd_addr = self.output("if_cfg_est_m_rd_addr", self._params.axi_addr_width)
        self.if_cfg_est_m_rd_data = self.input("if_cfg_est_m_rd_data", self._params.axi_data_width)
        self.if_cfg_est_m_rd_data_valid = self.input("if_cfg_est_m_rd_data_valid", 1)

        self.if_cfg_wst_s_wr_en = self.input("if_cfg_wst_s_wr_en", 1)
        self.if_cfg_wst_s_wr_addr = self.input("if_cfg_wst_s_wr_addr", self._params.axi_addr_width)
        self.if_cfg_wst_s_wr_data = self.input("if_cfg_wst_s_wr_data", self._params.axi_data_width)
        self.if_cfg_wst_s_rd_en = self.input("if_cfg_wst_s_rd_en", 1)
        self.if_cfg_wst_s_rd_addr = self.input("if_cfg_wst_s_rd_addr", self._params.axi_addr_width)
        self.if_cfg_wst_s_rd_data = self.output("if_cfg_wst_s_rd_data", self._params.axi_data_width)
        self.if_cfg_wst_s_rd_data_valid = self.output("if_cfg_wst_s_rd_data_valid", 1)

        self.if_sram_cfg_est_m_wr_en = self.output("if_sram_cfg_est_m_wr_en", 1)
        self.if_sram_cfg_est_m_wr_addr = self.output("if_sram_cfg_est_m_wr_addr", self._params.glb_addr_width)
        self.if_sram_cfg_est_m_wr_data = self.output("if_sram_cfg_est_m_wr_data", self._params.axi_data_width)
        self.if_sram_cfg_est_m_rd_en = self.output("if_sram_cfg_est_m_rd_en", 1)
        self.if_sram_cfg_est_m_rd_addr = self.output("if_sram_cfg_est_m_rd_addr", self._params.glb_addr_width)
        self.if_sram_cfg_est_m_rd_data = self.input("if_sram_cfg_est_m_rd_data", self._params.axi_data_width)
        self.if_sram_cfg_est_m_rd_data_valid = self.input("if_sram_cfg_est_m_rd_data_valid", 1)

        self.if_sram_cfg_wst_s_wr_en = self.input("if_sram_cfg_wst_s_wr_en", 1)
        self.if_sram_cfg_wst_s_wr_addr = self.input("if_sram_cfg_wst_s_wr_addr", self._params.glb_addr_width)
        self.if_sram_cfg_wst_s_wr_data = self.input("if_sram_cfg_wst_s_wr_data", self._params.axi_data_width)
        self.if_sram_cfg_wst_s_rd_en = self.input("if_sram_cfg_wst_s_rd_en", 1)
        self.if_sram_cfg_wst_s_rd_addr = self.input("if_sram_cfg_wst_s_rd_addr", self._params.glb_addr_width)
        self.if_sram_cfg_wst_s_rd_data = self.output("if_sram_cfg_wst_s_rd_data", self._params.axi_data_width)
        self.if_sram_cfg_wst_s_rd_data_valid = self.output("if_sram_cfg_wst_s_rd_data_valid", 1)

        self.cfg_tile_connected_wsti = self.input("cfg_tile_connected_wsti", 1)
        self.cfg_tile_connected_esto = self.output("cfg_tile_connected_esto", 1)
        self.cfg_pcfg_tile_connected_wsti = self.input("cfg_pcfg_tile_connected_wsti", 1)
        self.cfg_pcfg_tile_connected_esto = self.output("cfg_pcfg_tile_connected_esto", 1)

        self.cgra_cfg_jtag_wsti_wr_en = self.input("cgra_cfg_jtag_wsti_wr_en", 1)
        self.cgra_cfg_jtag_wsti_rd_en = self.input("cgra_cfg_jtag_wsti_rd_en", 1)
        self.cgra_cfg_jtag_wsti_addr = self.input("cgra_cfg_jtag_wsti_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_wsti_data = self.input("cgra_cfg_jtag_wsti_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_jtag_esto_wr_en = self.output("cgra_cfg_jtag_esto_wr_en", 1)
        self.cgra_cfg_jtag_esto_rd_en = self.output("cgra_cfg_jtag_esto_rd_en", 1)
        self.cgra_cfg_jtag_esto_addr = self.output("cgra_cfg_jtag_esto_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_esto_data = self.output("cgra_cfg_jtag_esto_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_jtag_wsti_rd_en_bypass = self.input("cgra_cfg_jtag_wsti_rd_en_bypass", 1)
        self.cgra_cfg_jtag_wsti_addr_bypass = self.input(
            "cgra_cfg_jtag_wsti_addr_bypass", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_esto_rd_en_bypass = self.output("cgra_cfg_jtag_esto_rd_en_bypass", 1)
        self.cgra_cfg_jtag_esto_addr_bypass = self.output(
            "cgra_cfg_jtag_esto_addr_bypass", self._params.cgra_cfg_addr_width)

        self.cgra_cfg_pcfg_wsti_wr_en = self.input("cgra_cfg_pcfg_wsti_wr_en", 1)
        self.cgra_cfg_pcfg_wsti_rd_en = self.input("cgra_cfg_pcfg_wsti_rd_en", 1)
        self.cgra_cfg_pcfg_wsti_addr = self.input("cgra_cfg_pcfg_wsti_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_wsti_data = self.input("cgra_cfg_pcfg_wsti_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_pcfg_esto_wr_en = self.output("cgra_cfg_pcfg_esto_wr_en", 1)
        self.cgra_cfg_pcfg_esto_rd_en = self.output("cgra_cfg_pcfg_esto_rd_en", 1)
        self.cgra_cfg_pcfg_esto_addr = self.output("cgra_cfg_pcfg_esto_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_esto_data = self.output("cgra_cfg_pcfg_esto_data", self._params.cgra_cfg_data_width)

        self.strm_data_f2g = self.input("strm_data_f2g", self._params.cgra_data_width,
                                        size=self._params.cgra_per_glb, packed=True)
        self.strm_data_valid_f2g = self.input("strm_data_valid_f2g", 1, size=self._params.cgra_per_glb, packed=True)
        self.strm_data_g2f = self.output("strm_data_g2f", self._params.cgra_data_width,
                                         size=self._params.cgra_per_glb, packed=True)
        self.strm_data_valid_g2f = self.output(
            "strm_data_valid_g2f", 1, size=self._params.cgra_per_glb, packed=True)

        self.cgra_cfg_g2f_cfg_wr_en = self.output(
            "cgra_cfg_g2f_cfg_wr_en", 1, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_rd_en = self.output(
            "cgra_cfg_g2f_cfg_rd_en", 1, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_addr = self.output(
            "cgra_cfg_g2f_cfg_addr", self._params.cgra_cfg_addr_width, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_data = self.output(
            "cgra_cfg_g2f_cfg_data", self._params.cgra_cfg_data_width, size=self._params.cgra_per_glb, packed=True)

        self.strm_g2f_start_pulse = self.input("strm_g2f_start_pulse", 1)
        self.strm_f2g_start_pulse = self.input("strm_f2g_start_pulse", 1)
        self.pcfg_start_pulse = self.input("pcfg_start_pulse", 1)
        self.strm_f2g_interrupt_pulse = self.output("strm_f2g_interrupt_pulse", 1)
        self.strm_g2f_interrupt_pulse = self.output("strm_g2f_interrupt_pulse", 1)
        self.pcfg_g2f_interrupt_pulse = self.output("pcfg_g2f_interrupt_pulse", 1)

        # Interface
        self.interface_wiring()

        # Struct
        self.struct_wiring()

        # Local variables
        # configuration
        self.cfg_tile_connected_prev = self.var("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.var("cfg_tile_connected_next", 1)
        self.cfg_pcfg_tile_connected_prev = self.var("cfg_pcfg_tile_connected_prev", 1)
        self.cfg_pcfg_tile_connected_next = self.var("cfg_pcfg_tile_connected_next", 1)

        # st dma
        self.cfg_st_dma_ctrl = self.var("cfg_st_dma_ctrl", self.header.cfg_dma_ctrl_t)
        self.cfg_st_dma_header = self.var("cfg_st_dma_header", self.header.cfg_dma_header_t,
                                          size=self._params.queue_depth)
        # ld dma
        self.cfg_ld_dma_ctrl = self.var("cfg_ld_dma_ctrl", self.header.cfg_dma_ctrl_t)
        self.cfg_ld_dma_header = self.var("cfg_ld_dma_header", self.header.cfg_dma_header_t,
                                          size=self._params.queue_depth)
        # pcfg dma
        self.cfg_pcfg_dma_ctrl = self.var("cfg_pcfg_dma_ctrl", self.header.cfg_pcfg_dma_ctrl_t)
        self.cfg_pcfg_dma_header = self.var("cfg_pcfg_dma_header", self.header.cfg_pcfg_dma_header_t)

        self.glb_tile_cfg = GlbCfg(_params=self._params)
        self.add_child("glb_cfg",
                       self.glb_tile_cfg,
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id)
        self.wire(self.cfg_tile_connected_next, self.glb_tile_cfg.cfg_data_network['tile_connected'])
        self.wire(self.cfg_tile_connected_prev, self.cfg_tile_connected_wsti)
        self.wire(self.cfg_tile_connected_next, self.cfg_tile_connected_esto)
        self.wire(self.cfg_pcfg_tile_connected_next, self.glb_tile_cfg.cfg_pcfg_network['tile_connected'])
        self.wire(self.cfg_pcfg_tile_connected_prev, self.cfg_pcfg_tile_connected_wsti)
        self.wire(self.cfg_pcfg_tile_connected_next, self.cfg_pcfg_tile_connected_esto)
        self.wire(self.glb_tile_cfg.if_cfg_wst_s, self.if_cfg_wst_s)
        self.wire(self.glb_tile_cfg.if_cfg_est_m, self.if_cfg_est_m)
        self.wire(self.cfg_st_dma_ctrl, self.glb_tile_cfg.cfg_st_dma_ctrl)
        self.wire(self.cfg_st_dma_header, self.glb_tile_cfg.cfg_st_dma_header)
        self.wire(self.cfg_ld_dma_ctrl, self.glb_tile_cfg.cfg_ld_dma_ctrl)
        self.wire(self.cfg_ld_dma_header, self.glb_tile_cfg.cfg_ld_dma_header)
        self.wire(self.cfg_pcfg_dma_ctrl, self.glb_tile_cfg.cfg_pcfg_dma_ctrl)
        self.wire(self.cfg_pcfg_dma_header, self.glb_tile_cfg.cfg_pcfg_dma_header)

        # Instantiate modules
        # Clock gating
        self.gclk = self.var("gclk", 1)
        self.glb_clk_gate = ClkGate()
        self.add_child("glb_clk_gate",
                       self.glb_clk_gate,
                       clk=self.clk,
                       enable=self.clk_en,
                       gclk=self.gclk)

        self.glb_tile_pcfg_switch = GlbPcfgBroadcast(_params=self._params)
        self.add_child("glb_pcfg_switch",
                       self.glb_tile_pcfg_switch,
                       clk=self.gclk,
                       reset=self.reset,
                       cgra_cfg_core2sw=self.cgra_cfg_pcfgdma2mux,
                       cfg_pcfg_dma_mode=self.cfg_pcfg_dma_ctrl['mode'])

        self.add_child("glb_store_dma",
                       GlbStoreDma(_params=self._params),
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
                       cfg_data_network_latency=self.glb_tile_cfg.cfg_data_network['latency'],
                       cfg_st_dma_header=self.cfg_st_dma_header,
                       st_dma_start_pulse=self.strm_f2g_start_pulse,
                       st_dma_done_pulse=self.strm_f2g_interrupt_pulse)

        self.add_child("glb_load_dma",
                       GlbLoadDma(_params=self._params),
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
                       cfg_data_network_latency=self.glb_tile_cfg.cfg_data_network['latency'],
                       cfg_ld_dma_header=self.cfg_ld_dma_header,
                       ld_dma_start_pulse=self.strm_g2f_start_pulse,
                       ld_dma_done_pulse=self.strm_g2f_interrupt_pulse)

        self.add_child("glb_pcfg_dma",
                       GlbPcfgDma(_params=self._params),
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       cgra_cfg_pcfg=self.cgra_cfg_pcfgdma2mux,
                       rdrq_packet=self.pcfg_rdrq_packet_dma2sw,
                       rdrs_packet=self.pcfg_rdrs_packet_sw2dma,
                       # TODO: How to make this automatic
                       cfg_pcfg_dma_ctrl_mode=self.cfg_pcfg_dma_ctrl['mode'],
                       cfg_pcfg_network_latency=self.glb_tile_cfg.cfg_pcfg_network['latency'],
                       cfg_pcfg_dma_header=self.cfg_pcfg_dma_header,
                       pcfg_start_pulse=self.pcfg_start_pulse,
                       pcfg_done_pulse=self.pcfg_g2f_interrupt_pulse)

        self.add_child("glb_strm_mux",
                       GlbStrmMux(_params=self._params),
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

        self.glb_core_switch = GlbSwitch(_params=self._params)
        self.add_child("glb_switch",
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
                       cfg_tile_connected_prev=self.cfg_tile_connected_prev,
                       cfg_tile_connected_next=self.cfg_tile_connected_next,
                       cfg_pcfg_tile_connected_prev=self.cfg_pcfg_tile_connected_prev,
                       cfg_pcfg_tile_connected_next=self.cfg_pcfg_tile_connected_next,
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

        self.add_child("glb_proc_router",
                       GlbProcRouter(_params=self._params),
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

        self.add_child("glb_strm_router",
                       GlbRouter(_params=self._params, wr_channel=True, rd_channel=True),
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
                       cfg_tile_connected_prev=self.cfg_tile_connected_prev,
                       cfg_tile_connected_next=self.cfg_tile_connected_next)

        self.add_child("glb_pcfg_router",
                       GlbRouter(_params=self._params, wr_channel=False, rd_channel=True),
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
                       cfg_tile_connected_prev=self.cfg_tile_connected_prev,
                       cfg_tile_connected_next=self.cfg_tile_connected_next)

        self.glb_tile_sram_cfg_ctrl = GlbSramCfgCtrl(self._params)
        self.add_child("glb_sram_cfg_ctrl",
                       self.glb_tile_sram_cfg_ctrl,
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       if_sram_cfg_est_m=self.if_sram_cfg_est_m,
                       if_sram_cfg_wst_s=self.if_sram_cfg_wst_s)
        # FIXME: Array of modport is not supported by Kratos
        self.if_sram_cfg_bank2ctrl = []
        for i in range(self._params.banks_per_tile):
            if_sram_cfg_bank2ctrl = self.interface(GlbConfigInterface(addr_width=self._params.bank_addr_width,
                                                                      data_width=self._params.axi_data_width),
                                                   f"if_sram_cfg_bank2core_{i}")
            self.if_sram_cfg_bank2ctrl.append(if_sram_cfg_bank2ctrl)
        for i in range(self._params.banks_per_tile):
            self.wire(self.glb_tile_sram_cfg_ctrl.if_sram_cfg_ctrl2bank_m[i], self.if_sram_cfg_bank2ctrl[i])

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
                           if_sram_cfg_s=self.if_sram_cfg_bank2ctrl[i])
            self.glb_bank_arr.append(glb_bank)

        if self._params.is_sram_stub:
            self.readmemh_block = RawStringStmt(["initial begin",
                                                "\tstring b0_file_name;",
                                                "\tstring b1_file_name;",
                                                "\tstring load_arg;",
                                                "\t$sformat(b0_file_name, \"testvectors/tile%0d_b0.dat\", glb_tile_id);",  # noqa
                                                "\t$sformat(b1_file_name, \"testvectors/tile%0d_b1.dat\", glb_tile_id);",  # noqa
                                                "\t$sformat(load_arg, \"LOAD%0d\", glb_tile_id);",
                                                "\tif (($test$plusargs(load_arg))) begin",
                                                "\t\t$readmemh(b0_file_name, glb_core.glb_bank_0.glb_bank_memory.glb_bank_sram_stub.mem);",  # noqa
                                                "\t\t$readmemh(b1_file_name, glb_core.glb_bank_1.glb_bank_memory.glb_bank_sram_stub.mem);",  # noqa
                                                "\tend",
                                                "end"])
            self.writememh_block = RawStringStmt(["final begin",
                                                "\tstring b0_file_name;",
                                                "\tstring b1_file_name;",
                                                "\tstring save_arg;",
                                                "\t$sformat(b0_file_name, \"testvectors/tile%0d_b0_out.dat\", glb_tile_id);",  # noqa
                                                "\t$sformat(b1_file_name, \"testvectors/tile%0d_b1_out.dat\", glb_tile_id);",  # noqa
                                                "\t$sformat(save_arg, \"SAVE%0d\", glb_tile_id);",
                                                "\tif (($test$plusargs(save_arg))) begin",
                                                "\t\t$writememh(b0_file_name, glb_core.glb_bank_0.glb_bank_memory.glb_bank_sram_stub.mem);",  # noqa
                                                "\t\t$writememh(b1_file_name, glb_core.glb_bank_1.glb_bank_memory.glb_bank_sram_stub.mem);",  # noqa
                                                "\tend",
                                                "end"])
            self.add_stmt(self.readmemh_block.stmt())
            self.add_stmt(self.writememh_block.stmt())

        self.pcfg_wiring()

    def interface_wiring(self):
        self.if_cfg = GlbConfigInterface(addr_width=self._params.axi_addr_width, data_width=self._params.axi_data_width)
        self.if_sram_cfg = GlbConfigInterface(addr_width=self._params.glb_addr_width,
                                              data_width=self._params.axi_data_width)

        self.if_cfg_est_m = self.interface(self.if_cfg, "if_cfg_est_m")
        self.if_cfg_wst_s = self.interface(self.if_cfg, "if_cfg_wst_s")
        self.if_sram_cfg_est_m = self.interface(self.if_sram_cfg, "if_sram_cfg_est_m")
        self.if_sram_cfg_wst_s = self.interface(self.if_sram_cfg, "if_sram_cfg_wst_s")

        self.wire(self.if_cfg_est_m.wr_en, self.if_cfg_est_m_wr_en)
        self.wire(self.if_cfg_est_m.wr_addr, self.if_cfg_est_m_wr_addr)
        self.wire(self.if_cfg_est_m.wr_data, self.if_cfg_est_m_wr_data)
        self.wire(self.if_cfg_est_m.rd_en, self.if_cfg_est_m_rd_en)
        self.wire(self.if_cfg_est_m.rd_addr, self.if_cfg_est_m_rd_addr)
        self.wire(self.if_cfg_est_m.rd_data, self.if_cfg_est_m_rd_data)
        self.wire(self.if_cfg_est_m.rd_data_valid, self.if_cfg_est_m_rd_data_valid)

        self.wire(self.if_cfg_wst_s.wr_en, self.if_cfg_wst_s_wr_en)
        self.wire(self.if_cfg_wst_s.wr_addr, self.if_cfg_wst_s_wr_addr)
        self.wire(self.if_cfg_wst_s.wr_data, self.if_cfg_wst_s_wr_data)
        self.wire(self.if_cfg_wst_s.rd_en, self.if_cfg_wst_s_rd_en)
        self.wire(self.if_cfg_wst_s.rd_addr, self.if_cfg_wst_s_rd_addr)
        self.wire(self.if_cfg_wst_s.rd_data, self.if_cfg_wst_s_rd_data)
        self.wire(self.if_cfg_wst_s.rd_data_valid, self.if_cfg_wst_s_rd_data_valid)

        self.wire(self.if_sram_cfg_est_m.wr_en, self.if_sram_cfg_est_m_wr_en)
        self.wire(self.if_sram_cfg_est_m.wr_addr, self.if_sram_cfg_est_m_wr_addr)
        self.wire(self.if_sram_cfg_est_m.wr_data, self.if_sram_cfg_est_m_wr_data)
        self.wire(self.if_sram_cfg_est_m.rd_en, self.if_sram_cfg_est_m_rd_en)
        self.wire(self.if_sram_cfg_est_m.rd_addr, self.if_sram_cfg_est_m_rd_addr)
        self.wire(self.if_sram_cfg_est_m.rd_data, self.if_sram_cfg_est_m_rd_data)
        self.wire(self.if_sram_cfg_est_m.rd_data_valid, self.if_sram_cfg_est_m_rd_data_valid)

        self.wire(self.if_sram_cfg_wst_s.wr_en, self.if_sram_cfg_wst_s_wr_en)
        self.wire(self.if_sram_cfg_wst_s.wr_addr, self.if_sram_cfg_wst_s_wr_addr)
        self.wire(self.if_sram_cfg_wst_s.wr_data, self.if_sram_cfg_wst_s_wr_data)
        self.wire(self.if_sram_cfg_wst_s.rd_en, self.if_sram_cfg_wst_s_rd_en)
        self.wire(self.if_sram_cfg_wst_s.rd_addr, self.if_sram_cfg_wst_s_rd_addr)
        self.wire(self.if_sram_cfg_wst_s.rd_data, self.if_sram_cfg_wst_s_rd_data)
        self.wire(self.if_sram_cfg_wst_s.rd_data_valid, self.if_sram_cfg_wst_s_rd_data_valid)

    def struct_wiring(self):
        self.wr_packet_sw2bankarr = self.var(
            "wr_packet_sw2bankarr", self.header.wr_packet_t, size=self._params.banks_per_tile)
        self.rdrq_packet_sw2bankarr = self.var(
            "rdrq_packet_sw2bankarr", self.header.rdrq_packet_t, size=self._params.banks_per_tile)
        self.rdrs_packet_bankarr2sw = self.var(
            "rdrs_packet_bankarr2sw", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        self.strm_data_g2f_dma2mux = self.var("strm_data_g2f_dma2mux", self._params.cgra_data_width)
        self.strm_data_valid_g2f_dma2mux = self.var("strm_data_valid_g2f_dma2mux", 1)
        self.strm_data_f2g_mux2dma = self.var("strm_data_f2g_mux2dma", self._params.cgra_data_width)
        self.strm_data_valid_f2g_mux2dma = self.var("strm_data_valid_f2g_mux2dma", 1)
        self.cgra_cfg_pcfgdma2mux = self.var("cgra_cfg_pcfgdma2mux", self.header.cgra_cfg_t)

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

        self.proc_wr_packet_w2e_wsti = self.var("proc_wr_packet_w2e_wsti", self.header.wr_packet_t)
        self.proc_wr_packet_w2e_esto = self.var("proc_wr_packet_w2e_esto", self.header.wr_packet_t)

        self.proc_rdrq_packet_w2e_wsti = self.var("proc_rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
        self.proc_rdrq_packet_w2e_esto = self.var("proc_rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

        self.proc_rdrs_packet_w2e_wsti = self.var("proc_rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
        self.proc_rdrs_packet_e2w_wsto = self.var("proc_rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)
        self.proc_rdrs_packet_e2w_esti = self.var("proc_rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
        self.proc_rdrs_packet_w2e_esto = self.var("proc_rdrs_packet_w2e_esto", self.header.rdrs_packet_t)

        self.strm_wr_packet_w2e_wsti = self.var("strm_wr_packet_w2e_wsti", self.header.wr_packet_t)
        self.strm_wr_packet_e2w_wsto = self.var("strm_wr_packet_e2w_wsto", self.header.wr_packet_t)
        self.strm_wr_packet_e2w_esti = self.var("strm_wr_packet_e2w_esti", self.header.wr_packet_t)
        self.strm_wr_packet_w2e_esto = self.var("strm_wr_packet_w2e_esto", self.header.wr_packet_t)

        self.strm_rdrq_packet_w2e_wsti = self.var("strm_rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_e2w_wsto = self.var("strm_rdrq_packet_e2w_wsto", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_e2w_esti = self.var("strm_rdrq_packet_e2w_esti", self.header.rdrq_packet_t)
        self.strm_rdrq_packet_w2e_esto = self.var("strm_rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

        self.strm_rdrs_packet_w2e_wsti = self.var("strm_rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_e2w_wsto = self.var("strm_rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_e2w_esti = self.var("strm_rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
        self.strm_rdrs_packet_w2e_esto = self.var("strm_rdrs_packet_w2e_esto", self.header.rdrs_packet_t)

        self.pcfg_rdrq_packet_w2e_wsti = self.var("pcfg_rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_e2w_wsto = self.var("pcfg_rdrq_packet_e2w_wsto", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_e2w_esti = self.var("pcfg_rdrq_packet_e2w_esti", self.header.rdrq_packet_t)
        self.pcfg_rdrq_packet_w2e_esto = self.var("pcfg_rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

        self.pcfg_rdrs_packet_w2e_wsti = self.var("pcfg_rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_e2w_wsto = self.var("pcfg_rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_e2w_esti = self.var("pcfg_rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
        self.pcfg_rdrs_packet_w2e_esto = self.var("pcfg_rdrs_packet_w2e_esto", self.header.rdrs_packet_t)

        for port, _ in self.header.wr_packet_ports:
            self.wire(self.proc_wr_packet_w2e_wsti[port], self.proc_w2e_wsti_dict[port])
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.proc_wr_packet_w2e_esto[port], self.proc_w2e_esto_dict[port])

        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.proc_rdrq_packet_w2e_wsti[port], self.proc_w2e_wsti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.proc_rdrq_packet_w2e_esto[port], self.proc_w2e_esto_dict[port])

        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.proc_rdrs_packet_e2w_wsto[port], self.proc_e2w_wsto_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.proc_rdrs_packet_e2w_esti[port], self.proc_e2w_esti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.proc_rdrs_packet_w2e_wsti[port], self.proc_w2e_wsti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.proc_rdrs_packet_w2e_esto[port], self.proc_w2e_esto_dict[port])

        for port, _ in self.header.wr_packet_ports:
            self.wire(self.strm_wr_packet_w2e_wsti[port], self.strm_w2e_wsti_dict[port])
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.strm_wr_packet_w2e_esto[port], self.strm_w2e_esto_dict[port])
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.strm_wr_packet_e2w_esti[port], self.strm_e2w_esti_dict[port])
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.strm_wr_packet_e2w_wsto[port], self.strm_e2w_wsto_dict[port])

        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.strm_rdrq_packet_w2e_wsti[port], self.strm_w2e_wsti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.strm_rdrq_packet_w2e_esto[port], self.strm_w2e_esto_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.strm_rdrq_packet_e2w_esti[port], self.strm_e2w_esti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.strm_rdrq_packet_e2w_wsto[port], self.strm_e2w_wsto_dict[port])

        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.strm_rdrs_packet_e2w_wsto[port], self.strm_e2w_wsto_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.strm_rdrs_packet_e2w_esti[port], self.strm_e2w_esti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.strm_rdrs_packet_w2e_wsti[port], self.strm_w2e_wsti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.strm_rdrs_packet_w2e_esto[port], self.strm_w2e_esto_dict[port])

        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.pcfg_rdrq_packet_w2e_wsti[port], self.pcfg_w2e_wsti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.pcfg_rdrq_packet_w2e_esto[port], self.pcfg_w2e_esto_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.pcfg_rdrq_packet_e2w_esti[port], self.pcfg_e2w_esti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.pcfg_rdrq_packet_e2w_wsto[port], self.pcfg_e2w_wsto_dict[port])

        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.pcfg_rdrs_packet_e2w_wsto[port], self.pcfg_e2w_wsto_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.pcfg_rdrs_packet_e2w_esti[port], self.pcfg_e2w_esti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.pcfg_rdrs_packet_w2e_wsti[port], self.pcfg_w2e_wsti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.pcfg_rdrs_packet_w2e_esto[port], self.pcfg_w2e_esto_dict[port])

    def pcfg_wiring(self):
        cgra_cfg_g2f_w = self.var(f"cgra_cfg_g2f_cfg_w", self.header.cgra_cfg_t,
                                  size=self._params.cgra_per_glb, packed=True)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_g2f, cgra_cfg_g2f_w)
        for i in range(self._params.cgra_per_glb):
            self.wire(cgra_cfg_g2f_w[i]['wr_en'], self.cgra_cfg_g2f_cfg_wr_en[i])
            self.wire(cgra_cfg_g2f_w[i]['rd_en'], self.cgra_cfg_g2f_cfg_rd_en[i])
            self.wire(cgra_cfg_g2f_w[i]['addr'], self.cgra_cfg_g2f_cfg_addr[i])
            self.wire(cgra_cfg_g2f_w[i]['data'], self.cgra_cfg_g2f_cfg_data[i])

        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['wr_en'], self.cgra_cfg_jtag_wsti_wr_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['rd_en'], self.cgra_cfg_jtag_wsti_rd_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['addr'], self.cgra_cfg_jtag_wsti_addr)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['data'], self.cgra_cfg_jtag_wsti_data)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['wr_en'], self.cgra_cfg_jtag_esto_wr_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['rd_en'], self.cgra_cfg_jtag_esto_rd_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['addr'], self.cgra_cfg_jtag_esto_addr)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['data'], self.cgra_cfg_jtag_esto_data)

        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['wr_en'], self.cgra_cfg_pcfg_wsti_wr_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['rd_en'], self.cgra_cfg_pcfg_wsti_rd_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['addr'], self.cgra_cfg_pcfg_wsti_addr)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['data'], self.cgra_cfg_pcfg_wsti_data)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['wr_en'], self.cgra_cfg_pcfg_esto_wr_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['rd_en'], self.cgra_cfg_pcfg_esto_rd_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['addr'], self.cgra_cfg_pcfg_esto_addr)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['data'], self.cgra_cfg_pcfg_esto_data)

        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti_rd_en_bypass, self.cgra_cfg_jtag_wsti_rd_en_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto_rd_en_bypass, self.cgra_cfg_jtag_esto_rd_en_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti_addr_bypass, self.cgra_cfg_jtag_wsti_addr_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto_addr_bypass, self.cgra_cfg_jtag_esto_addr_bypass)
