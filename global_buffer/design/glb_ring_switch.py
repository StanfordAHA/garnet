from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen


class GlbRingSwitch(Generator):
    def __init__(self, _params: GlobalBufferParams, wr_channel=True, rd_channel=True):
        name = "glb_ring_switch"
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
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        if self.wr_channel:
            self.wr_packet_w2e_wsti = self.input("wr_packet_w2e_wsti", self.header.wr_packet_t)
            self.wr_packet_e2w_wsto = self.output("wr_packet_e2w_wsto", self.header.wr_packet_t)
            self.wr_packet_e2w_esti = self.input("wr_packet_e2w_esti", self.header.wr_packet_t)
            self.wr_packet_w2e_esto = self.output("wr_packet_w2e_esto", self.header.wr_packet_t)
            self.wr_packet_dma2ring = self.input("wr_packet_dma2ring", self.header.wr_packet_t)
            self.wr_packet_ring2bank = self.output("wr_packet_ring2bank", self.header.wr_packet_t)

        if self.rd_channel:
            self.rdrq_packet_w2e_wsti = self.input("rdrq_packet_w2e_wsti", self.header.rdrq_packet_t)
            self.rdrq_packet_e2w_wsto = self.output("rdrq_packet_e2w_wsto", self.header.rdrq_packet_t)
            self.rdrq_packet_e2w_esti = self.input("rdrq_packet_e2w_esti", self.header.rdrq_packet_t)
            self.rdrq_packet_w2e_esto = self.output("rdrq_packet_w2e_esto", self.header.rdrq_packet_t)

            self.rdrs_packet_w2e_wsti = self.input("rdrs_packet_w2e_wsti", self.header.rdrs_packet_t)
            self.rdrs_packet_e2w_wsto = self.output("rdrs_packet_e2w_wsto", self.header.rdrs_packet_t)
            self.rdrs_packet_e2w_esti = self.input("rdrs_packet_e2w_esti", self.header.rdrs_packet_t)
            self.rdrs_packet_w2e_esto = self.output("rdrs_packet_w2e_esto", self.header.rdrs_packet_t)

            self.rdrq_packet_dma2ring = self.input("rdrq_packet_dma2ring", self.header.rdrq_packet_t)
            self.rdrq_packet_ring2bank = self.output("rdrq_packet_ring2bank", self.header.rdrq_packet_t)
            self.rdrs_packet_bank2ring = self.input("rdrs_packet_bank2ring", self.header.rdrs_packet_t)
            self.rdrs_packet_ring2dma = self.output("rdrs_packet_ring2dma", self.header.rdrs_packet_t)

        self.cfg_ld_dma_on = self.input("cfg_ld_dma_on", 1)
        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)
        self.clk_en_ring2bank = self.output("clk_en_ring2bank", 1)

        # local variables
        if self.wr_channel:
            self.wr_packet_w2e_wsti_muxed = self.var("wr_packet_w2e_wsti_muxed", self.header.wr_packet_t)
            self.wr_packet_w2e_esto_w = self.var("wr_packet_w2e_esto_w", self.header.wr_packet_t)
            self.wr_packet_e2w_esti_muxed = self.var("wr_packet_e2w_esti_muxed", self.header.wr_packet_t)
            self.wr_packet_e2w_wsto_w = self.var("wr_packet_e2w_wsto_w", self.header.wr_packet_t)
            self.wr_packet_ring2bank_w = self.var("wr_packet_ring2bank_w", self.header.wr_packet_t)

        if self.rd_channel:
            self.rdrq_packet_w2e_wsti_muxed = self.var("rdrq_packet_w2e_wsti_muxed", self.header.rdrq_packet_t)
            self.rdrq_packet_w2e_esto_w = self.var("rdrq_packet_w2e_esto_w", self.header.rdrq_packet_t)
            self.rdrq_packet_e2w_esti_muxed = self.var("rdrq_packet_e2w_esti_muxed", self.header.rdrq_packet_t)
            self.rdrq_packet_e2w_wsto_w = self.var("rdrq_packet_e2w_wsto_w", self.header.rdrq_packet_t)
            self.rdrq_packet_ring2bank_w = self.var("rdrq_packet_ring2bank_w", self.header.rdrq_packet_t)

            self.rdrs_packet_w2e_wsti_muxed = self.var("rdrs_packet_w2e_wsti_muxed", self.header.rdrs_packet_t)
            self.rdrs_packet_w2e_esto_w = self.var("rdrs_packet_w2e_esto_w", self.header.rdrs_packet_t)
            self.rdrs_packet_e2w_esti_muxed = self.var("rdrs_packet_e2w_esti_muxed", self.header.rdrs_packet_t)
            self.rdrs_packet_e2w_wsto_w = self.var("rdrs_packet_e2w_wsto_w", self.header.rdrs_packet_t)
            self.rdrs_packet_ring2dma_w = self.var("rdrs_packet_ring2dma_w", self.header.rdrs_packet_t)

        # localparam
        self.tile_sel_msb = _params.bank_addr_width + _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1
        self.tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width

        self.add_always(self.packet_wsti_muxed_logic)
        self.add_always(self.packet_esti_muxed_logic)

        if self.wr_channel:
            self.add_always(self.wr_packet_switch_logic)

        if self.rd_channel:
            self.add_always(self.rdrq_packet_switch_logic)
            self.add_always(self.rdrs_packet_switch_logic)

        self.add_always(self.packet_pipeline)
        self.add_always(self.rdrs_ring2dma)
        self.add_ring2bank_clk_en()

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
        if (self.wr_packet_dma2ring['wr_en'] == 1):
            if (self.wr_packet_dma2ring['wr_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id):
                self.wr_packet_ring2bank_w = self.wr_packet_dma2ring
                self.wr_packet_w2e_esto_w = 0
            else:
                self.wr_packet_ring2bank_w = 0
                self.wr_packet_w2e_esto_w = self.wr_packet_dma2ring
        elif (self.wr_packet_w2e_wsti_muxed['wr_en'] == 1):
            if (self.wr_packet_w2e_wsti_muxed['wr_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id):
                self.wr_packet_ring2bank_w = self.wr_packet_w2e_wsti_muxed
                self.wr_packet_w2e_esto_w = 0
            else:
                self.wr_packet_ring2bank_w = 0
                self.wr_packet_w2e_esto_w = self.wr_packet_w2e_wsti_muxed
        else:
            self.wr_packet_ring2bank_w = 0
            self.wr_packet_w2e_esto_w = 0
        self.wr_packet_e2w_wsto_w = self.wr_packet_e2w_esti_muxed

    @always_comb
    def rdrq_packet_switch_logic(self):
        if (self.rdrq_packet_dma2ring['rd_en'] == 1):
            if (self.rdrq_packet_dma2ring['rd_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id):
                self.rdrq_packet_ring2bank_w = self.rdrq_packet_dma2ring
                self.rdrq_packet_w2e_esto_w = 0
            else:
                self.rdrq_packet_ring2bank_w = 0
                self.rdrq_packet_w2e_esto_w = self.rdrq_packet_dma2ring
        elif (self.rdrq_packet_w2e_wsti_muxed['rd_en'] == 1):
            if (self.rdrq_packet_w2e_wsti_muxed['rd_addr'][self.tile_sel_msb, self.tile_sel_lsb] == self.glb_tile_id):
                self.rdrq_packet_ring2bank_w = self.rdrq_packet_w2e_wsti_muxed
                self.rdrq_packet_w2e_esto_w = 0
            else:
                self.rdrq_packet_ring2bank_w = 0
                self.rdrq_packet_w2e_esto_w = self.rdrq_packet_w2e_wsti_muxed
        else:
            self.rdrq_packet_ring2bank_w = 0
            self.rdrq_packet_w2e_esto_w = 0
        self.rdrq_packet_e2w_wsto_w = self.rdrq_packet_e2w_esti_muxed

    @always_comb
    def rdrs_packet_switch_logic(self):
        if (self.rdrs_packet_bank2ring['rd_data_valid'] == 1):
            self.rdrs_packet_w2e_esto_w = self.rdrs_packet_bank2ring
        else:
            if (self.rdrs_packet_w2e_wsti_muxed['rd_data_valid'] & self.cfg_ld_dma_on):
                self.rdrs_packet_w2e_esto_w = 0
            else:
                self.rdrs_packet_w2e_esto_w = self.rdrs_packet_w2e_wsti_muxed

        if (self.rdrs_packet_w2e_wsti_muxed['rd_data_valid'] & self.cfg_ld_dma_on):
            self.rdrs_packet_ring2dma_w = self.rdrs_packet_w2e_wsti_muxed
        else:
            self.rdrs_packet_ring2dma_w = 0
        self.rdrs_packet_e2w_wsto_w = self.rdrs_packet_e2w_esti_muxed

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_pipeline(self):
        if self.reset:
            if self.wr_channel:
                self.wr_packet_w2e_esto = 0
                self.wr_packet_e2w_wsto = 0
                self.wr_packet_ring2bank = 0
            if self.rd_channel:
                self.rdrq_packet_w2e_esto = 0
                self.rdrq_packet_e2w_wsto = 0
                self.rdrq_packet_ring2bank = 0
                self.rdrs_packet_w2e_esto = 0
                self.rdrs_packet_e2w_wsto = 0
        else:
            if self.wr_channel:
                self.wr_packet_w2e_esto = self.wr_packet_w2e_esto_w
                self.wr_packet_e2w_wsto = self.wr_packet_e2w_wsto_w
                self.wr_packet_ring2bank = self.wr_packet_ring2bank_w
            if self.rd_channel:
                self.rdrq_packet_w2e_esto = self.rdrq_packet_w2e_esto_w
                self.rdrq_packet_e2w_wsto = self.rdrq_packet_e2w_wsto_w
                self.rdrq_packet_ring2bank = self.rdrq_packet_ring2bank_w
                self.rdrs_packet_w2e_esto = self.rdrs_packet_w2e_esto_w
                self.rdrs_packet_e2w_wsto = self.rdrs_packet_e2w_wsto_w

    @always_comb
    def rdrs_ring2dma(self):
        self.rdrs_packet_ring2dma = self.rdrs_packet_ring2dma_w

    def add_ring2bank_clk_en(self):
        if self.wr_channel:
            self.wr_clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_wr_delay + self._params.wr_clk_en_margin)
            self.ring2bank_wr_clk_en = self.var("ring2bank_wr_clk_en", 1)
            self.add_child("ring2bank_wr_clk_en_gen",
                           self.wr_clk_en_gen,
                           clk=self.clk,
                           reset=self.reset,
                           enable=self.wr_packet_ring2bank_w['wr_en'],
                           clk_en=self.ring2bank_wr_clk_en
                           )
        if self.rd_channel:
            self.rd_clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_rd_delay + self._params.rd_clk_en_margin)
            self.ring2bank_rd_clk_en = self.var("ring2bank_rd_clk_en", 1)
            self.add_child("ring2bank_rd_clk_en_gen",
                           self.rd_clk_en_gen,
                           clk=self.clk,
                           reset=self.reset,
                           enable=self.rdrq_packet_ring2bank_w['rd_en'],
                           clk_en=self.ring2bank_rd_clk_en
                           )
        if self.wr_channel and self.rd_channel:
            self.wire(self.clk_en_ring2bank, self.ring2bank_wr_clk_en | self.ring2bank_rd_clk_en)
        elif self.wr_channel:
            self.wire(self.clk_en_ring2bank, self.ring2bank_wr_clk_en)
        else:
            self.wire(self.clk_en_ring2bank, self.ring2bank_rd_clk_en)
