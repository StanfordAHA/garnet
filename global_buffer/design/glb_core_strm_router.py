from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbCoreStrmRouter(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_core_strm_router")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.clk_en = self.input("clk_en", 1)
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.packet_w2e_wsti = self.input("packet_w2e_wsti", self.header.packet_t)
        self.packet_e2w_wsto = self.output("packet_e2w_wsto", self.header.packet_t)
        self.packet_e2w_esti = self.input("packet_e2w_esti", self.header.packet_t)
        self.packet_w2e_esto = self.output("packet_w2e_esto", self.header.packet_t)

        self.wr_packet_sw2sr = self.input("wr_packet_sw2sr", self.header.wr_packet_t)
        self.wr_packet_sr2sw = self.output("wr_packet_sr2sw", self.header.wr_packet_t)
        self.rdrq_packet_sw2sr = self.input("rdrq_packet_sw2sr", self.header.rdrq_packet_t)
        self.rdrq_packet_sr2sw = self.output("rdrq_packet_sr2sw", self.header.rdrq_packet_t)
        self.rdrs_packet_sw2sr = self.input("rdrs_packet_sw2sr", self.header.rdrs_packet_t)
        self.rdrs_packet_sr2sw = self.output("rdrs_packet_sr2sw", self.header.rdrs_packet_t)

        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)

        # local variables
        self.packet_w2e_wsti_d1 = self.var("packet_w2e_wsti_d1", self.header.packet_t)
        self.packet_w2e_wsti_turned = self.var("packet_w2e_wsti_turned", self.header.packet_t)
        self.packet_w2e_wsti_turned_d1 = self.var("packet_w2e_wsti_turned_d1", self.header.packet_t)
        self.packet_e2w_esti_d1 = self.var("packet_e2w_esti_d1", self.header.packet_t)
        self.packet_e2w_esti_turned = self.var("packet_e2w_esti_turned", self.header.packet_t)
        self.packet_e2w_esti_turned_d1 = self.var("packet_e2w_esti_turned_d1", self.header.packet_t)
        self.packet_sw2sr_d1 = self.var("packet_sw2sr_d1", self.header.packet_t)

        # localparam
        self.packet_addr_tile_sel_msb = (_params.bank_addr_width
                                         + _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1)
        self.packet_addr_tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width

        # localparam
        self.add_always(self.packet_wst_logic)
        self.add_always(self.packet_est_logic)
        self.add_always(self.packet_pipeline)
        self.add_always(self.packet_sw2sr_pipeline)
        self.add_always(self.packet_switch)

    @always_comb
    def packet_wsti_muxed_logic(self):
        if self.cfg_tile_connected_prev:
            self.wr_packet_w2e_wsti_muxed = self.wr_packet_w2e_wsti
            self.rdrq_packet_w2e_wsti_muxed = self.rdrq_packet_w2e_wsti
            self.rdrs_packet_w2e_wsti_muxed = self.rdrs_packet_w2e_wsti
        else:
            self.wr_packet_w2e_wsti_muxed = self.wr_packet_e2w_wsto_d
            self.rdrq_packet_w2e_wsti_muxed = self.rdrq_packet_e2w_wsto_d
            self.rdrs_packet_w2e_wsti_muxed = self.rdrs_packet_e2w_wsto_d

    @always_comb
    def packet_esti_muxed_logic(self):
        if self.cfg_tile_connected_next:
            self.wr_packet_e2w_esti_muxed = self.wr_packet_e2w_esti
            self.rdrq_packet_e2w_esti_muxed = self.rdrq_packet_e2w_esti
            self.rdrs_packet_e2w_esti_muxed = self.rdrs_packet_e2w_esti
        else:
            self.wr_packet_e2w_esti_muxed = self.wr_packet_w2e_esto_d
            self.rdrq_packet_e2w_esti_muxed = self.rdrq_packet_w2e_esto_d
            self.rdrs_packet_e2w_esti_muxed = self.rdrs_packet_w2e_esto_d

    @always_comb
    def wr_packet_switch_logic(self):
        if (self.wr_packet_sw2sr['wr_en'] == 1):
            if (self.wr_packet_sw2sr['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.wr_packet_sr2sw_w = self.wr_packet_sw2sr
                self.wr_packet_w2e_esto_w = 0
            else:
                self.wr_packet_sr2sw_w = 0
                if self.cfg_tile_connected_next:
                    self.wr_packet_w2e_esto_w = self.wr_packet_sw2sr
                else:
                    self.wr_packet_w2e_esto_w = 0
        elif (self.wr_packet_w2e_wsti_muxed['wr_en'] == 1):
            if (self.wr_packet_w2e_wsti_muxed['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.wr_packet_sr2sw_w = self.wr_packet_w2e_wsti_muxed
                self.wr_packet_w2e_esto_w = 0
            else:
                self.wr_packet_sr2sw_w = 0
                if self.cfg_tile_connected_next:
                    self.wr_packet_w2e_esto_w = self.wr_packet_w2e_wsti_muxed
                else:
                    self.wr_packet_w2e_esto_w = 0
        else:
            self.wr_packet_sr2sw_w = 0
            self.wr_packet_w2e_esto_w = 0

        if self.cfg_tile_connected_prev:
            self.wr_packet_e2w_wsto_w = self.wr_packet_e2w_esti_muxed
        else:
            self.wr_packet_e2w_wsto_w = 0
