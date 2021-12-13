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
        self.rd_packet_w2e_wsti_turned = self.var("rd_packet_w2e_wsti_turned", self.header.rd_packet_t)
        self.rd_packet_w2e_wsti_turned_d1 = self.var("rd_packet_w2e_wsti_turned_d1", self.header.rd_packet_t)
        self.rd_packet_e2w_esti_turned = self.var("rd_packet_e2w_esti_turned", self.header.rd_packet_t)
        self.rd_packet_e2w_esti_turned_d1 = self.var("rd_packet_e2w_esti_turned_d1", self.header.rd_packet_t)
        self.rd_packet_sw2pcfgr_d1 = self.var("rd_packet_sw2pcfgr_d1", self.header.rd_packet_t)

        self.add_is_even_stmt()
        self.add_always(self.packet_wst_logic)
        self.add_always(self.packet_est_logic)
        self.add_always(self.packet_pipeline)
        self.add_always(self.packet_switch)

    def add_is_even_stmt(self):
        self.is_even = self.var("is_even", 1)
        self.wire(self.is_even, self.glb_tile_id[0] == 0)

    @always_comb
    def packet_wst_logic(self):
        if self.cfg_tile_connected_prev:
            self.rd_packet_w2e_wsti_turned = self.rd_packet_w2e_wsti
        else:
            self.rd_packet_w2e_wsti_turned = self.rd_packet_e2w_wsto

    @always_comb
    def packet_est_logic(self):
        if self.cfg_tile_connected_next:
            self.rd_packet_e2w_esti_turned = self.rd_packet_e2w_esti
        else:
            self.rd_packet_e2w_esti_turned = self.rd_packet_w2e_esto

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_pipeline(self):
        if self.reset:
            self.rd_packet_w2e_wsti_turned_d1 = 0
            self.rd_packet_e2w_esti_turned_d1 = 0
            self.rd_packet_sw2pcfgr_d1 = 0
        else:
            self.rd_packet_w2e_wsti_turned_d1 = self.rd_packet_w2e_wsti_turned
            self.rd_packet_e2w_esti_turned_d1 = self.rd_packet_e2w_esti_turned
            self.rd_packet_sw2pcfgr_d1 = self.rd_packet_sw2pcfgr

    @always_comb
    def packet_switch(self):
        # packet to core
        if self.is_even:
            self.rd_packet_pcfgr2sw = self.rd_packet_w2e_wsti_turned
            self.rd_packet_w2e_esto = self.rd_packet_sw2pcfgr_d1
            self.rd_packet_e2w_wsto = self.rd_packet_sw2pcfgr_d1
        else:
            self.rd_packet_pcfgr2sw = self.rd_packet_e2w_esti_turned
            self.rd_packet_w2e_esto = self.rd_packet_w2e_wsti_turned_d1
            self.rd_packet_e2w_wsto = self.rd_packet_e2w_esti_turned_d1
