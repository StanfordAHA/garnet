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
        self.cgra_cfg_core2sw = self.input("cgra_cfg_core2sw", self.header.cgra_cfg_t)
        self.cgra_cfg_jtag_wsti = self.input("cgra_cfg_jtag_wsti", self.header.cgra_cfg_t)
        self.cgra_cfg_jtag_esto = self.output("cgra_cfg_jtag_esto", self.header.cgra_cfg_t)
        self.cgra_cfg_pcfg_wsti = self.input("cgra_cfg_pcfg_wsti", self.header.cgra_cfg_t)
        self.cgra_cfg_pcfg_esto = self.output("cgra_cfg_pcfg_esto", self.header.cgra_cfg_t)
        self.cgra_cfg_g2f = self.output("cgra_cfg_g2f", self.header.cgra_cfg_t, size=self._params.cgra_per_glb, packed=True)

        self.cgra_cfg_jtag_wsti_rd_en_bypass = self.input("cgra_cfg_jtag_wsti_rd_en_bypass", 1)
        self.cgra_cfg_jtag_wsti_addr_bypass = self.input("cgra_cfg_jtag_wsti_addr_bypass", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_esto_rd_en_bypass = self.output("cgra_cfg_jtag_esto_rd_en_bypass", 1)
        self.cgra_cfg_jtag_esto_addr_bypass = self.output("cgra_cfg_jtag_esto_addr_bypass", self._params.cgra_cfg_addr_width)

        # local variables
        self.cgra_cfg_g2f_w = self.var("cgra_cfg_g2f_w", self.header.cgra_cfg_t, size=self._params.cgra_per_glb)
        self.cgra_cfg_pcfg_muxed = self.var("cgra_cfg_pcfg_muxed", self.header.cgra_cfg_t)

        self.add_always(self.bypass_logic)
        self.add_always(self.cgra_cfg_pcfg_muxed_logic)
        self.add_always(self.pipeline)
        self.add_always(self.cgra_cfg_g2f_logic)
        self.add_always(self.pipeline_cgra_cfg_g2f)

    @always_comb
    def bypass_logic(self):
        self.cgra_cfg_jtag_esto_rd_en_bypass = self.cgra_cfg_jtag_wsti_rd_en_bypass
        self.cgra_cfg_jtag_esto_addr_bypass = self.cgra_cfg_jtag_wsti_addr_bypass

    @always_comb
    def cgra_cfg_pcfg_muxed_logic(self):
        if self.cfg_pcfg_dma_mode == 1:
            self.cgra_cfg_pcfg_muxed = self.cgra_cfg_core2sw
        else:
            self.cgra_cfg_pcfg_muxed = self.cgra_cfg_pcfg_wsti

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline(self):
        if self.reset:
            self.cgra_cfg_jtag_esto = 0
            self.cgra_cfg_pcfg_esto = 0
        else:
            self.cgra_cfg_jtag_esto = self.cgra_cfg_jtag_wsti
            self.cgra_cfg_pcfg_esto = self.cgra_cfg_pcfg_muxed

    @always_comb
    def cgra_cfg_g2f_logic(self):
        for i in range(self._params.cgra_per_glb):
            if self.cgra_cfg_jtag_esto_rd_en_bypass:
                self.cgra_cfg_g2f_w[i]['wr_en'] = 0
                self.cgra_cfg_g2f_w[i]['rd_en'] = 1
                self.cgra_cfg_g2f_w[i]['addr'] = self.cgra_cfg_jtag_esto_addr_bypass
                self.cgra_cfg_g2f_w[i]['data'] = 0
            else:
                self.cgra_cfg_g2f_w[i] = self.cgra_cfg_jtag_esto | self.cgra_cfg_pcfg_esto

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline_cgra_cfg_g2f(self):
        if self.reset:
            for i in range(self._params.cgra_per_glb):
                self.cgra_cfg_g2f[i] = 0
        else:
            for i in range(self._params.cgra_per_glb):
                self.cgra_cfg_g2f[i] = self.cgra_cfg_g2f_w[i]
