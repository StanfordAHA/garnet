from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbCoreProcRouter(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_core_proc_router")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
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

        self.wr_packet_pr2sw = self.output(
            "wr_packet_pr2sw", self.header.wr_packet_t)
        self.rdrq_packet_pr2sw = self.output(
            "rdrq_packet_pr2sw", self.header.rdrq_packet_t)
        self.rdrs_packet_sw2pr = self.input(
            "rdrs_packet_sw2pr", self.header.rdrs_packet_t)

        # local variables
        self.packet_w2e_wsti_d1 = self.var(
            "packet_w2e_wsti_d1", self.header.packet_t)
        self.packet_e2w_esti_d1 = self.var(
            "packet_e2w_esti_d1", self.header.packet_t)
        self.rdrs_packet_sw2pr_d1 = self.var(
            "rdrs_packet_sw2pr_d1", self.header.rdrs_packet_t)
        self.rdrq_packet_pr2sw_filtered = self.var(
            "rdrq_packet_pr2sw_filtered", self.header.rdrq_packet_t)
        self.rdrq_packet_pr2sw_muxed = self.var(
            "rdrq_packet_pr2sw_muxed", self.header.rdrq_packet_t)
        self.wr_packet_pr2sw_filtered = self.var(
            "wr_packet_pr2sw_filtered", self.header.wr_packet_t)
        self.wr_packet_pr2sw_muxed = self.var(
            "wr_packet_pr2sw_muxed", self.header.wr_packet_t)

        # localparam
        self.packet_addr_tile_sel_msb = _params.bank_addr_width + \
            _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1
        self.packet_addr_tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width

        self.add_is_even_stmt()
        self.add_always(self.packet_pipeline)
        self.add_always(self.rdrs_packet_pipeline)
        self.add_always(self.rq_assign)
        self.add_always(self.rs_assign)

    def add_is_even_stmt(self):
        self.is_even = self.var("is_even", 1)
        self.wire(self.is_even, self.glb_tile_id[0] == 0)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def packet_pipeline(self):
        if self.reset:
            self.packet_w2e_wsti_d1 = 0
            self.packet_e2w_esti_d1 = 0
        else:
            self.packet_w2e_wsti_d1 = self.packet_w2e_wsti
            self.packet_e2w_esti_d1 = self.packet_e2w_esti

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrs_packet_pipeline(self):
        if self.reset:
            self.rdrs_packet_sw2pr_d1 = 0
        else:
            self.rdrs_packet_sw2pr_d1 = self.rdrs_packet_sw2pr

    @always_comb
    def rq_assign(self):
        # TODO: Kratos currently does not support struct of struct
        # packet output
        for port in self.header.wr_packet_ports + self.header.rdrq_packet_ports:
            self.packet_w2e_esto[port] = self.packet_w2e_wsti_d1[port]
            self.packet_e2w_wsto[port] = self.packet_e2w_esti_d1[port]

        # packet to core
        if self.is_even:
            for port in self.header.wr_packet_ports:
                self.wr_packet_pr2sw_muxed[port] = self.packet_w2e_esto[port]
        else:
            for port in self.header.wr_packet_ports:
                self.wr_packet_pr2sw_muxed[port] = self.packet_e2w_wsto[port]
        if self.is_even:
            for port in self.header.rdrq_packet_ports:
                self.rdrq_packet_pr2sw_muxed[port] = self.packet_w2e_esto[port]
        else:
            for port in self.header.rdrq_packet_ports:
                self.rdrq_packet_pr2sw_muxed[port] = self.packet_e2w_wsto[port]

        if (self.wr_packet_pr2sw_muxed['wr_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                == self.glb_tile_id):
            for port in self.header.wr_packet_ports:
                self.wr_packet_pr2sw_filtered[port] = self.wr_packet_pr2sw_muxed[port]
        else:
            for port in self.header.wr_packet_ports:
                self.wr_packet_pr2sw_filtered[port] = 0

        if (self.rdrq_packet_pr2sw_muxed['rd_addr'][self.packet_addr_tile_sel_msb, self.packet_addr_tile_sel_lsb]
                == self.glb_tile_id):
            for port in self.header.rdrq_packet_ports:
                self.rdrq_packet_pr2sw_filtered[port] = self.rdrq_packet_pr2sw_muxed[port]
        else:
            for port in self.header.rdrq_packet_ports:
                self.rdrq_packet_pr2sw_filtered[port] = 0

        self.wr_packet_pr2sw = self.wr_packet_pr2sw_filtered
        self.rdrq_packet_pr2sw = self.rdrq_packet_pr2sw_filtered

    @always_comb
    def rs_assign(self):
        if (self.is_even == 1) & (self.rdrs_packet_sw2pr_d1['rd_data_valid'] == 1):
            for port in self.header.rdrs_packet_ports:
                self.packet_w2e_esto[port] = self.rdrs_packet_sw2pr_d1[port]
        else:
            for port in self.header.rdrs_packet_ports:
                self.packet_w2e_esto[port] = self.packet_w2e_wsti_d1[port]

        if (self.is_even == 0) & (self.rdrs_packet_sw2pr_d1['rd_data_valid'] == 1):
            for port in self.header.rdrs_packet_ports:
                self.packet_e2w_wsto[port] = self.rdrs_packet_sw2pr_d1[port]
        else:
            for port in self.header.rdrs_packet_ports:
                self.packet_e2w_wsto[port] = self.packet_e2w_esti_d1[port]
