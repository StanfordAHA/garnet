from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbCorePcfgRouter(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_core_pcfg_router")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.rd_packet_w2e_wsti = self.input("rd_packet_w2e_wsti", self.header.rd_packet_t)
        self.rd_packet_e2w_wsto = self.output("rd_packet_e2w_wsto", self.header.rd_packet_t)
        self.rd_packet_e2w_esti = self.input("rd_packet_e2w_esti", self.header.rd_packet_t)
        self.rd_packet_w2e_esto = self.output("rd_packet_w2e_esto", self.header.rd_packet_t)

        self.rd_packet_sw2pcfgr = self.input("rd_packet_sw2pcfgr", self.header.rd_packet_t)
        self.rd_packet_pcfgr2sw = self.output("rd_packet_pcfgr2sw", self.header.rd_packet_t)

        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)

        # local variables
        self.rdrq_packet_w2e_wsti = self.var("rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
        self.rdrq_packet_w2e_wsti_muxed = self.var("rdrq_packet_w2e_wsti_muxed", self.header.rdrq_packet_t)
        self.rdrq_packet_w2e_esto_w = self.var("rdrq_packet_w2e_esto_w", self.header.rdrq_packet_t)
        self.rdrq_packet_w2e_esto = self.var("rdrq_packet_w2e_esto", self.header.rdrq_packet_t)
        self.rdrq_packet_e2w_esti = self.var("rdrq_packet_e2w_esti", self.header.rdrq_packet_t)
        self.rdrq_packet_e2w_esti_muxed = self.var("rdrq_packet_e2w_esti_muxed", self.header.rdrq_packet_t)
        self.rdrq_packet_e2w_wsto_w = self.var("rdrq_packet_e2w_wsto_w", self.header.rdrq_packet_t)
        self.rdrq_packet_e2w_wsto = self.var("rdrq_packet_e2w_wsto", self.header.rdrq_packet_t)
        self.rdrq_packet_sr2sw_w = self.var("rdrq_packet_sr2sw_w", self.header.rdrq_packet_t)

        self.add_always(self.packet_wsti_muxed_logic)
        self.add_always(self.packet_esti_muxed_logic)
        self.add_always(self.rdrq_packet_switch_logic)
        self.add_always(self.rdrs_packet_switch_logic)
        self.add_always(self.packet_pipeline)

        # wiring
        for signal in self.header.rdrq_packet_ports:
            self.wire(self.rdrq_packet_w2e_wsti[signal], self.rd_packet_w2e_wsti[signal])
            self.wire(self.rdrq_packet_w2e_esto[signal], self.rd_packet_w2e_esto[signal])
            self.wire(self.rdrq_packet_e2w_esti[signal], self.rd_packet_e2w_esti[signal])
            self.wire(self.rdrq_packet_e2w_wsto[signal], self.rd_packet_e2w_wsto[signal])

        for signal in self.header.rdrs_packet_ports:
            self.wire(self.rdrs_packet_w2e_wsti[signal], self.rd_packet_w2e_wsti[signal])
            self.wire(self.rdrs_packet_w2e_esto[signal], self.rd_packet_w2e_esto[signal])
            self.wire(self.rdrs_packet_e2w_esti[signal], self.rd_packet_e2w_esti[signal])
            self.wire(self.rdrs_packet_e2w_wsto[signal], self.rd_packet_e2w_wsto[signal])

        # localparam
        self.packet_addr_tile_sel_msb = (_params.bank_addr_width
                                         + _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1)
        self.packet_addr_tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width

    @always_comb
    def packet_wsti_muxed_logic(self):
        if self.cfg_tile_connected_prev:
            self.rdrq_packet_w2e_wsti_muxed = self.rdrq_packet_w2e_wsti
            self.rdrs_packet_w2e_wsti_muxed = self.rdrs_packet_w2e_wsti
        else:
            self.rdrq_packet_w2e_wsti_muxed = self.rdrq_packet_e2w_wsto
            self.rdrs_packet_w2e_wsti_muxed = self.rdrs_packet_e2w_wsto

    @always_comb
    def packet_esti_muxed_logic(self):
        if self.cfg_tile_connected_next:
            self.rdrq_packet_e2w_esti_muxed = self.rdrq_packet_e2w_esti
            self.rdrs_packet_e2w_esti_muxed = self.rdrs_packet_e2w_esti
        else:
            self.rdrq_packet_e2w_esti_muxed = self.rdrq_packet_w2e_esto
            self.rdrs_packet_e2w_esti_muxed = self.rdrs_packet_w2e_esto

    @always_comb
    def rdrq_packet_switch_logic(self):
        if (self.rdrq_packet_sw2sr['rd_en'] == 1):
            if (self.rdrq_packet_sw2sr['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.rdrq_packet_sr2sw_w = self.rdrq_packet_sw2sr
                self.rdrq_packet_w2e_esto_w = 0
            else:
                self.rdrq_packet_sr2sw_w = 0
                if self.cfg_tile_connected_next:
                    self.rdrq_packet_w2e_esto_w = self.rdrq_packet_sw2sr
                else:
                    self.rdrq_packet_w2e_esto_w = 0
        elif (self.rdrq_packet_w2e_wsti_muxed['rd_en'] == 1):
            if (self.rdrq_packet_w2e_wsti_muxed['rd_addr'][self.packet_addr_tile_sel_msb,
                                                           self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.rdrq_packet_sr2sw_w = self.rdrq_packet_w2e_wsti_muxed
                self.rdrq_packet_w2e_esto_w = 0
            else:
                self.rdrq_packet_sr2sw_w = 0
                if self.cfg_tile_connected_next:
                    self.rdrq_packet_w2e_esto_w = self.rdrq_packet_w2e_wsti_muxed
                else:
                    self.rdrq_packet_w2e_esto_w = 0
        else:
            self.rdrq_packet_sr2sw_w = 0
            self.rdrq_packet_w2e_esto_w = 0

        if self.cfg_tile_connected_prev:
            self.rdrq_packet_e2w_wsto_w = self.rdrq_packet_e2w_esti_muxed
        else:
            self.rdrq_packet_e2w_wsto_w = 0

    @always_comb
    def rdrs_packet_switch_logic(self):
        if (self.rdrs_packet_e2w_esti_muxed['rd_data_valid'] == 1):
            if (self.rdrs_packet_e2w_esti_muxed['rd_dst_tile'] == self.glb_tile_id):
                self.rdrs_packet_sr2sw_w = self.rdrs_packet_e2w_esti_muxed
                self.rdrs_packet_e2w_wsto_w = 0
            else:
                self.rdrs_packet_sr2sw_w = 0
                if self.cfg_tile_connected_prev:
                    self.rdrs_packet_e2w_wsto_w = self.rdrs_packet_e2w_esti_muxed
                else:
                    self.rdrs_packet_e2w_wsto_w = 0
        else:
            self.rdrs_packet_sr2sw_w = 0
            self.rdrs_packet_e2w_wsto_w = 0

        if self.cfg_tile_connected_next:
            self.rdrs_packet_w2e_esto_w = self.rdrs_packet_w2e_wsti_muxed
        else:
            self.rdrs_packet_w2e_esto_w = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_pipeline(self):
        if self.reset:
            self.wr_packet_w2e_esto = 0
            self.wr_packet_e2w_wsto = 0
            self.wr_packet_sr2sw = 0
            self.rdrq_packet_w2e_esto = 0
            self.rdrq_packet_e2w_wsto = 0
            self.rdrq_packet_sr2sw = 0
            self.rdrs_packet_w2e_esto = 0
            self.rdrs_packet_e2w_wsto = 0
            self.rdrs_packet_sr2sw = 0
        elif self.clk_en:
            self.wr_packet_w2e_esto = self.wr_packet_w2e_esto_w
            self.wr_packet_e2w_wsto = self.wr_packet_e2w_wsto_w
            self.wr_packet_sr2sw = self.wr_packet_sr2sw_w
            self.rdrq_packet_w2e_esto = self.rdrq_packet_w2e_esto_w
            self.rdrq_packet_e2w_wsto = self.rdrq_packet_e2w_wsto_w
            self.rdrq_packet_sr2sw = self.rdrq_packet_sr2sw_w
            self.rdrs_packet_w2e_esto = self.rdrs_packet_w2e_esto_w
            self.rdrs_packet_e2w_wsto = self.rdrs_packet_e2w_wsto_w
            self.rdrs_packet_sr2sw = self.rdrs_packet_sr2sw_w
