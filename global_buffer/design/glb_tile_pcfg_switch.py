from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbTilePcfgSwitch(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_tile_pcfg_switch")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        self.cfg_pcfg_dma_mode = self.input("cfg_pcfg_dma_mode", 1)
        self.cgra_cfg_core2sw = self.input(
            "cgra_cfg_core2sw", self.header.cgra_cfg_t)
        self.cgra_cfg_jtag_wsti = self.input(
            "cgra_cfg_jtag_wsti", self.header.cgra_cfg_t)
        self.cgra_cfg_jtag_esto = self.output(
            "cgra_cfg_jtag_esto", self.header.cgra_cfg_t)
        self.cgra_cfg_pcfg_wsti = self.input(
            "cgra_cfg_pcfg_wsti", self.header.cgra_cfg_t)
        self.cgra_cfg_pcfg_esto = self.output(
            "cgra_cfg_pcfg_esto", self.header.cgra_cfg_t)
        self.cgra_cfg_g2f = self.output(
            "cgra_cfg_g2f", self.header.cgra_cfg_t, size=self._params.cgra_per_glb)

        self.cgra_cfg_jtag_wsti_rd_en_bypass = self.input(
            "cgra_cfg_jtag_wsti_rd_en_bypass", 1)
        self.cgra_cfg_jtag_wsti_addr_bypass = self.input(
            "cgra_cfg_jtag_wsti_addr_bypass", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_esto_rd_en_bypass = self.output(
            "cgra_cfg_jtag_esto_rd_en_bypass", 1)
        self.cgra_cfg_jtag_esto_addr_bypass = self.output(
            "cgra_cfg_jtag_esto_addr_bypass", self._params.cgra_cfg_addr_width)

        self.is_stub = True
