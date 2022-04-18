from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbPcfgBroadcast(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_pcfg_broadcast")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        self.cgra_cfg_dma2mux = self.input("cgra_cfg_dma2mux", self.header.cgra_cfg_t)
        self.cgra_cfg_pcfg_wsti = self.input("cgra_cfg_pcfg_wsti", self.header.cgra_cfg_t)
        self.cgra_cfg_pcfg_esto = self.output("cgra_cfg_pcfg_esto", self.header.cgra_cfg_t)
        self.cgra_cfg_pcfg_esti = self.input("cgra_cfg_pcfg_esti", self.header.cgra_cfg_t)
        self.cgra_cfg_pcfg_wsto = self.output("cgra_cfg_pcfg_wsto", self.header.cgra_cfg_t)
        self.cgra_cfg_g2f = self.output("cgra_cfg_g2f", self.header.cgra_cfg_t, size=self._params.cgra_per_glb)

        self.cgra_cfg_jtag_wsti = self.input("cgra_cfg_jtag_wsti", self.header.cgra_cfg_t)
        self.cgra_cfg_jtag_esto = self.output("cgra_cfg_jtag_esto", self.header.cgra_cfg_t)

        self.cgra_cfg_jtag_rd_en_bypass_wsti = self.input("cgra_cfg_jtag_rd_en_bypass_wsti", 1)
        self.cgra_cfg_jtag_addr_bypass_wsti = self.input("cgra_cfg_jtag_addr_bypass_wsti",
                                                         self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_rd_en_bypass_esto = self.output("cgra_cfg_jtag_rd_en_bypass_esto", 1)
        self.cgra_cfg_jtag_addr_bypass_esto = self.output("cgra_cfg_jtag_addr_bypass_esto",
                                                          self._params.cgra_cfg_addr_width)
        self.cfg_pcfg_broadcast_mux = self.input("cfg_pcfg_broadcast_mux", self.header.cfg_pcfg_broadcast_mux_t)

        # local variables
        self.pcfg_south_muxed = self.var("pcfg_south_muxed", self.header.cgra_cfg_t)
        self.pcfg_east_muxed = self.var("pcfg_east_muxed", self.header.cgra_cfg_t)
        self.pcfg_west_muxed = self.var("pcfg_west_muxed", self.header.cgra_cfg_t)

        self.cgra_cfg_g2f_w = self.var("cgra_cfg_g2f_w", self.header.cgra_cfg_t,
                                       size=self._params.cgra_per_glb, packed=True)

        self.add_always(self.bypass_logic)
        self.add_always(self.pcfg_south_mux)
        self.add_always(self.pcfg_west_mux)
        self.add_always(self.pcfg_east_mux)

        self.add_always(self.jtag_pipeline)
        self.add_always(self.pcfg_pipeline)

        for i in range(self._params.cgra_per_glb):
            self.add_always(self.cgra_cfg_g2f_mux, i=i)
        self.add_always(self.pipeline_cgra_cfg_g2f)

    @always_comb
    def bypass_logic(self):
        self.cgra_cfg_jtag_rd_en_bypass_esto = self.cgra_cfg_jtag_rd_en_bypass_wsti
        self.cgra_cfg_jtag_addr_bypass_esto = self.cgra_cfg_jtag_addr_bypass_wsti

    @always_comb
    def pcfg_south_mux(self):
        if self.cfg_pcfg_broadcast_mux['south'] == 0:
            self.pcfg_south_muxed = 0
        elif self.cfg_pcfg_broadcast_mux['south'] == 1:
            self.pcfg_south_muxed = self.cgra_cfg_dma2mux
        elif self.cfg_pcfg_broadcast_mux['south'] == 2:
            self.pcfg_south_muxed = self.cgra_cfg_pcfg_wsti
        elif self.cfg_pcfg_broadcast_mux['south'] == 3:
            self.pcfg_south_muxed = self.cgra_cfg_pcfg_esti
        else:
            self.pcfg_south_muxed = 0

    @always_comb
    def pcfg_west_mux(self):
        if self.cfg_pcfg_broadcast_mux['west'] == 0:
            self.pcfg_west_muxed = 0
        elif self.cfg_pcfg_broadcast_mux['west'] == 1:
            self.pcfg_west_muxed = self.cgra_cfg_dma2mux
        elif self.cfg_pcfg_broadcast_mux['west'] == 2:
            self.pcfg_west_muxed = self.cgra_cfg_pcfg_esti
        else:
            self.pcfg_west_muxed = 0

    @always_comb
    def pcfg_east_mux(self):
        if self.cfg_pcfg_broadcast_mux['east'] == 0:
            self.pcfg_east_muxed = 0
        elif self.cfg_pcfg_broadcast_mux['east'] == 1:
            self.pcfg_east_muxed = self.cgra_cfg_dma2mux
        elif self.cfg_pcfg_broadcast_mux['east'] == 2:
            self.pcfg_east_muxed = self.cgra_cfg_pcfg_wsti
        else:
            self.pcfg_east_muxed = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def jtag_pipeline(self):
        if self.reset:
            self.cgra_cfg_jtag_esto = 0
        else:
            self.cgra_cfg_jtag_esto = self.cgra_cfg_jtag_wsti

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pcfg_pipeline(self):
        if self.reset:
            self.cgra_cfg_pcfg_esto = 0
            self.cgra_cfg_pcfg_wsto = 0
        else:
            self.cgra_cfg_pcfg_esto = self.pcfg_east_muxed
            self.cgra_cfg_pcfg_wsto = self.pcfg_west_muxed

    @always_comb
    def cgra_cfg_g2f_mux(self, i):
        if self.cgra_cfg_jtag_rd_en_bypass_esto:
            self.cgra_cfg_g2f_w[i]['wr_en'] = 0
            self.cgra_cfg_g2f_w[i]['rd_en'] = 1
            self.cgra_cfg_g2f_w[i]['addr'] = self.cgra_cfg_jtag_addr_bypass_esto
            self.cgra_cfg_g2f_w[i]['data'] = 0
        else:
            self.cgra_cfg_g2f_w[i] = self.cgra_cfg_jtag_wsti | self.pcfg_south_muxed

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline_cgra_cfg_g2f(self):
        if self.reset:
            for i in range(self._params.cgra_per_glb):
                self.cgra_cfg_g2f[i] = 0
        else:
            for i in range(self._params.cgra_per_glb):
                self.cgra_cfg_g2f[i] = self.cgra_cfg_g2f_w[i]
