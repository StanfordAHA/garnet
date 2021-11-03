from kratos import Generator
from global_buffer.design.glb_core import GlbCore
from global_buffer.design.glb_tile_cfg import GlbTileCfg
from global_buffer.design.glb_tile_pcfg_switch import GlbTilePcfgSwitch
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbTile(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_tile")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input(
            "glb_tile_id", self._params.tile_sel_addr_width)

        self.proc_wr_en_e2w_esti = self.input(
            "proc_wr_en_e2w_esti", 1)
        self.proc_wr_strb_e2w_esti = self.input(
            "proc_wr_strb_e2w_esti", self._params.bank_data_width // 8)
        self.proc_wr_addr_e2w_esti = self.input(
            "proc_wr_addr_e2w_esti", self._params.glb_addr_width)
        self.proc_wr_data_e2w_esti = self.input(
            "proc_wr_data_e2w_esti", self._params.bank_data_width)
        self.proc_rd_en_e2w_esti = self.input(
            "proc_rd_en_e2w_esti", 1)
        self.proc_rd_addr_e2w_esti = self.input(
            "proc_rd_addr_e2w_esti", self._params.glb_addr_width)
        self.proc_rd_data_e2w_esti = self.input(
            "proc_rd_data_e2w_esti", self._params.bank_data_width)
        self.proc_rd_data_valid_e2w_esti = self.input(
            "proc_rd_data_valid_e2w_esti", 1)

        self.proc_wr_en_w2e_esto = self.output(
            "proc_wr_en_w2e_esto", 1)
        self.proc_wr_strb_w2e_esto = self.output(
            "proc_wr_strb_w2e_esto", self._params.bank_data_width // 8)
        self.proc_wr_addr_w2e_esto = self.output(
            "proc_wr_addr_w2e_esto", self._params.glb_addr_width)
        self.proc_wr_data_w2e_esto = self.output(
            "proc_wr_data_w2e_esto", self._params.bank_data_width)
        self.proc_rd_en_w2e_esto = self.output(
            "proc_rd_en_w2e_esto", 1)
        self.proc_rd_addr_w2e_esto = self.output(
            "proc_rd_addr_w2e_esto", self._params.glb_addr_width)
        self.proc_rd_data_w2e_esto = self.output(
            "proc_rd_data_w2e_esto", self._params.bank_data_width)
        self.proc_rd_data_valid_w2e_esto = self.output(
            "proc_rd_data_valid_w2e_esto", 1)

        self.proc_wr_en_w2e_wsti = self.input(
            "proc_wr_en_w2e_wsti", 1)
        self.proc_wr_strb_w2e_wsti = self.input(
            "proc_wr_strb_w2e_wsti", self._params.bank_data_width // 8)
        self.proc_wr_addr_w2e_wsti = self.input(
            "proc_wr_addr_w2e_wsti", self._params.glb_addr_width)
        self.proc_wr_data_w2e_wsti = self.input(
            "proc_wr_data_w2e_wsti", self._params.bank_data_width)
        self.proc_rd_en_w2e_wsti = self.input(
            "proc_rd_en_w2e_wsti", 1)
        self.proc_rd_addr_w2e_wsti = self.input(
            "proc_rd_addr_w2e_wsti", self._params.glb_addr_width)
        self.proc_rd_data_w2e_wsti = self.input(
            "proc_rd_data_w2e_wsti", self._params.bank_data_width)
        self.proc_rd_data_valid_w2e_wsti = self.input(
            "proc_rd_data_valid_w2e_wsti", 1)

        self.proc_wr_en_e2w_wsto = self.output(
            "proc_wr_en_e2w_wsto", 1)
        self.proc_wr_strb_e2w_wsto = self.output(
            "proc_wr_strb_e2w_wsto", self._params.bank_data_width // 8)
        self.proc_wr_addr_e2w_wsto = self.output(
            "proc_wr_addr_e2w_wsto", self._params.glb_addr_width)
        self.proc_wr_data_e2w_wsto = self.output(
            "proc_wr_data_e2w_wsto", self._params.bank_data_width)
        self.proc_rd_en_e2w_wsto = self.output(
            "proc_rd_en_e2w_wsto", 1)
        self.proc_rd_addr_e2w_wsto = self.output(
            "proc_rd_addr_e2w_wsto", self._params.glb_addr_width)
        self.proc_rd_data_e2w_wsto = self.output(
            "proc_rd_data_e2w_wsto", self._params.bank_data_width)
        self.proc_rd_data_valid_e2w_wsto = self.output(
            "proc_rd_data_valid_e2w_wsto", 1)

        self.strm_wr_en_e2w_esti = self.input(
            "strm_wr_en_e2w_esti", 1)
        self.strm_wr_strb_e2w_esti = self.input(
            "strm_wr_strb_e2w_esti", self._params.bank_data_width // 8)
        self.strm_wr_addr_e2w_esti = self.input(
            "strm_wr_addr_e2w_esti", self._params.glb_addr_width)
        self.strm_wr_data_e2w_esti = self.input(
            "strm_wr_data_e2w_esti", self._params.bank_data_width)
        self.strm_rd_en_e2w_esti = self.input(
            "strm_rd_en_e2w_esti", 1)
        self.strm_rd_addr_e2w_esti = self.input(
            "strm_rd_addr_e2w_esti", self._params.glb_addr_width)
        self.strm_rd_data_e2w_esti = self.input(
            "strm_rd_data_e2w_esti", self._params.bank_data_width)
        self.strm_rd_data_valid_e2w_esti = self.input(
            "strm_rd_data_valid_e2w_esti", 1)

        self.strm_wr_en_w2e_esto = self.output(
            "strm_wr_en_w2e_esto", 1)
        self.strm_wr_strb_w2e_esto = self.output(
            "strm_wr_strb_w2e_esto", self._params.bank_data_width // 8)
        self.strm_wr_addr_w2e_esto = self.output(
            "strm_wr_addr_w2e_esto", self._params.glb_addr_width)
        self.strm_wr_data_w2e_esto = self.output(
            "strm_wr_data_w2e_esto", self._params.bank_data_width)
        self.strm_rd_en_w2e_esto = self.output(
            "strm_rd_en_w2e_esto", 1)
        self.strm_rd_addr_w2e_esto = self.output(
            "strm_rd_addr_w2e_esto", self._params.glb_addr_width)
        self.strm_rd_data_w2e_esto = self.output(
            "strm_rd_data_w2e_esto", self._params.bank_data_width)
        self.strm_rd_data_valid_w2e_esto = self.output(
            "strm_rd_data_valid_w2e_esto", 1)

        self.strm_wr_en_w2e_wsti = self.input(
            "strm_wr_en_w2e_wsti", 1)
        self.strm_wr_strb_w2e_wsti = self.input(
            "strm_wr_strb_w2e_wsti", self._params.bank_data_width // 8)
        self.strm_wr_addr_w2e_wsti = self.input(
            "strm_wr_addr_w2e_wsti", self._params.glb_addr_width)
        self.strm_wr_data_w2e_wsti = self.input(
            "strm_wr_data_w2e_wsti", self._params.bank_data_width)
        self.strm_rd_en_w2e_wsti = self.input(
            "strm_rd_en_w2e_wsti", 1)
        self.strm_rd_addr_w2e_wsti = self.input(
            "strm_rd_addr_w2e_wsti", self._params.glb_addr_width)
        self.strm_rd_data_w2e_wsti = self.input(
            "strm_rd_data_w2e_wsti", self._params.bank_data_width)
        self.strm_rd_data_valid_w2e_wsti = self.input(
            "strm_rd_data_valid_w2e_wsti", 1)

        self.strm_wr_en_e2w_wsto = self.output(
            "strm_wr_en_e2w_wsto", 1)
        self.strm_wr_strb_e2w_wsto = self.output(
            "strm_wr_strb_e2w_wsto", self._params.bank_data_width // 8)
        self.strm_wr_addr_e2w_wsto = self.output(
            "strm_wr_addr_e2w_wsto", self._params.glb_addr_width)
        self.strm_wr_data_e2w_wsto = self.output(
            "strm_wr_data_e2w_wsto", self._params.bank_data_width)
        self.strm_rd_en_e2w_wsto = self.output(
            "strm_rd_en_e2w_wsto", 1)
        self.strm_rd_addr_e2w_wsto = self.output(
            "strm_rd_addr_e2w_wsto", self._params.glb_addr_width)
        self.strm_rd_data_e2w_wsto = self.output(
            "strm_rd_data_e2w_wsto", self._params.bank_data_width)
        self.strm_rd_data_valid_e2w_wsto = self.output(
            "strm_rd_data_valid_e2w_wsto", 1)

        self.pcfg_rd_en_e2w_esti = self.input(
            "pcfg_rd_en_e2w_esti", 1)
        self.pcfg_rd_addr_e2w_esti = self.input(
            "pcfg_rd_addr_e2w_esti", self._params.glb_addr_width)
        self.pcfg_rd_data_e2w_esti = self.input(
            "pcfg_rd_data_e2w_esti", self._params.bank_data_width)
        self.pcfg_rd_data_valid_e2w_esti = self.input(
            "pcfg_rd_data_valid_e2w_esti", 1)

        self.pcfg_rd_en_w2e_esto = self.output(
            "pcfg_rd_en_w2e_esto", 1)
        self.pcfg_rd_addr_w2e_esto = self.output(
            "pcfg_rd_addr_w2e_esto", self._params.glb_addr_width)
        self.pcfg_rd_data_w2e_esto = self.output(
            "pcfg_rd_data_w2e_esto", self._params.bank_data_width)
        self.pcfg_rd_data_valid_w2e_esto = self.output(
            "pcfg_rd_data_valid_w2e_esto", 1)

        self.pcfg_rd_en_w2e_wsti = self.input(
            "pcfg_rd_en_w2e_wsti", 1)
        self.pcfg_rd_addr_w2e_wsti = self.input(
            "pcfg_rd_addr_w2e_wsti", self._params.glb_addr_width)
        self.pcfg_rd_data_w2e_wsti = self.input(
            "pcfg_rd_data_w2e_wsti", self._params.bank_data_width)
        self.pcfg_rd_data_valid_w2e_wsti = self.input(
            "pcfg_rd_data_valid_w2e_wsti", 1)

        self.pcfg_rd_en_e2w_wsto = self.output(
            "pcfg_rd_en_e2w_wsto", 1)
        self.pcfg_rd_addr_e2w_wsto = self.output(
            "pcfg_rd_addr_e2w_wsto", self._params.glb_addr_width)
        self.pcfg_rd_data_e2w_wsto = self.output(
            "pcfg_rd_data_e2w_wsto", self._params.bank_data_width)
        self.pcfg_rd_data_valid_e2w_wsto = self.output(
            "pcfg_rd_data_valid_e2w_wsto", 1)

        self.if_cfg_est_m_wr_en = self.output(
            "if_cfg_est_m_wr_en", 1)
        self.if_cfg_est_m_wr_addr = self.output(
            "if_cfg_est_m_wr_addr", self._params.axi_addr_width)
        self.if_cfg_est_m_wr_data = self.output(
            "if_cfg_est_m_wr_data", self._params.axi_data_width)
        self.if_cfg_est_m_rd_en = self.output(
            "if_cfg_est_m_rd_en", 1)
        self.if_cfg_est_m_rd_addr = self.output(
            "if_cfg_est_m_rd_addr", self._params.axi_addr_width)
        self.if_cfg_est_m_rd_data = self.input(
            "if_cfg_est_m_rd_data", self._params.axi_data_width)
        self.if_cfg_est_m_rd_data_valid = self.input(
            "if_cfg_est_m_rd_data_valid", 1)

        self.if_cfg_wst_s_wr_en = self.input(
            "if_cfg_wst_s_wr_en", 1)
        self.if_cfg_wst_s_wr_addr = self.input(
            "if_cfg_wst_s_wr_addr", self._params.axi_addr_width)
        self.if_cfg_wst_s_wr_data = self.input(
            "if_cfg_wst_s_wr_data", self._params.axi_data_width)
        self.if_cfg_wst_s_rd_en = self.input(
            "if_cfg_wst_s_rd_en", 1)
        self.if_cfg_wst_s_rd_addr = self.input(
            "if_cfg_wst_s_rd_addr", self._params.axi_addr_width)
        self.if_cfg_wst_s_rd_data = self.output(
            "if_cfg_wst_s_rd_data", self._params.axi_data_width)
        self.if_cfg_wst_s_rd_data_valid = self.output(
            "if_cfg_wst_s_rd_data_valid", 1)

        self.if_sram_cfg_est_m_wr_en = self.output(
            "if_sram_cfg_est_m_wr_en", 1)
        self.if_sram_cfg_est_m_wr_addr = self.output(
            "if_sram_cfg_est_m_wr_addr", self._params.glb_addr_width)
        self.if_sram_cfg_est_m_wr_data = self.output(
            "if_sram_cfg_est_m_wr_data", self._params.axi_data_width)
        self.if_sram_cfg_est_m_rd_en = self.output(
            "if_sram_cfg_est_m_rd_en", 1)
        self.if_sram_cfg_est_m_rd_addr = self.output(
            "if_sram_cfg_est_m_rd_addr", self._params.glb_addr_width)
        self.if_sram_cfg_est_m_rd_data = self.input(
            "if_sram_cfg_est_m_rd_data", self._params.axi_data_width)
        self.if_sram_cfg_est_m_rd_data_valid = self.input(
            "if_sram_cfg_est_m_rd_data_valid", 1)

        self.if_sram_cfg_wst_s_wr_en = self.input(
            "if_sram_cfg_wst_s_wr_en", 1)
        self.if_sram_cfg_wst_s_wr_addr = self.input(
            "if_sram_cfg_wst_s_wr_addr", self._params.glb_addr_width)
        self.if_sram_cfg_wst_s_wr_data = self.input(
            "if_sram_cfg_wst_s_wr_data", self._params.axi_data_width)
        self.if_sram_cfg_wst_s_rd_en = self.input(
            "if_sram_cfg_wst_s_rd_en", 1)
        self.if_sram_cfg_wst_s_rd_addr = self.input(
            "if_sram_cfg_wst_s_rd_addr", self._params.glb_addr_width)
        self.if_sram_cfg_wst_s_rd_data = self.output(
            "if_sram_cfg_wst_s_rd_data", self._params.axi_data_width)
        self.if_sram_cfg_wst_s_rd_data_valid = self.output(
            "if_sram_cfg_wst_s_rd_data_valid", 1)

        self.cfg_tile_connected_wsti = self.input(
            "cfg_tile_connected_wsti", 1)
        self.cfg_tile_connected_esto = self.output(
            "cfg_tile_connected_esto", 1)
        self.cfg_pcfg_tile_connected_wsti = self.input(
            "cfg_pcfg_tile_connected_wsti", 1)
        self.cfg_pcfg_tile_connected_esto = self.output(
            "cfg_pcfg_tile_connected_esto", 1)

        self.cgra_cfg_jtag_wsti_wr_en = self.input(
            "cgra_cfg_jtag_wsti_wr_en", 1)
        self.cgra_cfg_jtag_wsti_rd_en = self.input(
            "cgra_cfg_jtag_wsti_rd_en", 1)
        self.cgra_cfg_jtag_wsti_addr = self.input(
            "cgra_cfg_jtag_wsti_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_wsti_data = self.input(
            "cgra_cfg_jtag_wsti_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_jtag_esto_wr_en = self.output(
            "cgra_cfg_jtag_esto_wr_en", 1)
        self.cgra_cfg_jtag_esto_rd_en = self.output(
            "cgra_cfg_jtag_esto_rd_en", 1)
        self.cgra_cfg_jtag_esto_addr = self.output(
            "cgra_cfg_jtag_esto_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_esto_data = self.output(
            "cgra_cfg_jtag_esto_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_jtag_wsti_rd_en_bypass = self.input(
            "cgra_cfg_jtag_wsti_rd_en_bypass", 1)
        self.cgra_cfg_jtag_wsti_addr_bypass = self.input(
            "cgra_cfg_jtag_wsti_addr_bypass", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_esto_rd_en_bypass = self.output(
            "cgra_cfg_jtag_esto_rd_en_bypass", 1)
        self.cgra_cfg_jtag_esto_addr_bypass = self.output(
            "cgra_cfg_jtag_esto_addr_bypass", self._params.cgra_cfg_addr_width)

        self.cgra_cfg_pcfg_wsti_wr_en = self.input(
            "cgra_cfg_pcfg_wsti_wr_en", 1)
        self.cgra_cfg_pcfg_wsti_rd_en = self.input(
            "cgra_cfg_pcfg_wsti_rd_en", 1)
        self.cgra_cfg_pcfg_wsti_addr = self.input(
            "cgra_cfg_pcfg_wsti_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_wsti_data = self.input(
            "cgra_cfg_pcfg_wsti_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_pcfg_esto_wr_en = self.output(
            "cgra_cfg_pcfg_esto_wr_en", 1)
        self.cgra_cfg_pcfg_esto_rd_en = self.output(
            "cgra_cfg_pcfg_esto_rd_en", 1)
        self.cgra_cfg_pcfg_esto_addr = self.output(
            "cgra_cfg_pcfg_esto_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_esto_data = self.output(
            "cgra_cfg_pcfg_esto_data", self._params.cgra_cfg_data_width)

        self.stream_data_f2g = self.input(
            "stream_data_f2g", self._params.cgra_data_width, size=self._params.cgra_per_glb, packed=True)
        self.stream_data_valid_f2g = self.input(
            "stream_data_valid_f2g", 1, size=self._params.cgra_per_glb, packed=True)
        self.stream_data_g2f = self.output(
            "stream_data_g2f", self._params.cgra_data_width, size=self._params.cgra_per_glb, packed=True)
        self.stream_data_valid_g2f = self.output(
            "stream_data_valid_g2f", 1, size=self._params.cgra_per_glb, packed=True)

        self.cgra_cfg_g2f_cfg_wr_en = self.output(
            "cgra_cfg_g2f_cfg_wr_en", 1, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_rd_en = self.output(
            "cgra_cfg_g2f_cfg_rd_en", 1, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_addr = self.output(
            "cgra_cfg_g2f_cfg_addr", self._params.cgra_cfg_addr_width, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_data = self.output(
            "cgra_cfg_g2f_cfg_data", self._params.cgra_cfg_data_width, size=self._params.cgra_per_glb, packed=True)

        self.strm_start_pulse = self.input(
            "strm_start_pulse", 1)
        self.pcfg_start_pulse = self.input(
            "pcfg_start_pulse", 1)
        self.strm_f2g_interrupt_pulse = self.output(
            "strm_f2g_interrupt_pulse", 1)
        self.strm_g2f_interrupt_pulse = self.output(
            "strm_g2f_interrupt_pulse", 1)
        self.pcfg_g2f_interrupt_pulse = self.output(
            "pcfg_g2f_interrupt_pulse", 1)

        self.if_cfg = GlbConfigInterface(
            addr_width=self._params.axi_addr_width, data_width=self._params.axi_data_width)
        self.if_sram_cfg = GlbConfigInterface(
            addr_width=self._params.glb_addr_width, data_width=self._params.axi_data_width)

        self.if_cfg_est_m = self.interface(self.if_cfg, "if_cfg_est_m")
        self.if_cfg_wst_s = self.interface(self.if_cfg, "if_cfg_wst_s")
        self.if_sram_cfg_est_m = self.interface(
            self.if_sram_cfg, "if_sram_cfg_est_m")
        self.if_sram_cfg_wst_s = self.interface(
            self.if_sram_cfg, "if_sram_cfg_wst_s")

        self.glb_tile_cfg = GlbTileCfg(_params=self._params)
        self.add_child("glb_tile_cfg",
                       self.glb_tile_cfg,
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id)
        self.glb_tile_pcfg_switch = GlbTilePcfgSwitch(_params=self._params)
        self.add_child("glb_tile_pcfg_switch",
                       self.glb_tile_pcfg_switch,
                       clk=self.clk,
                       reset=self.reset)
        self.glb_core = GlbCore(_params=self._params)
        self.add_child("glb_core",
                       self.glb_core,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id)

        self.interface_wiring()
        self.tile2cfg_wiring()
        self.tile2core_wiring()
        self.tile2pcfgs_wiring()
        self.cfg2core_wiring()
        self.core2pcfgs_wiring()

    def interface_wiring(self):
        self.wire(self.if_cfg_est_m.wr_en, self.if_cfg_est_m_wr_en)
        self.wire(self.if_cfg_est_m.wr_addr, self.if_cfg_est_m_wr_addr)
        self.wire(self.if_cfg_est_m.wr_data, self.if_cfg_est_m_wr_data)
        self.wire(self.if_cfg_est_m.rd_en, self.if_cfg_est_m_rd_en)
        self.wire(self.if_cfg_est_m.rd_addr, self.if_cfg_est_m_rd_addr)
        self.wire(self.if_cfg_est_m.rd_data, self.if_cfg_est_m_rd_data)
        self.wire(self.if_cfg_est_m.rd_data_valid,
                  self.if_cfg_est_m_rd_data_valid)

        self.wire(self.if_cfg_wst_s.wr_en, self.if_cfg_wst_s_wr_en)
        self.wire(self.if_cfg_wst_s.wr_addr, self.if_cfg_wst_s_wr_addr)
        self.wire(self.if_cfg_wst_s.wr_data, self.if_cfg_wst_s_wr_data)
        self.wire(self.if_cfg_wst_s.rd_en, self.if_cfg_wst_s_rd_en)
        self.wire(self.if_cfg_wst_s.rd_addr, self.if_cfg_wst_s_rd_addr)
        self.wire(self.if_cfg_wst_s.rd_data, self.if_cfg_wst_s_rd_data)
        self.wire(self.if_cfg_wst_s.rd_data_valid,
                  self.if_cfg_wst_s_rd_data_valid)

        self.wire(self.if_sram_cfg_est_m.wr_en, self.if_sram_cfg_est_m_wr_en)
        self.wire(self.if_sram_cfg_est_m.wr_addr,
                  self.if_sram_cfg_est_m_wr_addr)
        self.wire(self.if_sram_cfg_est_m.wr_data,
                  self.if_sram_cfg_est_m_wr_data)
        self.wire(self.if_sram_cfg_est_m.rd_en, self.if_sram_cfg_est_m_rd_en)
        self.wire(self.if_sram_cfg_est_m.rd_addr,
                  self.if_sram_cfg_est_m_rd_addr)
        self.wire(self.if_sram_cfg_est_m.rd_data,
                  self.if_sram_cfg_est_m_rd_data)
        self.wire(self.if_sram_cfg_est_m.rd_data_valid,
                  self.if_sram_cfg_est_m_rd_data_valid)

        self.wire(self.if_sram_cfg_wst_s.wr_en, self.if_sram_cfg_wst_s_wr_en)
        self.wire(self.if_sram_cfg_wst_s.wr_addr,
                  self.if_sram_cfg_wst_s_wr_addr)
        self.wire(self.if_sram_cfg_wst_s.wr_data,
                  self.if_sram_cfg_wst_s_wr_data)
        self.wire(self.if_sram_cfg_wst_s.rd_en, self.if_sram_cfg_wst_s_rd_en)
        self.wire(self.if_sram_cfg_wst_s.rd_addr,
                  self.if_sram_cfg_wst_s_rd_addr)
        self.wire(self.if_sram_cfg_wst_s.rd_data,
                  self.if_sram_cfg_wst_s_rd_data)
        self.wire(self.if_sram_cfg_wst_s.rd_data_valid,
                  self.if_sram_cfg_wst_s_rd_data_valid)

    def tile2cfg_wiring(self):
        self.wire(self.glb_tile_cfg.if_cfg_wst_s, self.if_cfg_wst_s)
        self.wire(self.glb_tile_cfg.if_cfg_est_m, self.if_cfg_est_m)

    def tile2core_wiring(self):
        self.wire(self.glb_core.if_sram_cfg_wst_s, self.if_sram_cfg_wst_s)
        self.wire(self.glb_core.if_sram_cfg_est_m, self.if_sram_cfg_est_m)

        self.wire(
            self.glb_core.proc_packet_w2e_wsti['wr_en'], self.proc_wr_en_w2e_wsti)
        self.wire(
            self.glb_core.proc_packet_w2e_wsti['wr_addr'], self.proc_wr_addr_w2e_wsti)
        self.wire(
            self.glb_core.proc_packet_w2e_wsti['wr_strb'], self.proc_wr_strb_w2e_wsti)
        self.wire(
            self.glb_core.proc_packet_w2e_wsti['wr_data'], self.proc_wr_data_w2e_wsti)
        self.wire(
            self.glb_core.proc_packet_w2e_wsti['rd_en'], self.proc_rd_en_w2e_wsti)
        self.wire(
            self.glb_core.proc_packet_w2e_wsti['rd_addr'], self.proc_rd_addr_w2e_wsti)
        self.wire(
            self.glb_core.proc_packet_w2e_wsti['rd_data'], self.proc_rd_data_w2e_wsti)
        self.wire(
            self.glb_core.proc_packet_w2e_wsti['rd_data_valid'], self.proc_rd_data_valid_w2e_wsti)

        self.wire(
            self.glb_core.proc_packet_e2w_wsto['wr_en'], self.proc_wr_en_e2w_wsto)
        self.wire(
            self.glb_core.proc_packet_e2w_wsto['wr_addr'], self.proc_wr_addr_e2w_wsto)
        self.wire(
            self.glb_core.proc_packet_e2w_wsto['wr_strb'], self.proc_wr_strb_e2w_wsto)
        self.wire(
            self.glb_core.proc_packet_e2w_wsto['wr_data'], self.proc_wr_data_e2w_wsto)
        self.wire(
            self.glb_core.proc_packet_e2w_wsto['rd_en'], self.proc_rd_en_e2w_wsto)
        self.wire(
            self.glb_core.proc_packet_e2w_wsto['rd_addr'], self.proc_rd_addr_e2w_wsto)
        self.wire(
            self.glb_core.proc_packet_e2w_wsto['rd_data'], self.proc_rd_data_e2w_wsto)
        self.wire(
            self.glb_core.proc_packet_e2w_wsto['rd_data_valid'], self.proc_rd_data_valid_e2w_wsto)

        self.wire(
            self.glb_core.proc_packet_e2w_esti['wr_en'], self.proc_wr_en_e2w_esti)
        self.wire(
            self.glb_core.proc_packet_e2w_esti['wr_addr'], self.proc_wr_addr_e2w_esti)
        self.wire(
            self.glb_core.proc_packet_e2w_esti['wr_strb'], self.proc_wr_strb_e2w_esti)
        self.wire(
            self.glb_core.proc_packet_e2w_esti['wr_data'], self.proc_wr_data_e2w_esti)
        self.wire(
            self.glb_core.proc_packet_e2w_esti['rd_en'], self.proc_rd_en_e2w_esti)
        self.wire(
            self.glb_core.proc_packet_e2w_esti['rd_addr'], self.proc_rd_addr_e2w_esti)
        self.wire(
            self.glb_core.proc_packet_e2w_esti['rd_data'], self.proc_rd_data_e2w_esti)
        self.wire(
            self.glb_core.proc_packet_e2w_esti['rd_data_valid'], self.proc_rd_data_valid_e2w_esti)

        self.wire(
            self.glb_core.proc_packet_w2e_esto['wr_en'], self.proc_wr_en_w2e_esto)
        self.wire(
            self.glb_core.proc_packet_w2e_esto['wr_addr'], self.proc_wr_addr_w2e_esto)
        self.wire(
            self.glb_core.proc_packet_w2e_esto['wr_strb'], self.proc_wr_strb_w2e_esto)
        self.wire(
            self.glb_core.proc_packet_w2e_esto['wr_data'], self.proc_wr_data_w2e_esto)
        self.wire(
            self.glb_core.proc_packet_w2e_esto['rd_en'], self.proc_rd_en_w2e_esto)
        self.wire(
            self.glb_core.proc_packet_w2e_esto['rd_addr'], self.proc_rd_addr_w2e_esto)
        self.wire(
            self.glb_core.proc_packet_w2e_esto['rd_data'], self.proc_rd_data_w2e_esto)
        self.wire(
            self.glb_core.proc_packet_w2e_esto['rd_data_valid'], self.proc_rd_data_valid_w2e_esto)

        self.wire(
            self.glb_core.strm_packet_w2e_wsti['wr_en'], self.strm_wr_en_w2e_wsti)
        self.wire(
            self.glb_core.strm_packet_w2e_wsti['wr_addr'], self.strm_wr_addr_w2e_wsti)
        self.wire(
            self.glb_core.strm_packet_w2e_wsti['wr_strb'], self.strm_wr_strb_w2e_wsti)
        self.wire(
            self.glb_core.strm_packet_w2e_wsti['wr_data'], self.strm_wr_data_w2e_wsti)
        self.wire(
            self.glb_core.strm_packet_w2e_wsti['rd_en'], self.strm_rd_en_w2e_wsti)
        self.wire(
            self.glb_core.strm_packet_w2e_wsti['rd_addr'], self.strm_rd_addr_w2e_wsti)
        self.wire(
            self.glb_core.strm_packet_w2e_wsti['rd_data'], self.strm_rd_data_w2e_wsti)
        self.wire(
            self.glb_core.strm_packet_w2e_wsti['rd_data_valid'], self.strm_rd_data_valid_w2e_wsti)

        self.wire(
            self.glb_core.strm_packet_e2w_wsto['wr_en'], self.strm_wr_en_e2w_wsto)
        self.wire(
            self.glb_core.strm_packet_e2w_wsto['wr_addr'], self.strm_wr_addr_e2w_wsto)
        self.wire(
            self.glb_core.strm_packet_e2w_wsto['wr_strb'], self.strm_wr_strb_e2w_wsto)
        self.wire(
            self.glb_core.strm_packet_e2w_wsto['wr_data'], self.strm_wr_data_e2w_wsto)
        self.wire(
            self.glb_core.strm_packet_e2w_wsto['rd_en'], self.strm_rd_en_e2w_wsto)
        self.wire(
            self.glb_core.strm_packet_e2w_wsto['rd_addr'], self.strm_rd_addr_e2w_wsto)
        self.wire(
            self.glb_core.strm_packet_e2w_wsto['rd_data'], self.strm_rd_data_e2w_wsto)
        self.wire(
            self.glb_core.strm_packet_e2w_wsto['rd_data_valid'], self.strm_rd_data_valid_e2w_wsto)

        self.wire(
            self.glb_core.strm_packet_e2w_esti['wr_en'], self.strm_wr_en_e2w_esti)
        self.wire(
            self.glb_core.strm_packet_e2w_esti['wr_addr'], self.strm_wr_addr_e2w_esti)
        self.wire(
            self.glb_core.strm_packet_e2w_esti['wr_strb'], self.strm_wr_strb_e2w_esti)
        self.wire(
            self.glb_core.strm_packet_e2w_esti['wr_data'], self.strm_wr_data_e2w_esti)
        self.wire(
            self.glb_core.strm_packet_e2w_esti['rd_en'], self.strm_rd_en_e2w_esti)
        self.wire(
            self.glb_core.strm_packet_e2w_esti['rd_addr'], self.strm_rd_addr_e2w_esti)
        self.wire(
            self.glb_core.strm_packet_e2w_esti['rd_data'], self.strm_rd_data_e2w_esti)
        self.wire(
            self.glb_core.strm_packet_e2w_esti['rd_data_valid'], self.strm_rd_data_valid_e2w_esti)

        self.wire(
            self.glb_core.strm_packet_w2e_esto['wr_en'], self.strm_wr_en_w2e_esto)
        self.wire(
            self.glb_core.strm_packet_w2e_esto['wr_addr'], self.strm_wr_addr_w2e_esto)
        self.wire(
            self.glb_core.strm_packet_w2e_esto['wr_strb'], self.strm_wr_strb_w2e_esto)
        self.wire(
            self.glb_core.strm_packet_w2e_esto['wr_data'], self.strm_wr_data_w2e_esto)
        self.wire(
            self.glb_core.strm_packet_w2e_esto['rd_en'], self.strm_rd_en_w2e_esto)
        self.wire(
            self.glb_core.strm_packet_w2e_esto['rd_addr'], self.strm_rd_addr_w2e_esto)
        self.wire(
            self.glb_core.strm_packet_w2e_esto['rd_data'], self.strm_rd_data_w2e_esto)
        self.wire(
            self.glb_core.strm_packet_w2e_esto['rd_data_valid'], self.strm_rd_data_valid_w2e_esto)

        self.wire(
            self.glb_core.pcfg_packet_w2e_wsti['rd_en'], self.pcfg_rd_en_w2e_wsti)
        self.wire(
            self.glb_core.pcfg_packet_w2e_wsti['rd_addr'], self.pcfg_rd_addr_w2e_wsti)
        self.wire(
            self.glb_core.pcfg_packet_w2e_wsti['rd_data'], self.pcfg_rd_data_w2e_wsti)
        self.wire(
            self.glb_core.pcfg_packet_w2e_wsti['rd_data_valid'], self.pcfg_rd_data_valid_w2e_wsti)

        self.wire(
            self.glb_core.pcfg_packet_e2w_wsto['rd_en'], self.pcfg_rd_en_e2w_wsto)
        self.wire(
            self.glb_core.pcfg_packet_e2w_wsto['rd_addr'], self.pcfg_rd_addr_e2w_wsto)
        self.wire(
            self.glb_core.pcfg_packet_e2w_wsto['rd_data'], self.pcfg_rd_data_e2w_wsto)
        self.wire(
            self.glb_core.pcfg_packet_e2w_wsto['rd_data_valid'], self.pcfg_rd_data_valid_e2w_wsto)

        self.wire(
            self.glb_core.pcfg_packet_e2w_esti['rd_en'], self.pcfg_rd_en_e2w_esti)
        self.wire(
            self.glb_core.pcfg_packet_e2w_esti['rd_addr'], self.pcfg_rd_addr_e2w_esti)
        self.wire(
            self.glb_core.pcfg_packet_e2w_esti['rd_data'], self.pcfg_rd_data_e2w_esti)
        self.wire(
            self.glb_core.pcfg_packet_e2w_esti['rd_data_valid'], self.pcfg_rd_data_valid_e2w_esti)

        self.wire(
            self.glb_core.pcfg_packet_w2e_esto['rd_en'], self.pcfg_rd_en_w2e_esto)
        self.wire(
            self.glb_core.pcfg_packet_w2e_esto['rd_addr'], self.pcfg_rd_addr_w2e_esto)
        self.wire(
            self.glb_core.pcfg_packet_w2e_esto['rd_data'], self.pcfg_rd_data_w2e_esto)
        self.wire(
            self.glb_core.pcfg_packet_w2e_esto['rd_data_valid'], self.pcfg_rd_data_valid_w2e_esto)

        self.wire(self.glb_core.strm_data_valid_f2g,
                  self.stream_data_valid_f2g)
        self.wire(self.glb_core.strm_data_valid_g2f,
                  self.stream_data_valid_g2f)
        self.wire(self.glb_core.strm_data_f2g, self.stream_data_f2g)
        self.wire(self.glb_core.strm_data_g2f, self.stream_data_g2f)

        self.wire(self.cfg_tile_connected_esto,
                  self.glb_tile_cfg.cfg_data_network['tile_connected'])
        self.wire(self.cfg_pcfg_tile_connected_esto,
                  self.glb_tile_cfg.cfg_pcfg_network['tile_connected'])
        self.wire(self.glb_core.cfg_data_network_connected_prev,
                  self.cfg_tile_connected_wsti)
        self.wire(self.glb_core.cfg_pcfg_network_connected_prev,
                  self.cfg_pcfg_tile_connected_wsti)

        self.wire(self.glb_core.ld_dma_start_pulse, self.strm_start_pulse)
        self.wire(self.glb_core.pcfg_start_pulse, self.pcfg_start_pulse)
        self.wire(self.glb_core.ld_dma_done_pulse,
                  self.strm_g2f_interrupt_pulse)
        self.wire(self.glb_core.st_dma_done_pulse,
                  self.strm_f2g_interrupt_pulse)
        self.wire(self.glb_core.pcfg_done_pulse, self.pcfg_g2f_interrupt_pulse)

    def cfg2core_wiring(self):
        self.wire(self.glb_core.cfg_data_network,
                  self.glb_tile_cfg.cfg_data_network)
        self.wire(self.glb_core.cfg_pcfg_network,
                  self.glb_tile_cfg.cfg_pcfg_network)

        self.wire(self.glb_core.cfg_st_dma_ctrl,
                  self.glb_tile_cfg.cfg_st_dma_ctrl)
        st_dma_header_w = self.var(
            "st_dma_header_w", self.header.cfg_st_dma_header_t, size=self._params.queue_depth)
        self.wire(st_dma_header_w, self.glb_tile_cfg.cfg_st_dma_header)
        self.wire(self.glb_core.cfg_st_dma_header, st_dma_header_w)
        self.wire(self.glb_core.st_dma_header_clr,
                  self.glb_tile_cfg.st_dma_header_clr)
        self.wire(self.glb_core.cfg_ld_dma_ctrl,
                  self.glb_tile_cfg.cfg_ld_dma_ctrl)

        # HACK
        ld_dma_header_w = self.var(
            "ld_dma_header_w", self.header.cfg_ld_dma_header_t, size=self._params.queue_depth)
        self.wire(self.glb_core.cfg_ld_dma_header, ld_dma_header_w)
        self.wire(ld_dma_header_w, self.glb_tile_cfg.cfg_ld_dma_header)

        self.wire(self.glb_core.ld_dma_header_clr,
                  self.glb_tile_cfg.ld_dma_header_clr)

        self.wire(self.glb_core.cfg_pcfg_dma_ctrl,
                  self.glb_tile_cfg.cfg_pcfg_dma_ctrl)
        self.wire(self.glb_core.cfg_pcfg_dma_header,
                  self.glb_tile_cfg.cfg_pcfg_dma_header)

    def core2pcfgs_wiring(self):
        self.wire(self.glb_core.cgra_cfg_pcfg,
                  self.glb_tile_pcfg_switch.cgra_cfg_core2sw)
        self.wire(
            self.glb_tile_cfg.cfg_pcfg_dma_ctrl['mode'], self.glb_tile_pcfg_switch.cfg_pcfg_dma_mode)

    def tile2pcfgs_wiring(self):
        cgra_cfg_g2f_w = self.var(
            f"cgra_cfg_g2f_cfg_w", self.header.cgra_cfg_t, size=self._params.cgra_per_glb, packed=True)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_g2f, cgra_cfg_g2f_w)
        for i in range(self._params.cgra_per_glb):
            self.wire(cgra_cfg_g2f_w[i]['wr_en'],
                      self.cgra_cfg_g2f_cfg_wr_en[i])
            self.wire(cgra_cfg_g2f_w[i]['rd_en'],
                      self.cgra_cfg_g2f_cfg_rd_en[i])
            self.wire(cgra_cfg_g2f_w[i]['addr'], self.cgra_cfg_g2f_cfg_addr[i])
            self.wire(cgra_cfg_g2f_w[i]['data'], self.cgra_cfg_g2f_cfg_data[i])

        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['wr_en'], self.cgra_cfg_jtag_wsti_wr_en)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['rd_en'], self.cgra_cfg_jtag_wsti_rd_en)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['addr'], self.cgra_cfg_jtag_wsti_addr)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['data'], self.cgra_cfg_jtag_wsti_data)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['wr_en'], self.cgra_cfg_jtag_esto_wr_en)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['rd_en'], self.cgra_cfg_jtag_esto_rd_en)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['addr'], self.cgra_cfg_jtag_esto_addr)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['data'], self.cgra_cfg_jtag_esto_data)

        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['wr_en'], self.cgra_cfg_pcfg_wsti_wr_en)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['rd_en'], self.cgra_cfg_pcfg_wsti_rd_en)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['addr'], self.cgra_cfg_pcfg_wsti_addr)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['data'], self.cgra_cfg_pcfg_wsti_data)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['wr_en'], self.cgra_cfg_pcfg_esto_wr_en)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['rd_en'], self.cgra_cfg_pcfg_esto_rd_en)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['addr'], self.cgra_cfg_pcfg_esto_addr)
        self.wire(
            self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['data'], self.cgra_cfg_pcfg_esto_data)

        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti_rd_en_bypass,
                  self.cgra_cfg_jtag_wsti_rd_en_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto_rd_en_bypass,
                  self.cgra_cfg_jtag_esto_rd_en_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti_addr_bypass,
                  self.cgra_cfg_jtag_wsti_addr_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto_addr_bypass,
                  self.cgra_cfg_jtag_esto_addr_bypass)
