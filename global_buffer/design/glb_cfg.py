from kratos import PackedStruct
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbConfig():
    def __init__(self, params: GlobalBufferParams):
        self.params = params
        self.cfg_data_network_t = PackedStruct("cfg_data_network_t",
                                               [("f2g_mux", 2),
                                                ("g2f_mux", 2),
                                                ("tile_connected", 1),
                                                ("latency", self.params.latency_width)])

        self.cfg_pcfg_network_t = PackedStruct("cfg_pcfg_network_t",
                                               [("tile_connected", 1),
                                                ("latency", self.params.latency_width)])
        self.cfg_st_dma_ctrl_t = PackedStruct("st_dma_ctrl_t",
                                              [("mode", 2)])

        self.cfg_st_dma_header_t = PackedStruct("st_dma_header_t",
                                                [("validate", 1),
                                                 ("start_addr",
                                                  self.params.glb_addr_width),
                                                 ("num_words", self.params.max_num_words_width)])
        self.cfg_ld_dma_ctrl_t = PackedStruct("ld_dma_ctrl_t",
                                              [("mode", 2),
                                               ("use_valid", 1)])

        # TODO: Kratos does not support struct of struct now.
        dma_header_struct_list = [("validate", 1),
                                  ("start_addr", self.params.glb_addr_width)]

        for i in range(self.params.loop_level):
            dma_header_struct_list += [(f"range_{i}", self.params.axi_data_width),
                                       (f"stride_{i}", self.params.axi_data_width)]
        dma_header_struct_list += [("num_active_words", self.params.max_num_words_width),
                                   ("num_inactive_words", self.params.max_num_words_width)]
        self.cfg_ld_dma_header_t = PackedStruct(
            "ld_dma_header_t", dma_header_struct_list)

        self.cfg_pcfg_dma_ctrl_t = PackedStruct("pcfg_dma_ctrl_t",
                                                [("mode", 1)])
        self.cfg_pcfg_dma_header_t = PackedStruct("pcfg_dma_header_t",
                                                  [("start_addr", self.params.glb_addr_width),
                                                   ("num_cfg", self.params.max_num_cfg_width)])
