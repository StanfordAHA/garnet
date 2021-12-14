from kratos import PackedStruct, clog2, enum
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
import math
from enum import Enum


class GlbHeader():
    enum_cache = {}

    def __init__(self, _params: GlobalBufferParams):
        self._params = _params

        self.cfg_data_network_t = PackedStruct("cfg_data_network_t",
                                               [("tile_connected", 1),
                                                ("latency", self._params.latency_width)])

        self.cfg_pcfg_network_t = PackedStruct("cfg_pcfg_network_t",
                                               [("tile_connected", 1),
                                                ("latency", self._params.latency_width)])

        self.cfg_dma_ctrl_t = PackedStruct("dma_ctrl_t",
                                           [("mode", 2),
                                            ("use_valid", 1),
                                            ("data_mux", 2),
                                            ("num_repeat", clog2(self._params.queue_depth) + 1)])

        # NOTE: Kratos does not support struct of struct now.
        dma_header_struct_list = [("start_addr", self._params.glb_addr_width),
                                  ("cycle_start_addr", self._params.cycle_count_width)]
        dma_header_struct_list += [("dim", 1 + clog2(self._params.loop_level))]
        for i in range(self._params.loop_level):
            dma_header_struct_list += [(f"range_{i}", self._params.axi_data_width),
                                       (f"stride_{i}", self._params.glb_addr_width + 1),
                                       (f"cycle_stride_{i}", self._params.cycle_count_width)]
        self.cfg_dma_header_t = PackedStruct("dma_header_t", dma_header_struct_list)

        # pcfg dma header
        self.cfg_pcfg_dma_ctrl_t = PackedStruct("pcfg_dma_ctrl_t", [("mode", 1)])
        self.cfg_pcfg_dma_header_t = PackedStruct("pcfg_dma_header_t",
                                                  [("start_addr", self._params.glb_addr_width),
                                                   ("num_cfg", self._params.max_num_cfg_width)])

        class PacketEnum(Enum):
            none = 0
            proc = 1
            strm = 2
            pcfg = 3
        self.PacketEnum = PacketEnum
        self.PacketEnumWidth = 2

        self.wr_packet_list = [("wr_en", 1),
                               ("wr_strb", math.ceil(self._params.bank_data_width / 8)),
                               ("wr_addr", self._params.glb_addr_width),
                               ("wr_data", self._params.bank_data_width), ]
        self.rdrq_packet_list = [("rd_en", 1),
                                 ("rd_type", 2),
                                 ("rd_src_tile", self._params.tile_sel_addr_width),
                                 ("rd_addr", self._params.glb_addr_width), ]
        self.rdrs_packet_list = [("rd_data", self._params.bank_data_width),
                                 ("rd_dst_tile", self._params.tile_sel_addr_width),
                                 ("rd_data_valid", 1), ]

        self.packet_list = self.wr_packet_list + self.rdrq_packet_list + self.rdrs_packet_list
        self.rd_packet_list = self.rdrq_packet_list + self.rdrs_packet_list

        self.packet_t = PackedStruct(
            "packet_t", self.wr_packet_list + self.rdrq_packet_list + self.rdrs_packet_list)
        self.rd_packet_t = PackedStruct(
            "rd_packet_t", self.rdrq_packet_list + self.rdrs_packet_list)
        self.rdrq_packet_t = PackedStruct("rdrq_packet_t", self.rdrq_packet_list)
        self.rdrs_packet_t = PackedStruct("rdrs_packet_t", self.rdrs_packet_list)

        self.wr_packet_t = PackedStruct("wr_packet_t", self.wr_packet_list)

        # NOTE: Kratos currently does not support struct of struct.
        # This can become cleaner if it does.
        self.wr_packet_ports = [name for (name, _) in self.wr_packet_list]
        self.rdrq_packet_ports = [name for (name, _) in self.rdrq_packet_list]
        self.rdrs_packet_ports = [name for (name, _) in self.rdrs_packet_list]
        self.rd_packet_ports = [name for (name, _) in (
            self.rdrq_packet_list + self.rdrs_packet_list)]
        self.packet_ports = [name for (name, _) in (
            self.rdrq_packet_list + self.rdrs_packet_list + self.wr_packet_list)]

        self.cgra_cfg_t = PackedStruct("cgra_cfg_t", [("rd_en", 1), ("wr_en", 1), (
            "addr", self._params.cgra_cfg_addr_width), ("data", self._params.cgra_cfg_data_width)])
