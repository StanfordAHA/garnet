from kratos import Generator, RawStringStmt
from kratos.util import clock
from global_buffer.design.glb_store_dma import GlbStoreDma
from global_buffer.design.glb_load_dma import GlbLoadDma
from global_buffer.design.glb_pcfg_dma import GlbPcfgDma
from global_buffer.design.glb_cfg import GlbCfg
from global_buffer.design.glb_bank_mux import GlbBankMux
from global_buffer.design.glb_ring_switch import GlbRingSwitch
from global_buffer.design.glb_pcfg_broadcast import GlbPcfgBroadcast
from global_buffer.design.glb_switch import GlbSwitch
from global_buffer.design.glb_tile_ifc import GlbTileInterface
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
        self.clk_en_pcfg_broadcast = self.clock_en("clk_en_pcfg_broadcast")
        self.clk_en_master = self.clock_en("clk_en_master")
        self.clk_en_bank_master = self.clock_en("clk_en_bank_master")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

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

        # Processor AXI interface
        self.if_proc = GlbTileInterface(addr_width=self._params.glb_addr_width,
                                        data_width=self._params.bank_data_width, is_clk_en=True, is_strb=True)
        self.if_proc_est_m = self.interface(self.if_proc, "if_proc_est_m")
        self.if_proc_wst_s = self.interface(self.if_proc, "if_proc_wst_s")
        # Connect m2s ports
        for m2s_port in self.if_proc.m_to_s:
            port = self.output(f"if_proc_est_m_{m2s_port}", self.if_proc_est_m[m2s_port].width)
            self.wire(port, self.if_proc_est_m[m2s_port])
            port = self.input(f"if_proc_wst_s_{m2s_port}", self.if_proc_wst_s[m2s_port].width)
            self.wire(port, self.if_proc_wst_s[m2s_port])
        # Connect s2m ports
        for s2m_port in self.if_proc.s_to_m:
            port = self.input(f"if_proc_est_m_{s2m_port}", self.if_proc_est_m[s2m_port].width)
            self.wire(port, self.if_proc_est_m[s2m_port])
            port = self.output(f"if_proc_wst_s_{s2m_port}", self.if_proc_wst_s[s2m_port].width)
            self.wire(port, self.if_proc_wst_s[s2m_port])

        # Configuration interface
        self.if_cfg = GlbTileInterface(addr_width=self._params.axi_addr_width,
                                       data_width=self._params.axi_data_width, is_clk_en=True, is_strb=False)
        self.if_cfg_est_m = self.interface(self.if_cfg, "if_cfg_est_m")
        self.if_cfg_wst_s = self.interface(self.if_cfg, "if_cfg_wst_s")
        # Connect m2s ports
        for m2s_port in self.if_cfg.m_to_s:
            port = self.output(f"if_cfg_est_m_{m2s_port}", self.if_cfg_est_m[m2s_port].width)
            self.wire(port, self.if_cfg_est_m[m2s_port])
            port = self.input(f"if_cfg_wst_s_{m2s_port}", self.if_cfg_wst_s[m2s_port].width)
            self.wire(port, self.if_cfg_wst_s[m2s_port])
        # Connect s2m ports
        for s2m_port in self.if_cfg.s_to_m:
            port = self.input(f"if_cfg_est_m_{s2m_port}", self.if_cfg_est_m[s2m_port].width)
            self.wire(port, self.if_cfg_est_m[s2m_port])
            port = self.output(f"if_cfg_wst_s_{s2m_port}", self.if_cfg_wst_s[s2m_port].width)
            self.wire(port, self.if_cfg_wst_s[s2m_port])

        self.cfg_tile_connected_wsti = self.input("cfg_tile_connected_wsti", 1)
        self.cfg_tile_connected_esto = self.output("cfg_tile_connected_esto", 1)
        self.cfg_pcfg_tile_connected_wsti = self.input("cfg_pcfg_tile_connected_wsti", 1)
        self.cfg_pcfg_tile_connected_esto = self.output("cfg_pcfg_tile_connected_esto", 1)

        self.cgra_cfg_jtag_wr_en_wsti = self.input("cgra_cfg_jtag_wr_en_wsti", 1)
        self.cgra_cfg_jtag_rd_en_wsti = self.input("cgra_cfg_jtag_rd_en_wsti", 1)
        self.cgra_cfg_jtag_addr_wsti = self.input("cgra_cfg_jtag_addr_wsti", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_data_wsti = self.input("cgra_cfg_jtag_data_wsti", self._params.cgra_cfg_data_width)

        self.cgra_cfg_jtag_wr_en_esto = self.output("cgra_cfg_jtag_wr_en_esto", 1)
        self.cgra_cfg_jtag_rd_en_esto = self.output("cgra_cfg_jtag_rd_en_esto", 1)
        self.cgra_cfg_jtag_addr_esto = self.output("cgra_cfg_jtag_addr_esto", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_data_esto = self.output("cgra_cfg_jtag_data_esto", self._params.cgra_cfg_data_width)

        self.cgra_cfg_jtag_rd_en_bypass_wsti = self.input("cgra_cfg_jtag_rd_en_bypass_wsti", 1)
        self.cgra_cfg_jtag_addr_bypass_wsti = self.input(
            "cgra_cfg_jtag_addr_bypass_wsti", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_rd_en_bypass_esto = self.output("cgra_cfg_jtag_rd_en_bypass_esto", 1)
        self.cgra_cfg_jtag_addr_bypass_esto = self.output(
            "cgra_cfg_jtag_addr_bypass_esto", self._params.cgra_cfg_addr_width)

        self.cgra_cfg_pcfg_wr_en_w2e_wsti = self.input("cgra_cfg_pcfg_wr_en_w2e_wsti", 1)
        self.cgra_cfg_pcfg_rd_en_w2e_wsti = self.input("cgra_cfg_pcfg_rd_en_w2e_wsti", 1)
        self.cgra_cfg_pcfg_addr_w2e_wsti = self.input("cgra_cfg_pcfg_addr_w2e_wsti", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_data_w2e_wsti = self.input("cgra_cfg_pcfg_data_w2e_wsti", self._params.cgra_cfg_data_width)
        self.cgra_cfg_pcfg_wr_en_w2e_esto = self.output("cgra_cfg_pcfg_wr_en_w2e_esto", 1)
        self.cgra_cfg_pcfg_rd_en_w2e_esto = self.output("cgra_cfg_pcfg_rd_en_w2e_esto", 1)
        self.cgra_cfg_pcfg_addr_w2e_esto = self.output("cgra_cfg_pcfg_addr_w2e_esto", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_data_w2e_esto = self.output("cgra_cfg_pcfg_data_w2e_esto", self._params.cgra_cfg_data_width)

        self.cgra_cfg_pcfg_wr_en_e2w_esti = self.input("cgra_cfg_pcfg_wr_en_e2w_esti", 1)
        self.cgra_cfg_pcfg_rd_en_e2w_esti = self.input("cgra_cfg_pcfg_rd_en_e2w_esti", 1)
        self.cgra_cfg_pcfg_addr_e2w_esti = self.input("cgra_cfg_pcfg_addr_e2w_esti", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_data_e2w_esti = self.input("cgra_cfg_pcfg_data_e2w_esti", self._params.cgra_cfg_data_width)
        self.cgra_cfg_pcfg_wr_en_e2w_wsto = self.output("cgra_cfg_pcfg_wr_en_e2w_wsto", 1)
        self.cgra_cfg_pcfg_rd_en_e2w_wsto = self.output("cgra_cfg_pcfg_rd_en_e2w_wsto", 1)
        self.cgra_cfg_pcfg_addr_e2w_wsto = self.output("cgra_cfg_pcfg_addr_e2w_wsto", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_data_e2w_wsto = self.output("cgra_cfg_pcfg_data_e2w_wsto", self._params.cgra_cfg_data_width)

        self.strm_data_f2g = self.input("strm_data_f2g", self._params.cgra_data_width,
                                        size=self._params.cgra_per_glb, packed=True)
        self.strm_data_valid_f2g = self.input("strm_data_valid_f2g", 1, size=self._params.cgra_per_glb, packed=True)
        self.strm_data_g2f = self.output("strm_data_g2f", self._params.cgra_data_width,
                                         size=self._params.cgra_per_glb, packed=True)
        self.strm_data_valid_g2f = self.output(
            "strm_data_valid_g2f", 1, size=self._params.cgra_per_glb, packed=True)
        self.data_flush = self.output("data_flush", 1)

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

        # Struct
        self.struct_wiring()

        # Local variables
        # configuration
        self.cfg_tile_connected_prev = self.var("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.var("cfg_tile_connected_next", 1)
        self.cfg_pcfg_tile_connected_prev = self.var("cfg_pcfg_tile_connected_prev", 1)
        self.cfg_pcfg_tile_connected_next = self.var("cfg_pcfg_tile_connected_next", 1)

        # st dma
        self.cfg_st_dma_ctrl = self.var("cfg_st_dma_ctrl", self.header.cfg_store_dma_ctrl_t)
        self.cfg_st_dma_header = self.var("cfg_st_dma_header", self.header.cfg_dma_header_t,
                                          size=self._params.queue_depth)
        # ld dma
        self.cfg_ld_dma_ctrl = self.var("cfg_ld_dma_ctrl", self.header.cfg_load_dma_ctrl_t)
        self.cfg_ld_dma_header = self.var("cfg_ld_dma_header", self.header.cfg_dma_header_t,
                                          size=self._params.queue_depth)
        # pcfg dma
        self.cfg_pcfg_dma_ctrl = self.var("cfg_pcfg_dma_ctrl", self.header.cfg_pcfg_dma_ctrl_t)
        self.cfg_pcfg_dma_header = self.var("cfg_pcfg_dma_header", self.header.cfg_pcfg_dma_header_t)

        # pcfg broadcast
        self.cfg_pcfg_broadcast_mux = self.var("cfg_pcfg_broadcast_mux", self.header.cfg_pcfg_broadcast_mux_t)

        # Clock gating - cfg
        self.gclk_cfg = self.var("gclk_cfg", 1)
        self.clk_en_cfg = self.var("clk_en_cfg", 1)
        self.wire(self.clk_en_cfg, self.if_cfg_wst_s['wr_clk_en'] | self.if_cfg_wst_s['rd_clk_en'])
        self.add_child("glb_clk_gate_cfg",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_cfg | self.clk_en_master,
                       gclk=self.gclk_cfg)

        # Clock gating - pcfg broadcast
        self.gclk_pcfg_broadcast = self.var("gclk_pcfg_broadcast", 1)
        self.add_child("glb_clk_gate_pcfg_broadcast",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_pcfg_broadcast | self.clk_en_master,
                       gclk=self.gclk_pcfg_broadcast)

        # Clock gating - ld_dma
        self.clk_en_ld_dma = self.var("clk_en_ld_dma", 1)
        self.gclk_ld_dma = self.var("gclk_ld_dma", 1)
        self.wire(self.clk_en_ld_dma, self.cfg_ld_dma_ctrl['mode'] != 0)
        self.clk_en_lddma2bank = self.var("clk_en_lddma2bank", 1)
        self.add_child("glb_clk_gate_ld_dma",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_ld_dma | self.clk_en_master,
                       gclk=self.gclk_ld_dma)

        # Clock gating - st_dma
        self.clk_en_st_dma = self.var("clk_en_st_dma", 1)
        self.gclk_st_dma = self.var("gclk_st_dma", 1)
        self.wire(self.clk_en_st_dma, self.cfg_st_dma_ctrl['mode'] != 0)
        self.clk_en_stdma2bank = self.var("clk_en_stdma2bank", 1)
        self.add_child("glb_clk_gate_st_dma",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_st_dma | self.clk_en_master,
                       gclk=self.gclk_st_dma)

        # Clock gating - proc switch
        self.clk_en_proc_switch = self.var("clk_en_proc_switch", 1)
        self.gclk_proc_switch = self.var("gclk_proc_switch", 1)
        self.wire(self.clk_en_proc_switch, self.if_proc_wst_s['wr_clk_en'] | self.if_proc_wst_s['rd_clk_en'])
        self.clk_en_procsw2bank = self.var("clk_en_procsw2bank", 1)
        self.add_child("glb_clk_gate_proc_switch",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_proc_switch | self.clk_en_master,
                       gclk=self.gclk_proc_switch)

        # Clock gating - pcfg_dma
        self.clk_en_pcfg_dma = self.var("clk_en_pcfg_dma", 1)
        self.gclk_pcfg_dma = self.var("gclk_pcfg_dma", 1)
        self.wire(self.clk_en_pcfg_dma, self.cfg_pcfg_dma_ctrl['mode'] != 0)
        self.clk_en_pcfgdma2bank = self.var("clk_en_pcfgdma2bank", 1)
        self.add_child("glb_clk_gate_pcfg_dma",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_pcfg_dma | self.clk_en_master,
                       gclk=self.gclk_pcfg_dma)

        # Clock gating - strm switch
        self.clk_en_strm_switch = self.var("clk_en_strm_switch", 1)
        self.gclk_strm_switch = self.var("gclk_strm_switch", 1)
        self.wire(self.clk_en_strm_switch, self.cfg_tile_connected_next | self.cfg_tile_connected_prev)
        self.clk_en_ring2bank = self.var("clk_en_ring2bank", 1)
        self.add_child("glb_clk_gate_strm_switch",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_strm_switch | self.clk_en_master,
                       gclk=self.gclk_strm_switch)

        # Clock gating - pcfg switch
        self.clk_en_pcfg_switch = self.var("clk_en_pcfg_switch", 1)
        self.gclk_pcfg_switch = self.var("gclk_pcfg_switch", 1)
        self.wire(self.clk_en_pcfg_switch, self.cfg_pcfg_tile_connected_next | self.cfg_pcfg_tile_connected_prev)
        self.clk_en_pcfgring2bank = self.var("clk_en_pcfgring2bank", 1)
        self.add_child("glb_clk_gate_pcfg_switch",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_pcfg_switch | self.clk_en_master,
                       gclk=self.gclk_pcfg_switch)

        # Clock gating - bank
        self.clk_en_bank = self.var("clk_en_bank", 1)
        self.gclk_bank = self.var("gclk_bank", 1)
        self.wire(self.clk_en_bank, self.clk_en_lddma2bank | self.clk_en_stdma2bank | self.clk_en_pcfgdma2bank
                  | self.clk_en_ring2bank | self.clk_en_pcfgring2bank | self.clk_en_procsw2bank)
        self.add_child("glb_clk_gate_bank",
                       ClkGate(_params=self._params),
                       clk=self.clk,
                       enable=self.clk_en_bank | self.clk_en_master | self.clk_en_bank_master,
                       gclk=self.gclk_bank)

        # module instantiation
        self.glb_cfg = GlbCfg(_params=self._params)
        self.add_child("glb_cfg",
                       self.glb_cfg,
                       mclk=self.clk,
                       gclk=clock(self.gclk_cfg),
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id)
        self.wire(self.cfg_tile_connected_next, self.glb_cfg.cfg_data_network['tile_connected'])
        self.wire(self.cfg_tile_connected_prev, self.cfg_tile_connected_wsti)
        self.wire(self.cfg_tile_connected_next, self.cfg_tile_connected_esto)
        self.wire(self.cfg_pcfg_tile_connected_next, self.glb_cfg.cfg_pcfg_network['tile_connected'])
        self.wire(self.cfg_pcfg_tile_connected_prev, self.cfg_pcfg_tile_connected_wsti)
        self.wire(self.cfg_pcfg_tile_connected_next, self.cfg_pcfg_tile_connected_esto)
        self.wire(self.glb_cfg.if_cfg_wst_s, self.if_cfg_wst_s)
        self.wire(self.glb_cfg.if_cfg_est_m, self.if_cfg_est_m)
        self.wire(self.cfg_st_dma_ctrl, self.glb_cfg.cfg_st_dma_ctrl)
        self.wire(self.cfg_st_dma_header, self.glb_cfg.cfg_st_dma_header)
        self.wire(self.cfg_ld_dma_ctrl, self.glb_cfg.cfg_ld_dma_ctrl)
        self.wire(self.cfg_ld_dma_header, self.glb_cfg.cfg_ld_dma_header)
        self.wire(self.cfg_pcfg_dma_ctrl, self.glb_cfg.cfg_pcfg_dma_ctrl)
        self.wire(self.cfg_pcfg_dma_header, self.glb_cfg.cfg_pcfg_dma_header)
        self.wire(self.cfg_pcfg_broadcast_mux, self.glb_cfg.cfg_pcfg_broadcast_mux)

        self.glb_pcfg_broadcast = GlbPcfgBroadcast(_params=self._params)
        self.add_child("glb_pcfg_broadcast",
                       self.glb_pcfg_broadcast,
                       clk=clock(self.gclk_pcfg_broadcast),
                       reset=self.reset,
                       cgra_cfg_dma2mux=self.cgra_cfg_pcfgdma2mux,
                       cfg_pcfg_broadcast_mux=self.cfg_pcfg_broadcast_mux)

        self.add_child("glb_store_dma",
                       GlbStoreDma(_params=self._params),
                       clk=clock(self.gclk_st_dma),
                       reset=self.reset,
                       clk_en_dma2bank=self.clk_en_stdma2bank,
                       data_f2g=self.strm_data_f2g,
                       data_valid_f2g=self.strm_data_valid_f2g,
                       wr_packet_dma2bank=self.wr_packet_dma2bank,
                       wr_packet_dma2ring=self.wr_packet_dma2ring,
                       # TODO: How to make this automatic
                       cfg_tile_connected_prev=self.cfg_tile_connected_prev,
                       cfg_tile_connected_next=self.cfg_tile_connected_next,
                       cfg_st_dma_num_repeat=self.cfg_st_dma_ctrl['num_repeat'],
                       cfg_st_dma_ctrl_use_valid=self.cfg_st_dma_ctrl['use_valid'],
                       cfg_st_dma_ctrl_mode=self.cfg_st_dma_ctrl['mode'],
                       cfg_data_network_latency=self.glb_cfg.cfg_data_network['latency'],
                       cfg_st_dma_header=self.cfg_st_dma_header,
                       st_dma_start_pulse=self.strm_f2g_start_pulse,
                       st_dma_done_interrupt=self.strm_f2g_interrupt_pulse,
                       cfg_data_network_f2g_mux=self.cfg_st_dma_ctrl['data_mux'])

        self.add_child("glb_load_dma",
                       GlbLoadDma(_params=self._params),
                       clk=clock(self.gclk_ld_dma),
                       reset=self.reset,
                       clk_en_dma2bank=self.clk_en_lddma2bank,
                       glb_tile_id=self.glb_tile_id,
                       data_g2f=self.strm_data_g2f,
                       data_valid_g2f=self.strm_data_valid_g2f,
                       data_flush=self.data_flush,
                       rdrq_packet_dma2bank=self.rdrq_packet_dma2bank,
                       rdrq_packet_dma2ring=self.rdrq_packet_dma2ring,
                       rdrs_packet_bank2dma=self.rdrs_packet_bank2dma,
                       rdrs_packet_ring2dma=self.rdrs_packet_ring2dma,
                       # TODO: How to make this automatic
                       cfg_tile_connected_prev=self.cfg_tile_connected_prev,
                       cfg_tile_connected_next=self.cfg_tile_connected_next,
                       cfg_ld_dma_num_repeat=self.cfg_ld_dma_ctrl['num_repeat'],
                       cfg_ld_dma_ctrl_use_valid=self.cfg_ld_dma_ctrl['use_valid'],
                       cfg_ld_dma_ctrl_use_flush=self.cfg_ld_dma_ctrl['use_flush'],
                       cfg_ld_dma_ctrl_mode=self.cfg_ld_dma_ctrl['mode'],
                       cfg_data_network_latency=self.glb_cfg.cfg_data_network['latency'],
                       cfg_ld_dma_header=self.cfg_ld_dma_header,
                       cfg_data_network_g2f_mux=self.cfg_ld_dma_ctrl['data_mux'],
                       ld_dma_start_pulse=self.strm_g2f_start_pulse,
                       ld_dma_done_interrupt=self.strm_g2f_interrupt_pulse)

        self.add_child("glb_pcfg_dma",
                       GlbPcfgDma(_params=self._params),
                       clk=clock(self.gclk_pcfg_dma),
                       reset=self.reset,
                       clk_en_dma2bank=self.clk_en_pcfgdma2bank,
                       glb_tile_id=self.glb_tile_id,
                       cgra_cfg_pcfg=self.cgra_cfg_pcfgdma2mux,
                       rdrq_packet_dma2bank=self.rdrq_packet_pcfgdma2bank,
                       rdrq_packet_dma2ring=self.rdrq_packet_pcfgdma2ring,
                       rdrs_packet_bank2dma=self.rdrs_packet_bank2pcfgdma,
                       rdrs_packet_ring2dma=self.rdrs_packet_pcfgring2dma,
                       # TODO: How to make this automatic
                       cfg_pcfg_tile_connected_prev=self.cfg_pcfg_tile_connected_prev,
                       cfg_pcfg_tile_connected_next=self.cfg_pcfg_tile_connected_next,
                       cfg_pcfg_dma_ctrl_mode=self.cfg_pcfg_dma_ctrl['mode'],
                       cfg_pcfg_dma_ctrl_relocation_value=self.cfg_pcfg_dma_ctrl['relocation_value'],
                       cfg_pcfg_dma_ctrl_relocation_is_msb=self.cfg_pcfg_dma_ctrl['relocation_is_msb'],
                       cfg_pcfg_network_latency=self.glb_cfg.cfg_pcfg_network['latency'],
                       cfg_pcfg_dma_header=self.cfg_pcfg_dma_header,
                       pcfg_dma_start_pulse=self.pcfg_start_pulse,
                       pcfg_dma_done_interrupt=self.pcfg_g2f_interrupt_pulse)

        self.glb_bank_mux = GlbBankMux(_params=self._params)
        self.add_child("glb_bank_mux",
                       self.glb_bank_mux,
                       clk=clock(self.gclk_bank),
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       wr_packet_procsw2bank=self.wr_packet_procsw2bank,
                       wr_packet_ring2bank=self.wr_packet_ring2bank,
                       wr_packet_dma2bank=self.wr_packet_dma2bank,
                       wr_packet_sw2bankarr=self.wr_packet_sw2bankarr,

                       rdrq_packet_procsw2bank=self.rdrq_packet_procsw2bank,
                       rdrq_packet_ring2bank=self.rdrq_packet_ring2bank,
                       rdrq_packet_dma2bank=self.rdrq_packet_dma2bank,
                       rdrq_packet_pcfgring2bank=self.rdrq_packet_pcfgring2bank,
                       rdrq_packet_pcfgdma2bank=self.rdrq_packet_pcfgdma2bank,
                       rdrq_packet_sw2bankarr=self.rdrq_packet_sw2bankarr,

                       rdrs_packet_bankarr2sw=self.rdrs_packet_bankarr2sw,
                       rdrs_packet_bank2procsw=self.rdrs_packet_bank2procsw,
                       rdrs_packet_bank2dma=self.rdrs_packet_bank2dma,
                       rdrs_packet_bank2pcfgdma=self.rdrs_packet_bank2pcfgdma,
                       rdrs_packet_bank2ring=self.rdrs_packet_bank2ring,
                       rdrs_packet_bank2pcfgring=self.rdrs_packet_bank2pcfgring,

                       # cfg
                       cfg_tile_connected_prev=self.cfg_tile_connected_prev,
                       cfg_tile_connected_next=self.cfg_tile_connected_next,
                       cfg_pcfg_tile_connected_prev=self.cfg_pcfg_tile_connected_prev,
                       cfg_pcfg_tile_connected_next=self.cfg_pcfg_tile_connected_next)

        self.glb_proc_switch = GlbSwitch(self._params, ifc=self.if_proc)
        self.add_child("glb_proc_switch",
                       self.glb_proc_switch,
                       mclk=self.clk,
                       gclk=clock(self.gclk_proc_switch),
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       if_est_m=self.if_proc_est_m,
                       if_wst_s=self.if_proc_wst_s,
                       clk_en_sw2bank=self.clk_en_procsw2bank,
                       wr_packet=self.wr_packet_procsw2bank,
                       rdrq_packet=self.rdrq_packet_procsw2bank,
                       rdrs_packet=self.rdrs_packet_bank2procsw)

        self.add_child("glb_strm_ring_switch",
                       GlbRingSwitch(_params=self._params, wr_channel=True, rd_channel=True),
                       clk=clock(self.gclk_strm_switch),
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       clk_en_ring2bank=self.clk_en_ring2bank,
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
                       wr_packet_ring2bank=self.wr_packet_ring2bank,
                       wr_packet_dma2ring=self.wr_packet_dma2ring,
                       rdrq_packet_ring2bank=self.rdrq_packet_ring2bank,
                       rdrq_packet_dma2ring=self.rdrq_packet_dma2ring,
                       rdrs_packet_ring2dma=self.rdrs_packet_ring2dma,
                       rdrs_packet_bank2ring=self.rdrs_packet_bank2ring,
                       cfg_ld_dma_on=(self.cfg_ld_dma_ctrl['mode'] != 0),
                       cfg_tile_connected_prev=self.cfg_tile_connected_prev,
                       cfg_tile_connected_next=self.cfg_tile_connected_next)

        self.add_child("glb_pcfg_ring_switch",
                       GlbRingSwitch(_params=self._params, wr_channel=False, rd_channel=True),
                       clk=clock(self.gclk_pcfg_switch),
                       clk_en_ring2bank=self.clk_en_pcfgring2bank,
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
                       rdrq_packet_dma2ring=self.rdrq_packet_pcfgdma2ring,
                       rdrq_packet_ring2bank=self.rdrq_packet_pcfgring2bank,
                       rdrs_packet_ring2dma=self.rdrs_packet_pcfgring2dma,
                       rdrs_packet_bank2ring=self.rdrs_packet_bank2pcfgring,
                       cfg_ld_dma_on=(self.cfg_pcfg_dma_ctrl['mode'] != 0),
                       cfg_tile_connected_prev=self.cfg_pcfg_tile_connected_prev,
                       cfg_tile_connected_next=self.cfg_pcfg_tile_connected_next)

        self.glb_bank_arr = []
        for i in range(self._params.banks_per_tile):
            glb_bank = GlbBank(self._params)
            self.add_child(f"glb_bank_{i}",
                           glb_bank,
                           clk=clock(self.gclk_bank),
                           reset=self.reset,
                           wr_packet=self.wr_packet_sw2bankarr[i],
                           rdrq_packet=self.rdrq_packet_sw2bankarr[i],
                           rdrs_packet=self.rdrs_packet_bankarr2sw[i])
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

    def struct_wiring(self):
        self.wr_packet_sw2bankarr = self.var(
            "wr_packet_sw2bankarr", self.header.wr_bank_packet_t, size=self._params.banks_per_tile)
        self.rdrq_packet_sw2bankarr = self.var(
            "rdrq_packet_sw2bankarr", self.header.rdrq_bank_packet_t, size=self._params.banks_per_tile)
        self.rdrs_packet_bankarr2sw = self.var(
            "rdrs_packet_bankarr2sw", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        self.cgra_cfg_pcfgdma2mux = self.var("cgra_cfg_pcfgdma2mux", self.header.cgra_cfg_t)

        self.wr_packet_procsw2bank = self.var("wr_packet_procsw2bank", self.header.wr_packet_t)
        self.wr_packet_ring2bank = self.var("wr_packet_ring2bank", self.header.wr_packet_t)
        self.wr_packet_dma2ring = self.var("wr_packet_dma2ring", self.header.wr_packet_t)
        self.wr_packet_dma2bank = self.var("wr_packet_dma2bank", self.header.wr_packet_t)

        self.rdrq_packet_procsw2bank = self.var("rdrq_packet_procsw2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_ring2bank = self.var("rdrq_packet_ring2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2ring = self.var("rdrq_packet_dma2ring", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2bank = self.var("rdrq_packet_dma2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgdma2bank = self.var("rdrq_packet_pcfgdma2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgring2bank = self.var("rdrq_packet_pcfgring2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_pcfgdma2ring = self.var("rdrq_packet_pcfgdma2ring", self.header.rdrq_packet_t)

        self.rdrs_packet_bank2procsw = self.var("rdrs_packet_bank2procsw", self.header.rdrs_packet_t)
        self.rdrs_packet_bank2ring = self.var("rdrs_packet_bank2ring", self.header.rdrs_packet_t)
        self.rdrs_packet_ring2dma = self.var("rdrs_packet_ring2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_bank2dma = self.var("rdrs_packet_bank2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_pcfgring2dma = self.var("rdrs_packet_pcfgring2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_bank2pcfgring = self.var("rdrs_packet_bank2pcfgring", self.header.rdrs_packet_t)
        self.rdrs_packet_bank2pcfgdma = self.var("rdrs_packet_bank2pcfgdma", self.header.rdrs_packet_t)

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
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_g2f, cgra_cfg_g2f_w)
        for i in range(self._params.cgra_per_glb):
            self.wire(cgra_cfg_g2f_w[i]['wr_en'], self.cgra_cfg_g2f_cfg_wr_en[i])
            self.wire(cgra_cfg_g2f_w[i]['rd_en'], self.cgra_cfg_g2f_cfg_rd_en[i])
            self.wire(cgra_cfg_g2f_w[i]['addr'], self.cgra_cfg_g2f_cfg_addr[i])
            self.wire(cgra_cfg_g2f_w[i]['data'], self.cgra_cfg_g2f_cfg_data[i])

        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_wsti['wr_en'], self.cgra_cfg_jtag_wr_en_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_wsti['rd_en'], self.cgra_cfg_jtag_rd_en_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_wsti['addr'], self.cgra_cfg_jtag_addr_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_wsti['data'], self.cgra_cfg_jtag_data_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_esto['wr_en'], self.cgra_cfg_jtag_wr_en_esto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_esto['rd_en'], self.cgra_cfg_jtag_rd_en_esto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_esto['addr'], self.cgra_cfg_jtag_addr_esto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_esto['data'], self.cgra_cfg_jtag_data_esto)

        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_wsti['wr_en'], self.cgra_cfg_pcfg_wr_en_w2e_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_wsti['rd_en'], self.cgra_cfg_pcfg_rd_en_w2e_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_wsti['addr'], self.cgra_cfg_pcfg_addr_w2e_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_wsti['data'], self.cgra_cfg_pcfg_data_w2e_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_esto['wr_en'], self.cgra_cfg_pcfg_wr_en_w2e_esto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_esto['rd_en'], self.cgra_cfg_pcfg_rd_en_w2e_esto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_esto['addr'], self.cgra_cfg_pcfg_addr_w2e_esto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_esto['data'], self.cgra_cfg_pcfg_data_w2e_esto)

        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_esti['wr_en'], self.cgra_cfg_pcfg_wr_en_e2w_esti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_esti['rd_en'], self.cgra_cfg_pcfg_rd_en_e2w_esti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_esti['addr'], self.cgra_cfg_pcfg_addr_e2w_esti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_esti['data'], self.cgra_cfg_pcfg_data_e2w_esti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_wsto['wr_en'], self.cgra_cfg_pcfg_wr_en_e2w_wsto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_wsto['rd_en'], self.cgra_cfg_pcfg_rd_en_e2w_wsto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_wsto['addr'], self.cgra_cfg_pcfg_addr_e2w_wsto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_pcfg_wsto['data'], self.cgra_cfg_pcfg_data_e2w_wsto)

        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_rd_en_bypass_wsti, self.cgra_cfg_jtag_rd_en_bypass_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_rd_en_bypass_esto, self.cgra_cfg_jtag_rd_en_bypass_esto)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_addr_bypass_wsti, self.cgra_cfg_jtag_addr_bypass_wsti)
        self.wire(self.glb_pcfg_broadcast.cgra_cfg_jtag_addr_bypass_esto, self.cgra_cfg_jtag_addr_bypass_esto)
