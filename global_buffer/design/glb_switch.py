from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbSwitch(Generator):
    def __init__(self, _params: GlobalBufferParams, wr_channel=True, rd_channel=True):
        name = "glb_switch"
        if wr_channel:
            name += "_WR"
        if rd_channel:
            name += "_RD"
        super().__init__(name)

        self._params = _params
        self.header = GlbHeader(self._params)

        self.wr_channel = wr_channel
        self.rd_channel = rd_channel
        assert self.wr_channel is True or self.rd_channel is True

        self.clk = self.clock("clk")
        self.clk_en = self.input("clk_en", 1)
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        if self.wr_channel:
            self.wr_packet_w2e_wsti = self.input("wr_packet_w2e_wsti", self.header.wr_packet_t)
            self.wr_packet_e2w_wsto = self.output("wr_packet_e2w_wsto", self.header.wr_packet_t)
            self.wr_packet_e2w_esti = self.input("wr_packet_e2w_esti", self.header.wr_packet_t)
            self.wr_packet_w2e_esto = self.output("wr_packet_w2e_esto", self.header.wr_packet_t)
            self.wr_packet_sw2r = self.input("wr_packet_sw2r", self.header.wr_packet_t)
            self.wr_packet_r2sw = self.output("wr_packet_r2sw", self.header.wr_packet_t)

        if self.rd_channel:
            self.rdrq_packet_w2e_wsti = self.input("rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
            self.rdrq_packet_e2w_wsto = self.output("rdrq_packet_e2w_wsto", self.header.rdrq_packet_t)
            self.rdrq_packet_e2w_esti = self.input("rdrq_packet_e2w_esti", self.header.rdrq_packet_t)
            self.rdrq_packet_w2e_esto = self.output("rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

            self.rdrs_packet_w2e_wsti = self.input("rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
            self.rdrs_packet_e2w_wsto = self.output("rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)
            self.rdrs_packet_e2w_esti = self.input("rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
            self.rdrs_packet_w2e_esto = self.output("rdrs_packet_w2e_esto", self.header.rdrs_packet_t)

            self.rdrq_packet_sw2r = self.input("rdrq_packet_sw2r", self.header.rdrq_packet_t)
            self.rdrq_packet_r2sw = self.output("rdrq_packet_r2sw", self.header.rdrq_packet_t)
            self.rdrs_packet_sw2r = self.input("rdrs_packet_sw2r", self.header.rdrs_packet_t)
            self.rdrs_packet_r2sw = self.output("rdrs_packet_r2sw", self.header.rdrs_packet_t)

        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)

        # local variables
        if self.wr_channel:
            self.wr_packet_w2e_wsti_muxed = self.var("wr_packet_w2e_wsti_muxed", self.header.wr_packet_t)
            self.wr_packet_w2e_esto_w = self.var("wr_packet_w2e_esto_w", self.header.wr_packet_t)
            self.wr_packet_e2w_esti_muxed = self.var("wr_packet_e2w_esti_muxed", self.header.wr_packet_t)
            self.wr_packet_e2w_wsto_w = self.var("wr_packet_e2w_wsto_w", self.header.wr_packet_t)
            self.wr_packet_r2sw_w = self.var("wr_packet_r2sw_w", self.header.wr_packet_t)

        if self.rd_channel:
            self.rdrq_packet_w2e_wsti_muxed = self.var("rdrq_packet_w2e_wsti_muxed", self.header.rdrq_packet_t)
            self.rdrq_packet_w2e_esto_w = self.var("rdrq_packet_w2e_esto_w", self.header.rdrq_packet_t)
            self.rdrq_packet_e2w_esti_muxed = self.var("rdrq_packet_e2w_esti_muxed", self.header.rdrq_packet_t)
            self.rdrq_packet_e2w_wsto_w = self.var("rdrq_packet_e2w_wsto_w", self.header.rdrq_packet_t)
            self.rdrq_packet_r2sw_w = self.var("rdrq_packet_r2sw_w", self.header.rdrq_packet_t)

            self.rdrs_packet_w2e_wsti_muxed = self.var("rdrs_packet_w2e_wsti_muxed", self.header.rdrs_packet_t)
            self.rdrs_packet_w2e_esto_w = self.var("rdrs_packet_w2e_esto_w", self.header.rdrs_packet_t)
            self.rdrs_packet_e2w_esti_muxed = self.var("rdrs_packet_e2w_esti_muxed", self.header.rdrs_packet_t)
            self.rdrs_packet_e2w_wsto_w = self.var("rdrs_packet_e2w_wsto_w", self.header.rdrs_packet_t)
            self.rdrs_packet_r2sw_w = self.var("rdrs_packet_r2sw_w", self.header.rdrs_packet_t)

        # localparam
        self.packet_addr_tile_sel_msb = (_params.bank_addr_width
                                         + _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1)
        self.packet_addr_tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width

        self.add_always(self.packet_wsti_muxed_logic)
        self.add_always(self.packet_esti_muxed_logic)

        if self.wr_channel:
            self.add_always(self.wr_packet_switch_logic)

        if self.rd_channel:
            self.add_always(self.rdrq_packet_switch_logic)
            self.add_always(self.rdrs_packet_switch_logic)

        self.add_always(self.packet_pipeline)

    @always_comb
    def packet_wsti_muxed_logic(self):
        if self.cfg_tile_connected_prev:
            if self.wr_channel:
                self.wr_packet_w2e_wsti_muxed = self.wr_packet_w2e_wsti
            if self.rd_channel:
                self.rdrq_packet_w2e_wsti_muxed = self.rdrq_packet_w2e_wsti
                self.rdrs_packet_w2e_wsti_muxed = self.rdrs_packet_w2e_wsti
        else:
            if self.wr_channel:
                self.wr_packet_w2e_wsti_muxed = self.wr_packet_e2w_wsto
            if self.rd_channel:
                self.rdrq_packet_w2e_wsti_muxed = self.rdrq_packet_e2w_wsto
                self.rdrs_packet_w2e_wsti_muxed = self.rdrs_packet_e2w_wsto

    @always_comb
    def packet_esti_muxed_logic(self):
        if self.cfg_tile_connected_next:
            if self.wr_channel:
                self.wr_packet_e2w_esti_muxed = self.wr_packet_e2w_esti
            if self.rd_channel:
                self.rdrq_packet_e2w_esti_muxed = self.rdrq_packet_e2w_esti
                self.rdrs_packet_e2w_esti_muxed = self.rdrs_packet_e2w_esti
        else:
            if self.wr_channel:
                self.wr_packet_e2w_esti_muxed = self.wr_packet_w2e_esto
            if self.rd_channel:
                self.rdrq_packet_e2w_esti_muxed = self.rdrq_packet_w2e_esto
                self.rdrs_packet_e2w_esti_muxed = self.rdrs_packet_w2e_esto

    @always_comb
    def wr_packet_switch_logic(self):
        if (self.wr_packet_sw2r['wr_en'] == 1):
            if (self.wr_packet_sw2r['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.wr_packet_r2sw_w = self.wr_packet_sw2r
                self.wr_packet_w2e_esto_w = 0
            else:
                self.wr_packet_r2sw_w = 0
                self.wr_packet_w2e_esto_w = self.wr_packet_sw2r
        elif (self.wr_packet_w2e_wsti_muxed['wr_en'] == 1):
            if (self.wr_packet_w2e_wsti_muxed['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.wr_packet_r2sw_w = self.wr_packet_w2e_wsti_muxed
                self.wr_packet_w2e_esto_w = 0
            else:
                self.wr_packet_r2sw_w = 0
                self.wr_packet_w2e_esto_w = self.wr_packet_w2e_wsti_muxed
        else:
            self.wr_packet_r2sw_w = 0
            self.wr_packet_w2e_esto_w = 0

        self.wr_packet_e2w_wsto_w = self.wr_packet_e2w_esti_muxed

    @always_comb
    def rdrq_packet_switch_logic(self):
        if (self.rdrq_packet_sw2r['rd_en'] == 1):
            if (self.rdrq_packet_sw2r['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.rdrq_packet_r2sw_w = self.rdrq_packet_sw2r
                self.rdrq_packet_w2e_esto_w = 0
            else:
                self.rdrq_packet_r2sw_w = 0
                self.rdrq_packet_w2e_esto_w = self.rdrq_packet_sw2r
        elif (self.rdrq_packet_w2e_wsti_muxed['rd_en'] == 1):
            if (self.rdrq_packet_w2e_wsti_muxed['rd_addr'][self.packet_addr_tile_sel_msb,
                                                           self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.rdrq_packet_r2sw_w = self.rdrq_packet_w2e_wsti_muxed
                self.rdrq_packet_w2e_esto_w = 0
            else:
                self.rdrq_packet_r2sw_w = 0
                self.rdrq_packet_w2e_esto_w = self.rdrq_packet_w2e_wsti_muxed
        else:
            self.rdrq_packet_r2sw_w = 0
            self.rdrq_packet_w2e_esto_w = 0

        self.rdrq_packet_e2w_wsto_w = self.rdrq_packet_e2w_esti_muxed

    @always_comb
    def rdrs_packet_switch_logic(self):
        if (self.rdrs_packet_sw2r['rd_data_valid'] == 1):
            self.rdrs_packet_w2e_esto_w = self.rdrs_packet_sw2r
        else:
            if ((self.rdrs_packet_w2e_wsti_muxed['rd_data_valid'] == 1)
                    & (self.rdrs_packet_w2e_wsti_muxed['rd_dst_tile'] == self.glb_tile_id)):
                self.rdrs_packet_w2e_esto_w = 0
            else:
                self.rdrs_packet_w2e_esto_w = self.rdrs_packet_w2e_wsti_muxed

        if ((self.rdrs_packet_w2e_wsti_muxed['rd_data_valid'] == 1)
                & (self.rdrs_packet_w2e_wsti_muxed['rd_dst_tile'] == self.glb_tile_id)):
            self.rdrs_packet_r2sw_w = self.rdrs_packet_w2e_wsti_muxed
        else:
            self.rdrs_packet_r2sw_w = self.rdrs_packet_w2e_wsti_muxed

        self.rdrs_packet_e2w_wsto_w = self.rdrs_packet_e2w_esti_muxed

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_pipeline(self):
        if self.reset:
            if self.wr_channel:
                self.wr_packet_w2e_esto = 0
                self.wr_packet_e2w_wsto = 0
                self.wr_packet_r2sw = 0
            if self.rd_channel:
                self.rdrq_packet_w2e_esto = 0
                self.rdrq_packet_e2w_wsto = 0
                self.rdrq_packet_r2sw = 0
                self.rdrs_packet_w2e_esto = 0
                self.rdrs_packet_e2w_wsto = 0
                self.rdrs_packet_r2sw = 0
        elif self.clk_en:
            if self.wr_channel:
                self.wr_packet_w2e_esto = self.wr_packet_w2e_esto_w
                self.wr_packet_e2w_wsto = self.wr_packet_e2w_wsto_w
                self.wr_packet_r2sw = self.wr_packet_r2sw_w
            if self.rd_channel:
                self.rdrq_packet_w2e_esto = self.rdrq_packet_w2e_esto_w
                self.rdrq_packet_e2w_wsto = self.rdrq_packet_e2w_wsto_w
                self.rdrq_packet_r2sw = self.rdrq_packet_r2sw_w
                self.rdrs_packet_w2e_esto = self.rdrs_packet_w2e_esto_w
                self.rdrs_packet_e2w_wsto = self.rdrs_packet_e2w_wsto_w
                self.rdrs_packet_r2sw = self.rdrs_packet_r2sw_w
