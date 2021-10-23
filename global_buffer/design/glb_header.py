from kratos import PackedStruct
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
import math


class GlbHeader():
    def __init__(self, params: GlobalBufferParams):
        self.params = params

        wr_packet_list = [("wr_en", 1),
                          ("wr_strb", math.ceil(self.params.bank_data_width/8)),
                          ("wr_addr", self.params.glb_addr_width),
                          ("wr_data", self.params.bank_data_width), ]
        rdrq_packet_list = [("rd_en", 1),
                            ("rd_addr", self.params.glb_addr_width), ]
        rdrs_packet_list = [("rd_data", self.params.bank_data_width),
                            ("rd_data_valid", 1), ]

        self.packet_t = PackedStruct(
            "packet_t", wr_packet_list + rdrq_packet_list + rdrs_packet_list)
        self.wr_packet_t = PackedStruct("wr_packet_t", wr_packet_list)
        self.rdrq_packet_t = PackedStruct("rdrq_packet_t", rdrq_packet_list)
        self.rdrs_packet_t = PackedStruct("rdrs_packet_t", rdrs_packet_list)

        # TODO: Kratos currently does not support struct of struct.
        # This can become cleaner if it does.
        self.wr_packet_ports = [name for (name, _) in wr_packet_list]
        self.rdrq_packet_ports = [name for (name, _) in rdrq_packet_list]
        self.rdrs_packet_ports = [name for (name, _) in rdrs_packet_list]
