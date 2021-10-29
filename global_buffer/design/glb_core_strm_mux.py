from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbCoreStrmMux(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_core_strm_mux")
        self._params = _params

        self.clk = self.clock("clk")
        self.clk_en = self.input("clk_en", 1)
        self.reset = self.reset("reset")

        self.data_g2f_dma = self.input(
            "data_g2f_dma", width=self._params.cgra_data_width)
        self.data_valid_g2f_dma = self.input(
            "data_valid_g2f_dma", width=1)
        self.data_g2f = self.output(
            "data_g2f", width=self._params.cgra_data_width, size=self._params.cgra_per_glb)
        self.data_valid_g2f = self.output(
            "data_valid_g2f", self._params.cgra_per_glb)

        self.data_f2g_dma = self.output(
            "data_f2g_dma", width=self._params.cgra_data_width)
        self.data_valid_f2g_dma = self.output(
            "data_valid_f2g_dma", width=1)
        self.data_f2g = self.input(
            "data_f2g", width=self._params.cgra_data_width, size=self._params.cgra_per_glb)
        self.data_valid_f2g = self.input(
            "data_valid_f2g", self._params.cgra_per_glb)

        self.cfg_data_network_g2f_mux = self.input(
            "cfg_data_network_g2f_mux", self._params.cgra_per_glb)
        self.cfg_data_network_f2g_mux = self.input(
            "cfg_data_network_f2g_mux", self._params.cgra_per_glb)

        # local variables
        self.data_g2f_int = self.var(
            "data_g2f_int", width=self._params.cgra_data_width, size=self._params.cgra_per_glb)
        self.data_valid_g2f_int = self.var(
            "data_valid_g2f_int", self._params.cgra_per_glb)

        self.add_always(self.pipeline)
        self.add_always(self.data_g2f_logic)
        self.add_always(self.data_f2g_logic)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline(self):
        if self.reset:
            for i in range(self._params.cgra_per_glb):
                self.data_g2f[i] = 0
                self.data_valid_g2f[i] = 0
        elif self.clk_en:
            for i in range(self._params.cgra_per_glb):
                self.data_g2f[i] = self.data_g2f_int[i]
                self.data_valid_g2f[i] = self.data_valid_g2f_int[i]

    @always_comb
    def data_g2f_logic(self):
        for i in range(self._params.cgra_per_glb):
            if self.cfg_data_network_g2f_mux[i] == 1:
                self.data_g2f_int[i] = self.data_g2f_dma
                self.data_valid_g2f_int[i] = self.data_valid_g2f_dma
            else:
                self.data_g2f_int[i] = 0
                self.data_valid_g2f_int[i] = 0

    @always_comb
    def data_f2g_logic(self):
        self.data_f2g_dma = 0
        self.data_valid_f2g_dma = 0
        for i in range(self._params.cgra_per_glb):
            if self.cfg_data_network_f2g_mux[i] == 1:
                self.data_f2g_dma = self.data_f2g[i]
                self.data_valid_f2g_dma = self.data_valid_f2g[i]
            else:
                self.data_f2g_dma = self.data_f2g_dma
                self.data_valid_f2g_dma = self.data_valid_f2g_dma
