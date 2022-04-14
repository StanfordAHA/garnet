from kratos import PackedStruct, clog2
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbHeader():
    enum_cache = {}

    def __init__(self, _params: GlobalBufferParams):
        self._params = _params

        self.cfg_data_network_t = PackedStruct("cfg_data_network_t",
                                               [("tile_connected", 1),
                                                ("latency", self._params.latency_width)])

        self.cfg_pcfg_network_t = PackedStruct("cfg_pcfg_network_t",
                                               [("tile_connected", 1),
                                                ("latency", self._params.pcfg_latency_width)])

        self.cfg_store_dma_ctrl_t = PackedStruct("store_dma_ctrl_t",
                                                 [("mode", 2),
                                                  ("use_valid", 1),
                                                     ("data_mux", 2),
                                                     ("num_repeat", clog2(self._params.queue_depth) + 1)])

        self.cfg_load_dma_ctrl_t = PackedStruct("load_dma_ctrl_t",
                                                [("mode", 2),
                                                 ("use_valid", 1),
                                                 ("use_flush", 1),
                                                    ("data_mux", 2),
                                                    ("num_repeat", clog2(self._params.queue_depth) + 1)])

        dma_header_struct_list = [("start_addr", self._params.glb_addr_width),
                                  ("cycle_start_addr", self._params.cycle_count_width)]
        dma_header_struct_list += [("dim", 1 + clog2(self._params.loop_level))]
        for i in range(self._params.loop_level):
            dma_header_struct_list += [(f"range_{i}", self._params.axi_data_width),
                                       (f"stride_{i}", self._params.glb_addr_width + 1),
                                       (f"cycle_stride_{i}", self._params.cycle_count_width)]
        self.cfg_dma_header_t = PackedStruct("dma_header_t", dma_header_struct_list)

        # pcfg dma header
        self.cfg_pcfg_dma_ctrl_t = PackedStruct("pcfg_dma_ctrl_t",
                                                [("mode", 1),
                                                 ("relocation_value", self._params.cgra_cfg_addr_width // 2),
                                                 ("relocation_is_msb", 1)])
        self.cfg_pcfg_dma_header_t = PackedStruct("pcfg_dma_header_t",
                                                  [("start_addr", self._params.glb_addr_width),
                                                   ("num_cfg", self._params.max_num_cfg_width)])

        self.wr_bank_packet_ports = [("wr_en", 1),
                                     ("wr_strb", self._params.bank_strb_width),
                                     ("wr_addr", self._params.bank_addr_width),
                                     ("wr_data", self._params.bank_data_width), ]
        self.rdrq_bank_packet_ports = [("rd_en", 1),
                                       ("rd_addr", self._params.bank_addr_width), ]
        self.wr_packet_ports = [("wr_en", 1),
                                ("wr_strb", self._params.bank_strb_width),
                                ("wr_addr", self._params.glb_addr_width),
                                ("wr_data", self._params.bank_data_width), ]
        self.rdrq_packet_ports = [("rd_en", 1),
                                  ("rd_addr", self._params.glb_addr_width), ]
        self.rdrs_packet_ports = [("rd_data", self._params.bank_data_width),
                                  ("rd_data_valid", 1), ]

        self.packet_ports = self.wr_packet_ports + self.rdrq_packet_ports + self.rdrs_packet_ports
        self.rd_packet_ports = self.rdrq_packet_ports + self.rdrs_packet_ports

        self.wr_bank_packet_t = PackedStruct("wr_bank_packet_t", self.wr_bank_packet_ports)
        self.rdrq_bank_packet_t = PackedStruct("rdrq_bank_packet_t", self.rdrq_bank_packet_ports)
        self.wr_packet_t = PackedStruct("wr_packet_t", self.wr_packet_ports)
        self.rdrq_packet_t = PackedStruct("rdrq_packet_t", self.rdrq_packet_ports)
        self.rdrs_packet_t = PackedStruct("rdrs_packet_t", self.rdrs_packet_ports)
        self.packet_t = PackedStruct("packet_t")
        self.packet_t.add_attribute("wr", self.wr_packet_t)
        self.packet_t.add_attribute("rdrq", self.rdrq_packet_t)
        self.packet_t.add_attribute("rdrs", self.rdrs_packet_t)
        self.rd_packet_t = PackedStruct("rd_packet_t")
        self.rd_packet_t.add_attribute("rdrq", self.rdrq_packet_t)
        self.rd_packet_t.add_attribute("rdrs", self.rdrs_packet_t)

        self.cgra_cfg_t = PackedStruct("cgra_cfg_t", [("rd_en", 1), ("wr_en", 1), (
            "addr", self._params.cgra_cfg_addr_width), ("data", self._params.cgra_cfg_data_width)])

        self.cfg_pcfg_broadcast_mux_t = PackedStruct("pcfg_broadcast_mux_t", [("west", 2), ("east", 2), ("south", 2)])
