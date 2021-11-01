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
        self.glb_tile_id = self.input(
            "glb_tile_id", self._params.tile_sel_addr_width)

        self.packet_w2e_wsti = self.input(
            "packet_w2e_wsti", self.header.packet_t)
        self.packet_e2w_wsto = self.output(
            "packet_e2w_wsto", self.header.packet_t)
        self.packet_e2w_esti = self.input(
            "packet_e2w_esti", self.header.packet_t)
        self.packet_w2e_esto = self.output(
            "packet_w2e_esto", self.header.packet_t)

        self.packet_sw2sr = self.input(
            "packet_sw2sr", self.header.packet_t)
        self.packet_sr2sw = self.output(
            "packet_sr2sw", self.header.packet_t)

        self.cfg_tile_connected_prev = self.input(
            "cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input(
            "cfg_tile_connected_next", 1)

        # local variables
        self.packet_w2e_wsti_d1 = self.var(
            "packet_w2e_wsti_d1", self.header.packet_t)
        self.packet_w2e_wsti_turned = self.var(
            "packet_w2e_wsti_turned", self.header.packet_t)
        self.packet_w2e_wsti_turned_d1 = self.var(
            "packet_w2e_wsti_turned_d1", self.header.packet_t)
        self.packet_e2w_esti_d1 = self.var(
            "packet_e2w_esti_d1", self.header.packet_t)
        self.packet_e2w_esti_turned = self.var(
            "packet_e2w_esti_turned", self.header.packet_t)
        self.packet_e2w_esti_turned_d1 = self.var(
            "packet_e2w_esti_turned_d1", self.header.packet_t)
        self.packet_sw2sr_d1 = self.var(
            "packet_sw2sr_d1", self.header.packet_t)

        # localparam
        self.add_is_even_stmt()
        self.add_always(self.packet_wst_logic)
        self.add_always(self.packet_est_logic)
        self.add_always(self.packet_pipeline)
        self.add_always(self.packet_sw2sr_pipeline)
        self.add_always(self.packet_switch)

    def add_is_even_stmt(self):
        self.is_even = self.var("is_even", 1)
        self.wire(self.is_even, self.glb_tile_id[0] == 0)

    @always_comb
    def packet_wst_logic(self):
        if self.cfg_tile_connected_prev:
            self.packet_w2e_wsti_turned = self.packet_w2e_wsti_d1
        else:
            self.packet_w2e_wsti_turned = self.packet_e2w_wsto

    @always_comb
    def packet_est_logic(self):
        if self.cfg_tile_connected_next:
            self.packet_e2w_esti_turned = self.packet_e2w_esti_d1
        else:
            self.packet_e2w_esti_turned = self.packet_w2e_esto
    
    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_sw2sr_pipeline(self):
        if self.reset:
            self.packet_sw2sr_d1 = 0
        elif self.clk_en:
            self.packet_sw2sr_d1 = self.packet_sw2sr

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_pipeline(self):
        if self.reset:
            self.packet_w2e_wsti_turned_d1 = 0
            self.packet_e2w_esti_turned_d1 = 0
        elif self.clk_en:
            self.packet_w2e_wsti_turned_d1 = self.packet_w2e_wsti_turned
            self.packet_e2w_esti_turned_d1 = self.packet_e2w_esti_turned

    @always_comb
    def packet_switch(self):
        if self.is_even:
            self.packet_sr2sw = self.packet_w2e_wsti_turned
            self.packet_w2e_esto = self.packet_sw2sr_d1
            self.packet_e2w_wsto = self.packet_e2w_esti_turned_d1
        else:
            self.packet_sr2sw = self.packet_e2w_esti_turned
            self.packet_w2e_esto = self.packet_w2e_wsti_turned_d1
            self.packet_e2w_wsto = self.packet_sw2sr_d1
