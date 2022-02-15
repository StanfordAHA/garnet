from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbProcSwitch(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_proc_switch")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.wr_packet_w2e_wsti = self.input("wr_packet_w2e_wsti", self.header.wr_packet_t)
        self.wr_packet_w2e_esto = self.output("wr_packet_w2e_esto", self.header.wr_packet_t)
        self.rdrq_packet_w2e_wsti = self.input("rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
        self.rdrq_packet_w2e_esto = self.output("rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

        self.rdrs_packet_w2e_wsti = self.input("rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
        self.rdrs_packet_w2e_esto = self.output("rdrs_packet_w2e_esto", self.header.rdrs_packet_t)
        self.rdrs_packet_e2w_esti = self.input("rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
        self.rdrs_packet_e2w_wsto = self.output("rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)

        self.wr_packet_pr2sw = self.output("wr_packet_pr2sw", self.header.wr_packet_t)
        self.rdrq_packet_pr2sw = self.output("rdrq_packet_pr2sw", self.header.rdrq_packet_t)
        self.rdrs_packet_sw2pr = self.input("rdrs_packet_sw2pr", self.header.rdrs_packet_t)

        self.wr_packet_pr2sw_w = self.var("wr_packet_pr2sw_w", self.header.wr_packet_t)
        self.rdrq_packet_pr2sw_w = self.var("rdrq_packet_pr2sw_w", self.header.rdrq_packet_t)
        self.wr_packet_w2e_esto_w = self.var("wr_packet_w2e_esto_w", self.header.wr_packet_t)
        self.wr_packet_e2w_wsto_w = self.var("wr_packet_e2w_wsto_w", self.header.wr_packet_t)
        self.rdrq_packet_w2e_esto_w = self.var("rdrq_packet_w2e_esto_w", self.header.rdrq_packet_t)
        self.rdrq_packet_e2w_wsto_w = self.var("rdrq_packet_e2w_wsto_w", self.header.rdrq_packet_t)
        self.rdrs_packet_w2e_esto_w = self.var("rdrs_packet_w2e_esto_w", self.header.rdrs_packet_t)
        self.rdrs_packet_e2w_wsto_w = self.var("rdrs_packet_e2w_wsto_w", self.header.rdrs_packet_t)

        # localparam
        self.packet_addr_tile_sel_msb = _params.bank_addr_width + \
            _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1
        self.packet_addr_tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width

        self.add_always(self.wr_switch_logic)
        self.add_always(self.rdrq_switch_logic)
        self.add_always(self.rdrs_switch_logic)
        self.add_always(self.packet_pipeline)

    @always_comb
    def wr_switch_logic(self):
        if (self.wr_packet_w2e_wsti['wr_en'] == 1):
            if (self.wr_packet_w2e_wsti['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.wr_packet_pr2sw_w = self.wr_packet_w2e_wsti
                self.wr_packet_w2e_esto_w = 0
            else:
                self.wr_packet_pr2sw_w = 0
                self.wr_packet_w2e_esto_w = self.wr_packet_w2e_wsti
        else:
            self.wr_packet_pr2sw_w = 0
            self.wr_packet_w2e_esto_w = 0

    @always_comb
    def rdrq_switch_logic(self):
        if (self.rdrq_packet_w2e_wsti['rd_en'] == 1):
            if (self.rdrq_packet_w2e_wsti['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                    == self.glb_tile_id):
                self.rdrq_packet_pr2sw_w = self.rdrq_packet_w2e_wsti
                self.rdrq_packet_w2e_esto_w = 0
            else:
                self.rdrq_packet_pr2sw_w = 0
                self.rdrq_packet_w2e_esto_w = self.rdrq_packet_w2e_wsti
        else:
            self.rdrq_packet_pr2sw_w = 0
            self.rdrq_packet_w2e_esto_w = 0

    @always_comb
    def rdrs_switch_logic(self):
        if self.rdrs_packet_sw2pr['rd_data_valid'] == 1:
            self.rdrs_packet_w2e_esto_w = self.rdrs_packet_sw2pr
        elif self.rdrs_packet_w2e_wsti['rd_data_valid'] == 1:
            self.rdrs_packet_w2e_esto_w = self.rdrs_packet_w2e_wsti
        else:
            self.rdrs_packet_w2e_esto_w = 0
        if self.rdrs_packet_e2w_esti['rd_data_valid'] == 1:
            self.rdrs_packet_e2w_wsto_w = self.rdrs_packet_e2w_esti
        else:
            self.rdrs_packet_e2w_wsto_w = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_pipeline(self):
        if self.reset:
            self.wr_packet_w2e_esto = 0
            self.wr_packet_pr2sw = 0
            self.rdrq_packet_w2e_esto = 0
            self.rdrq_packet_pr2sw = 0
            self.rdrs_packet_w2e_esto = 0
            self.rdrs_packet_e2w_wsto = 0
        else:
            self.wr_packet_w2e_esto = self.wr_packet_w2e_esto_w
            self.wr_packet_pr2sw = self.wr_packet_pr2sw_w
            self.rdrq_packet_w2e_esto = self.rdrq_packet_w2e_esto_w
            self.rdrq_packet_pr2sw = self.rdrq_packet_pr2sw_w
            self.rdrs_packet_w2e_esto = self.rdrs_packet_w2e_esto_w
            self.rdrs_packet_e2w_wsto = self.rdrs_packet_e2w_wsto_w
