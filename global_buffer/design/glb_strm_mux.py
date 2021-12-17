from kratos import Generator, always_comb
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbStrmMux(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_strm_mux")
        self._params = _params
        self.data_g2f_dma = self.input("data_g2f_dma", width=self._params.cgra_data_width)
        self.data_valid_g2f_dma = self.input("data_valid_g2f_dma", width=1)
        self.data_g2f = self.output("data_g2f", width=self._params.cgra_data_width,
                                    size=self._params.cgra_per_glb, packed=True)
        self.data_valid_g2f = self.output("data_valid_g2f", 1, size=self._params.cgra_per_glb, packed=True)

        self.data_f2g_dma = self.output("data_f2g_dma", width=self._params.cgra_data_width)
        self.data_valid_f2g_dma = self.output("data_valid_f2g_dma", width=1)
        self.data_f2g = self.input("data_f2g", width=self._params.cgra_data_width,
                                   size=self._params.cgra_per_glb, packed=True)
        self.data_valid_f2g = self.input("data_valid_f2g", 1, size=self._params.cgra_per_glb, packed=True)

        self.cfg_data_network_g2f_mux = self.input("cfg_data_network_g2f_mux", self._params.cgra_per_glb)
        self.cfg_data_network_f2g_mux = self.input("cfg_data_network_f2g_mux", self._params.cgra_per_glb)

        # local variables
        self.add_always(self.data_g2f_logic)
        self.add_always(self.data_f2g_logic)

    @always_comb
    def data_g2f_logic(self):
        for i in range(self._params.cgra_per_glb):
            if self.cfg_data_network_g2f_mux[i] == 1:
                self.data_g2f[i] = self.data_g2f_dma
                self.data_valid_g2f[i] = self.data_valid_g2f_dma
            else:
                self.data_g2f[i] = 0
                self.data_valid_g2f[i] = 0

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
