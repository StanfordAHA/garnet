from kratos import Generator, always_ff, posedge, always_comb, clock_en, clog2, const, concat
from kratos.util import to_magma
from global_buffer.design.glb_tile import GlbTile
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.pipeline import Pipeline
from gemstone.generator.from_magma import FromMagma


class GlobalBuffer(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("global_buffer")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.core_stall = self.input("core_stall", self._params.num_glb_tiles)
        self.rtr_stall = self.input("rtr_stall", self._params.num_glb_tiles)
        self.pcfg_rtr_stall = self.input("pcfg_rtr_stall", self._params.num_glb_tiles)
        self.reset = self.reset("reset")
        # TODO: Why cgra_stall has same width as num_glb_tiles
        self.cgra_stall_in = self.input("cgra_stall_in", self._params.num_glb_tiles)
        self.cgra_stall = self.output(
            "cgra_stall", 1, size=[self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)

        self.proc_wr_en = self.input("proc_wr_en", 1)
        self.proc_wr_strb = self.input("proc_wr_strb", self._params.bank_data_width // 8)
        self.proc_wr_addr = self.input("proc_wr_addr", self._params.glb_addr_width)
        self.proc_wr_data = self.input("proc_wr_data", self._params.bank_data_width)
        self.proc_rd_en = self.input("proc_rd_en", 1)
        self.proc_rd_addr = self.input("proc_rd_addr", self._params.glb_addr_width)
        self.proc_rd_data = self.output("proc_rd_data", self._params.bank_data_width)
        self.proc_rd_data_valid = self.output("proc_rd_data_valid", 1)

        self.if_cfg_wr_en = self.input("if_cfg_wr_en", 1)
        self.if_cfg_wr_addr = self.input("if_cfg_wr_addr", self._params.axi_addr_width)
        self.if_cfg_wr_data = self.input("if_cfg_wr_data", self._params.axi_data_width)
        self.if_cfg_rd_en = self.input("if_cfg_rd_en", 1)
        self.if_cfg_rd_addr = self.input("if_cfg_rd_addr", self._params.axi_addr_width)
        self.if_cfg_rd_data = self.output("if_cfg_rd_data", self._params.axi_data_width)
        self.if_cfg_rd_data_valid = self.output("if_cfg_rd_data_valid", 1)

        self.if_sram_cfg_wr_en = self.input("if_sram_cfg_wr_en", 1)
        self.if_sram_cfg_wr_addr = self.input("if_sram_cfg_wr_addr", self._params.glb_addr_width)
        self.if_sram_cfg_wr_data = self.input("if_sram_cfg_wr_data", self._params.axi_data_width)
        self.if_sram_cfg_rd_en = self.input("if_sram_cfg_rd_en", 1)
        self.if_sram_cfg_rd_addr = self.input("if_sram_cfg_rd_addr", self._params.glb_addr_width)
        self.if_sram_cfg_rd_data = self.output("if_sram_cfg_rd_data", self._params.axi_data_width)
        self.if_sram_cfg_rd_data_valid = self.output("if_sram_cfg_rd_data_valid", 1)

        self.cgra_cfg_jtag_gc2glb_wr_en = self.input("cgra_cfg_jtag_gc2glb_wr_en", 1)
        self.cgra_cfg_jtag_gc2glb_rd_en = self.input("cgra_cfg_jtag_gc2glb_rd_en", 1)
        self.cgra_cfg_jtag_gc2glb_addr = self.input("cgra_cfg_jtag_gc2glb_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_gc2glb_data = self.input("cgra_cfg_jtag_gc2glb_data", self._params.cgra_cfg_data_width)

        self.strm_data_f2g = self.input("strm_data_f2g", self._params.cgra_data_width, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.strm_data_valid_f2g = self.input("strm_data_valid_f2g", 1, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.strm_data_g2f = self.output("strm_data_g2f", self._params.cgra_data_width, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.strm_data_valid_g2f = self.output("strm_data_valid_g2f", 1, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)

        self.cgra_cfg_g2f_cfg_wr_en = self.output("cgra_cfg_g2f_cfg_wr_en", 1, size=[
                                                  self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.cgra_cfg_g2f_cfg_rd_en = self.output("cgra_cfg_g2f_cfg_rd_en", 1, size=[
                                                  self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.cgra_cfg_g2f_cfg_addr = self.output("cgra_cfg_g2f_cfg_addr", self._params.cgra_cfg_addr_width, size=[
                                                 self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.cgra_cfg_g2f_cfg_data = self.output("cgra_cfg_g2f_cfg_data", self._params.cgra_cfg_data_width, size=[
                                                 self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)

        self.strm_g2f_start_pulse = self.input("strm_g2f_start_pulse", self._params.num_glb_tiles)
        self.strm_f2g_start_pulse = self.input("strm_f2g_start_pulse", self._params.num_glb_tiles)
        self.pcfg_start_pulse = self.input("pcfg_start_pulse", self._params.num_glb_tiles)
        self.strm_f2g_interrupt_pulse = self.output("strm_f2g_interrupt_pulse", self._params.num_glb_tiles)
        self.strm_g2f_interrupt_pulse = self.output("strm_g2f_interrupt_pulse", self._params.num_glb_tiles)
        self.pcfg_g2f_interrupt_pulse = self.output("pcfg_g2f_interrupt_pulse", self._params.num_glb_tiles)

        # local variables
        self.cgra_cfg_jtag_gc2glb_wr_en_d = self.var("cgra_cfg_jtag_gc2glb_wr_en_d", 1)
        self.cgra_cfg_jtag_gc2glb_rd_en_d = self.var("cgra_cfg_jtag_gc2glb_rd_en_d", 1)
        self.cgra_cfg_jtag_gc2glb_addr_d = self.var("cgra_cfg_jtag_gc2glb_addr_d", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_gc2glb_data_d = self.var("cgra_cfg_jtag_gc2glb_data_d", self._params.cgra_cfg_data_width)

        self.proc_packet_d = self.var("proc_packet_d", self.header.packet_t)

        self.proc_packet_w2e_wsti = self.var(
            "proc_packet_w2e_wsti", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)
        self.proc_packet_w2e_esto = self.var(
            "proc_packet_w2e_esto", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)
        self.proc_packet_e2w_esti = self.var(
            "proc_packet_e2w_esti", self.header.rdrs_packet_t, size=self._params.num_glb_tiles, packed=True)
        self.proc_packet_e2w_wsto = self.var(
            "proc_packet_e2w_wsto", self.header.rdrs_packet_t, size=self._params.num_glb_tiles, packed=True)

        self.strm_packet_e2w_esti = self.var(
            "strm_packet_e2w_esti", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)
        self.strm_packet_w2e_wsti = self.var(
            "strm_packet_w2e_wsti", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)
        self.strm_packet_e2w_wsto = self.var(
            "strm_packet_e2w_wsto", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)
        self.strm_packet_w2e_esto = self.var(
            "strm_packet_w2e_esto", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)

        self.pcfg_packet_e2w_esti = self.var(
            "pcfg_packet_e2w_esti", self.header.rd_packet_t, size=self._params.num_glb_tiles, packed=True)
        self.pcfg_packet_w2e_wsti = self.var(
            "pcfg_packet_w2e_wsti", self.header.rd_packet_t, size=self._params.num_glb_tiles, packed=True)
        self.pcfg_packet_e2w_wsto = self.var(
            "pcfg_packet_e2w_wsto", self.header.rd_packet_t, size=self._params.num_glb_tiles, packed=True)
        self.pcfg_packet_w2e_esto = self.var(
            "pcfg_packet_w2e_esto", self.header.rd_packet_t, size=self._params.num_glb_tiles, packed=True)

        self.cfg_tile_connected = self.var("cfg_tile_connected", self._params.num_glb_tiles + 1)
        self.cfg_pcfg_tile_connected = self.var("cfg_pcfg_tile_connected", self._params.num_glb_tiles + 1)
        self.wire(self.cfg_tile_connected[0], 0)
        self.wire(self.cfg_pcfg_tile_connected[0], 0)

        self.cgra_cfg_jtag_wsti_wr_en = self.var(
            "cgra_cfg_jtag_wsti_wr_en", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_wsti_rd_en = self.var(
            "cgra_cfg_jtag_wsti_rd_en", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_wsti_addr = self.var(
            "cgra_cfg_jtag_wsti_addr", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_wsti_data = self.var(
            "cgra_cfg_jtag_wsti_data", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_jtag_esto_wr_en = self.var(
            "cgra_cfg_jtag_esto_wr_en", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_esto_rd_en = self.var(
            "cgra_cfg_jtag_esto_rd_en", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_esto_addr = self.var(
            "cgra_cfg_jtag_esto_addr", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_esto_data = self.var(
            "cgra_cfg_jtag_esto_data", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_jtag_wsti_rd_en_bypass = self.var("cgra_cfg_jtag_wsti_rd_en_bypass", 1,
                                                        size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_wsti_addr_bypass = self.var("cgra_cfg_jtag_wsti_addr_bypass",
                                                       self._params.cgra_cfg_addr_width,
                                                       size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_esto_rd_en_bypass = self.var("cgra_cfg_jtag_esto_rd_en_bypass", 1,
                                                        size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_esto_addr_bypass = self.var("cgra_cfg_jtag_esto_addr_bypass",
                                                       self._params.cgra_cfg_addr_width,
                                                       size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_pcfg_wsti_wr_en = self.var(
            "cgra_cfg_pcfg_wsti_wr_en", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_wsti_rd_en = self.var(
            "cgra_cfg_pcfg_wsti_rd_en", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_wsti_addr = self.var(
            "cgra_cfg_pcfg_wsti_addr", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_wsti_data = self.var(
            "cgra_cfg_pcfg_wsti_data", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_pcfg_esto_wr_en = self.var(
            "cgra_cfg_pcfg_esto_wr_en", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_esto_rd_en = self.var(
            "cgra_cfg_pcfg_esto_rd_en", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_esto_addr = self.var(
            "cgra_cfg_pcfg_esto_addr", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_esto_data = self.var(
            "cgra_cfg_pcfg_esto_data", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.strm_f2g_interrupt_pulse_w = self.var("strm_f2g_interrupt_pulse_w", self._params.num_glb_tiles)
        self.strm_f2g_interrupt_pulse_d = self.var("strm_f2g_interrupt_pulse_d", self._params.num_glb_tiles)
        self.wire(self.strm_f2g_interrupt_pulse_d, self.strm_f2g_interrupt_pulse)

        self.strm_g2f_interrupt_pulse_w = self.var("strm_g2f_interrupt_pulse_w", self._params.num_glb_tiles)
        self.strm_g2f_interrupt_pulse_d = self.var("strm_g2f_interrupt_pulse_d", self._params.num_glb_tiles)
        self.wire(self.strm_g2f_interrupt_pulse_d, self.strm_g2f_interrupt_pulse)

        self.pcfg_g2f_interrupt_pulse_w = self.var("pcfg_g2f_interrupt_pulse_w", self._params.num_glb_tiles)
        self.pcfg_g2f_interrupt_pulse_d = self.var("pcfg_g2f_interrupt_pulse_d", self._params.num_glb_tiles)
        self.wire(self.pcfg_g2f_interrupt_pulse_d, self.pcfg_g2f_interrupt_pulse)

        self.cgra_cfg_g2f_cfg_wr_en_w = self.var("cgra_cfg_g2f_cfg_wr_en_w", 1, size=[
                                                 self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.cgra_cfg_g2f_cfg_wr_en_d = self.var("cgra_cfg_g2f_cfg_wr_en_d", 1, size=[
                                                 self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.wire(self.cgra_cfg_g2f_cfg_wr_en_d, self.cgra_cfg_g2f_cfg_wr_en)

        self.cgra_cfg_g2f_cfg_rd_en_w = self.var("cgra_cfg_g2f_cfg_rd_en_w", 1, size=[
                                                 self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.cgra_cfg_g2f_cfg_rd_en_d = self.var("cgra_cfg_g2f_cfg_rd_en_d", 1, size=[
                                                 self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.wire(self.cgra_cfg_g2f_cfg_rd_en_d, self.cgra_cfg_g2f_cfg_rd_en)

        self.cgra_cfg_g2f_cfg_addr_w = self.var("cgra_cfg_g2f_cfg_addr_w", self._params.cgra_cfg_addr_width, size=[
                                                self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.cgra_cfg_g2f_cfg_addr_d = self.var("cgra_cfg_g2f_cfg_addr_d", self._params.cgra_cfg_addr_width, size=[
                                                self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.wire(self.cgra_cfg_g2f_cfg_addr_d, self.cgra_cfg_g2f_cfg_addr)

        self.cgra_cfg_g2f_cfg_data_w = self.var("cgra_cfg_g2f_cfg_data_w", self._params.cgra_cfg_data_width, size=[
                                                self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.cgra_cfg_g2f_cfg_data_d = self.var("cgra_cfg_g2f_cfg_data_d", self._params.cgra_cfg_data_width, size=[
                                                self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.wire(self.cgra_cfg_g2f_cfg_data_d, self.cgra_cfg_g2f_cfg_data)

        self.strm_data_f2g_w = self.var("strm_data_f2g_w", self._params.cgra_data_width, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.strm_data_f2g_d = self.var("strm_data_f2g_d", self._params.cgra_data_width, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.wire(self.strm_data_f2g, self.strm_data_f2g_w)

        self.strm_data_valid_f2g_w = self.var("strm_data_valid_f2g_w", 1, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.strm_data_valid_f2g_d = self.var("strm_data_valid_f2g_d", 1, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.wire(self.strm_data_valid_f2g, self.strm_data_valid_f2g_w)

        self.strm_data_g2f_w = self.var("strm_data_g2f_w", self._params.cgra_data_width, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.strm_data_g2f_d = self.var("strm_data_g2f_d", self._params.cgra_data_width, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.wire(self.strm_data_g2f_d, self.strm_data_g2f)

        self.strm_data_valid_g2f_w = self.var("strm_data_valid_g2f_w", 1, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.strm_data_valid_g2f_d = self.var("strm_data_valid_g2f_d", 1, size=[
            self._params.num_glb_tiles, self._params.cgra_per_glb], packed=True)
        self.wire(self.strm_data_valid_g2f_d, self.strm_data_valid_g2f)

        # interface
        if_cfg_tile2tile = GlbConfigInterface(
            addr_width=self._params.axi_addr_width, data_width=self._params.axi_data_width)
        if_sram_cfg_tile2tile = GlbConfigInterface(
            addr_width=self._params.glb_addr_width, data_width=self._params.axi_data_width)

        self.if_cfg_list = []
        self.if_sram_cfg_list = []
        for i in range(self._params.num_glb_tiles + 1):
            self.if_cfg_list.append(self.interface(
                if_cfg_tile2tile, f"if_cfg_tile2tile_{i}"))
            self.if_sram_cfg_list.append(self.interface(
                if_sram_cfg_tile2tile, f"if_sram_cfg_tile2tile_{i}"))

        # GLS pipeline
        self.core_stall_d = self.var("core_stall_d", self._params.num_glb_tiles)
        self.rtr_stall_d = self.var("rtr_stall_d", self._params.num_glb_tiles)
        self.pcfg_rtr_stall_d = self.var("pcfg_rtr_stall_d", self._params.num_glb_tiles)
        self.cgra_stall_in_d = self.var("cgra_stall_in_d", self._params.num_glb_tiles)
        self.strm_g2f_start_pulse_d = self.var("strm_g2f_start_pulse_d", self._params.num_glb_tiles)
        self.strm_f2g_start_pulse_d = self.var("strm_f2g_start_pulse_d", self._params.num_glb_tiles)
        self.pcfg_start_pulse_d = self.var("pcfg_start_pulse_d", self._params.num_glb_tiles)
        self.gls_in = concat(self.core_stall, self.rtr_stall, self.pcfg_rtr_stall, self.cgra_stall_in, self.strm_g2f_start_pulse,
                             self.strm_f2g_start_pulse, self.pcfg_start_pulse)
        self.gls_out = concat(self.core_stall_d, self.rtr_stall_d, self.pcfg_rtr_stall_d, self.cgra_stall_in_d, self.strm_g2f_start_pulse_d,
                              self.strm_f2g_start_pulse_d, self.pcfg_start_pulse_d)

        self.gls_pipeline = Pipeline(width=self.gls_in.width, depth=self._params.gls_pipeline_depth)
        self.add_child("gls_pipeline",
                       self.gls_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.gls_in,
                       out_=self.gls_out)
        for i in range(self._params.num_glb_tiles):
            self.wire(self.cgra_stall[i], concat(*[self.cgra_stall_in_d[i]] * self._params.cgra_per_glb))

        # GLB Tiles
        self.glb_tile = []
        for i in range(self._params.num_glb_tiles):
            self.glb_tile.append(GlbTile(_params=self._params))

        self.wire(self.if_cfg_list[-1].rd_data, 0)
        self.wire(self.if_cfg_list[-1].rd_data_valid, 0)
        self.wire(self.if_sram_cfg_list[-1].rd_data, 0)
        self.wire(self.if_sram_cfg_list[-1].rd_data_valid, 0)

        self.add_glb_tile()
        self.add_always(self.left_edge_proc_ff)
        self.add_always(self.left_edge_cfg_ff)
        self.add_always(self.left_edge_sram_cfg_ff)
        self.add_always(self.left_edge_cgra_cfg_ff)
        self.tile2tile_e2w_wiring()
        self.tile2tile_w2e_wiring()
        self.add_always(self.tile2tile_w2e_cfg_wiring)
        self.add_always(self.interrupt_pipeline)
        self.add_always(self.strm_data_pipeline)
        self.add_always(self.cgra_cfg_pcfg_pipeline)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def left_edge_proc_ff(self):
        if self.reset:
            self.proc_packet_d['wr']['wr_en'] = 0
            self.proc_packet_d['wr']['wr_strb'] = 0
            self.proc_packet_d['wr']['wr_addr'] = 0
            self.proc_packet_d['wr']['wr_data'] = 0
            self.proc_packet_d['rdrq']['rd_en'] = 0
            self.proc_packet_d['rdrq']['rd_src_tile'] = 0
            self.proc_packet_d['rdrq']['rd_addr'] = 0
            self.proc_packet_d['rdrs']['rd_data'] = 0
            self.proc_packet_d['rdrs']['rd_dst_tile'] = 0
            self.proc_packet_d['rdrs']['rd_data_valid'] = 0
            self.proc_rd_data = 0
            self.proc_rd_data_valid = 0
        else:
            self.proc_packet_d['wr']['wr_en'] = self.proc_wr_en
            self.proc_packet_d['wr']['wr_strb'] = self.proc_wr_strb
            self.proc_packet_d['wr']['wr_addr'] = self.proc_wr_addr
            self.proc_packet_d['wr']['wr_data'] = self.proc_wr_data
            self.proc_packet_d['rdrq']['rd_en'] = self.proc_rd_en
            self.proc_packet_d['rdrq']['rd_src_tile'] = 0
            self.proc_packet_d['rdrq']['rd_addr'] = self.proc_rd_addr
            self.proc_packet_d['rdrs']['rd_data'] = 0
            self.proc_packet_d['rdrs']['rd_dst_tile'] = 0
            self.proc_packet_d['rdrs']['rd_data_valid'] = 0
            self.proc_rd_data = self.proc_packet_e2w_wsto[0]['rd_data']
            self.proc_rd_data_valid = self.proc_packet_e2w_wsto[0]['rd_data_valid']

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def left_edge_cfg_ff(self):
        if self.reset:
            self.if_cfg_list[0].wr_en = 0
            self.if_cfg_list[0].wr_addr = 0
            self.if_cfg_list[0].wr_data = 0
            self.if_cfg_list[0].rd_en = 0
            self.if_cfg_list[0].rd_addr = 0
            self.if_cfg_rd_data = 0
            self.if_cfg_rd_data_valid = 0
        else:
            self.if_cfg_list[0].wr_en = self.if_cfg_wr_en
            self.if_cfg_list[0].wr_addr = self.if_cfg_wr_addr
            self.if_cfg_list[0].wr_data = self.if_cfg_wr_data
            self.if_cfg_list[0].rd_en = self.if_cfg_rd_en
            self.if_cfg_list[0].rd_addr = self.if_cfg_rd_addr
            self.if_cfg_rd_data = self.if_cfg_list[0].rd_data
            self.if_cfg_rd_data_valid = self.if_cfg_list[0].rd_data_valid

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def left_edge_sram_cfg_ff(self):
        if self.reset:
            self.if_sram_cfg_list[0].wr_en = 0
            self.if_sram_cfg_list[0].wr_addr = 0
            self.if_sram_cfg_list[0].wr_data = 0
            self.if_sram_cfg_list[0].rd_en = 0
            self.if_sram_cfg_list[0].rd_addr = 0
            self.if_sram_cfg_rd_data = 0
            self.if_sram_cfg_rd_data_valid = 0
        else:
            self.if_sram_cfg_list[0].wr_en = self.if_sram_cfg_wr_en
            self.if_sram_cfg_list[0].wr_addr = self.if_sram_cfg_wr_addr
            self.if_sram_cfg_list[0].wr_data = self.if_sram_cfg_wr_data
            self.if_sram_cfg_list[0].rd_en = self.if_sram_cfg_rd_en
            self.if_sram_cfg_list[0].rd_addr = self.if_sram_cfg_rd_addr
            self.if_sram_cfg_rd_data = self.if_sram_cfg_list[0].rd_data
            self.if_sram_cfg_rd_data_valid = self.if_sram_cfg_list[0].rd_data_valid

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def left_edge_cgra_cfg_ff(self):
        if self.reset:
            self.cgra_cfg_jtag_gc2glb_wr_en_d = 0
            self.cgra_cfg_jtag_gc2glb_rd_en_d = 0
            self.cgra_cfg_jtag_gc2glb_addr_d = 0
            self.cgra_cfg_jtag_gc2glb_data_d = 0
        else:
            self.cgra_cfg_jtag_gc2glb_wr_en_d = self.cgra_cfg_jtag_gc2glb_wr_en
            self.cgra_cfg_jtag_gc2glb_rd_en_d = self.cgra_cfg_jtag_gc2glb_rd_en
            self.cgra_cfg_jtag_gc2glb_addr_d = self.cgra_cfg_jtag_gc2glb_addr
            self.cgra_cfg_jtag_gc2glb_data_d = self.cgra_cfg_jtag_gc2glb_data

    def tile2tile_e2w_wiring(self):
        self.wire(self.proc_packet_e2w_esti[self._params.num_glb_tiles - 1],
                  self.proc_packet_w2e_esto[self._params.num_glb_tiles - 1]['rdrs'])
        self.wire(self.strm_packet_e2w_esti[self._params.num_glb_tiles - 1], 0)
        self.wire(self.pcfg_packet_e2w_esti[self._params.num_glb_tiles - 1], 0)
        for i in range(self._params.num_glb_tiles - 1):
            self.wire(self.proc_packet_e2w_esti[i], self.proc_packet_e2w_wsto[i + 1])
            self.wire(self.strm_packet_e2w_esti[i], self.strm_packet_e2w_wsto[i + 1])
            self.wire(self.pcfg_packet_e2w_esti[i], self.pcfg_packet_e2w_wsto[i + 1])

    def tile2tile_w2e_wiring(self):
        self.wire(self.proc_packet_w2e_wsti[0], self.proc_packet_d)
        self.wire(self.strm_packet_w2e_wsti[0], 0)
        self.wire(self.pcfg_packet_w2e_wsti[0], 0)
        for i in range(1, self._params.num_glb_tiles):
            self.wire(self.proc_packet_w2e_wsti[const(i, clog2(self._params.num_glb_tiles))],
                      self.proc_packet_w2e_esto[const((i - 1), clog2(self._params.num_glb_tiles))])
            self.wire(self.strm_packet_w2e_wsti[const(i, clog2(self._params.num_glb_tiles))],
                      self.strm_packet_w2e_esto[const((i - 1), clog2(self._params.num_glb_tiles))])
            self.wire(self.pcfg_packet_w2e_wsti[const(i, clog2(self._params.num_glb_tiles))],
                      self.pcfg_packet_w2e_esto[const((i - 1), clog2(self._params.num_glb_tiles))])

    @always_comb
    def tile2tile_w2e_cfg_wiring(self):
        for i in range(0, self._params.num_glb_tiles):
            if i == 0:
                self.cgra_cfg_jtag_wsti_rd_en[i] = 0
                self.cgra_cfg_jtag_wsti_wr_en[i] = self.cgra_cfg_jtag_gc2glb_wr_en_d
                self.cgra_cfg_jtag_wsti_addr[i] = self.cgra_cfg_jtag_gc2glb_addr_d
                self.cgra_cfg_jtag_wsti_data[i] = self.cgra_cfg_jtag_gc2glb_data_d

                self.cgra_cfg_jtag_wsti_rd_en_bypass[i] = self.cgra_cfg_jtag_gc2glb_rd_en_d
                self.cgra_cfg_jtag_wsti_addr_bypass[i] = self.cgra_cfg_jtag_gc2glb_addr_d

                self.cgra_cfg_pcfg_wsti_rd_en[i] = 0
                self.cgra_cfg_pcfg_wsti_wr_en[i] = 0
                self.cgra_cfg_pcfg_wsti_addr[i] = 0
                self.cgra_cfg_pcfg_wsti_data[i] = 0
            else:
                self.cgra_cfg_jtag_wsti_rd_en[i] = self.cgra_cfg_jtag_esto_rd_en[i - 1]
                self.cgra_cfg_jtag_wsti_wr_en[i] = self.cgra_cfg_jtag_esto_wr_en[i - 1]
                self.cgra_cfg_jtag_wsti_addr[i] = self.cgra_cfg_jtag_esto_addr[i - 1]
                self.cgra_cfg_jtag_wsti_data[i] = self.cgra_cfg_jtag_esto_data[i - 1]

                self.cgra_cfg_jtag_wsti_rd_en_bypass[i] = self.cgra_cfg_jtag_esto_rd_en_bypass[i - 1]
                self.cgra_cfg_jtag_wsti_addr_bypass[i] = self.cgra_cfg_jtag_esto_addr_bypass[i - 1]

                self.cgra_cfg_pcfg_wsti_rd_en[i] = self.cgra_cfg_pcfg_esto_rd_en[i - 1]
                self.cgra_cfg_pcfg_wsti_wr_en[i] = self.cgra_cfg_pcfg_esto_wr_en[i - 1]
                self.cgra_cfg_pcfg_wsti_addr[i] = self.cgra_cfg_pcfg_esto_addr[i - 1]
                self.cgra_cfg_pcfg_wsti_data[i] = self.cgra_cfg_pcfg_esto_data[i - 1]

    def add_glb_tile(self):
        for i in range(self._params.num_glb_tiles):
            self.add_child(f"glb_tile_gen_{i}",
                           self.glb_tile[i],
                           clk=self.clk,
                           clk_en_core=clock_en(~self.core_stall_d[i]),
                           clk_en_rtr=clock_en(~self.rtr_stall_d[i]),
                           clk_en_pcfg_rtr=clock_en(~self.pcfg_rtr_stall_d[i]),
                           reset=self.reset,
                           glb_tile_id=i,

                           # proc
                           proc_wr_en_w2e_wsti=self.proc_packet_w2e_wsti[i]["wr"]['wr_en'],
                           proc_wr_strb_w2e_wsti=self.proc_packet_w2e_wsti[i]["wr"]['wr_strb'],
                           proc_wr_addr_w2e_wsti=self.proc_packet_w2e_wsti[i]["wr"]['wr_addr'],
                           proc_wr_data_w2e_wsti=self.proc_packet_w2e_wsti[i]["wr"]['wr_data'],
                           proc_rd_en_w2e_wsti=self.proc_packet_w2e_wsti[i]["rdrq"]['rd_en'],
                           proc_rd_src_tile_w2e_wsti=self.proc_packet_w2e_wsti[i]["rdrq"]['rd_src_tile'],
                           proc_rd_addr_w2e_wsti=self.proc_packet_w2e_wsti[i]["rdrq"]['rd_addr'],
                           proc_rd_data_w2e_wsti=self.proc_packet_w2e_wsti[i]["rdrs"]['rd_data'],
                           proc_rd_dst_tile_w2e_wsti=self.proc_packet_w2e_wsti[i]["rdrs"]['rd_dst_tile'],
                           proc_rd_data_valid_w2e_wsti=self.proc_packet_w2e_wsti[i]["rdrs"]['rd_data_valid'],

                           proc_wr_en_w2e_esto=self.proc_packet_w2e_esto[i]["wr"]['wr_en'],
                           proc_wr_strb_w2e_esto=self.proc_packet_w2e_esto[i]["wr"]['wr_strb'],
                           proc_wr_addr_w2e_esto=self.proc_packet_w2e_esto[i]["wr"]['wr_addr'],
                           proc_wr_data_w2e_esto=self.proc_packet_w2e_esto[i]["wr"]['wr_data'],
                           proc_rd_en_w2e_esto=self.proc_packet_w2e_esto[i]["rdrq"]['rd_en'],
                           proc_rd_src_tile_w2e_esto=self.proc_packet_w2e_esto[i]["rdrq"]['rd_src_tile'],
                           proc_rd_addr_w2e_esto=self.proc_packet_w2e_esto[i]["rdrq"]['rd_addr'],
                           proc_rd_data_w2e_esto=self.proc_packet_w2e_esto[i]["rdrs"]['rd_data'],
                           proc_rd_dst_tile_w2e_esto=self.proc_packet_w2e_esto[i]["rdrs"]['rd_dst_tile'],
                           proc_rd_data_valid_w2e_esto=self.proc_packet_w2e_esto[i]["rdrs"]['rd_data_valid'],

                           proc_rd_data_e2w_esti=self.proc_packet_e2w_esti[i]['rd_data'],
                           proc_rd_dst_tile_e2w_esti=self.proc_packet_e2w_esti[i]['rd_dst_tile'],
                           proc_rd_data_valid_e2w_esti=self.proc_packet_e2w_esti[i]['rd_data_valid'],

                           proc_rd_data_e2w_wsto=self.proc_packet_e2w_wsto[i]['rd_data'],
                           proc_rd_dst_tile_e2w_wsto=self.proc_packet_e2w_wsto[i]['rd_dst_tile'],
                           proc_rd_data_valid_e2w_wsto=self.proc_packet_e2w_wsto[i]['rd_data_valid'],

                           strm_wr_en_e2w_esti=self.strm_packet_e2w_esti[i]["wr"]['wr_en'],
                           strm_wr_strb_e2w_esti=self.strm_packet_e2w_esti[i]["wr"]['wr_strb'],
                           strm_wr_addr_e2w_esti=self.strm_packet_e2w_esti[i]["wr"]['wr_addr'],
                           strm_wr_data_e2w_esti=self.strm_packet_e2w_esti[i]["wr"]['wr_data'],
                           strm_rd_en_e2w_esti=self.strm_packet_e2w_esti[i]["rdrq"]['rd_en'],
                           strm_rd_src_tile_e2w_esti=self.strm_packet_e2w_esti[i]["rdrq"]['rd_src_tile'],
                           strm_rd_addr_e2w_esti=self.strm_packet_e2w_esti[i]["rdrq"]['rd_addr'],
                           strm_rd_data_e2w_esti=self.strm_packet_e2w_esti[i]["rdrs"]['rd_data'],
                           strm_rd_dst_tile_e2w_esti=self.strm_packet_e2w_esti[i]["rdrs"]['rd_dst_tile'],
                           strm_rd_data_valid_e2w_esti=self.strm_packet_e2w_esti[i]["rdrs"]['rd_data_valid'],

                           strm_wr_en_w2e_esto=self.strm_packet_w2e_esto[i]["wr"]['wr_en'],
                           strm_wr_strb_w2e_esto=self.strm_packet_w2e_esto[i]["wr"]['wr_strb'],
                           strm_wr_addr_w2e_esto=self.strm_packet_w2e_esto[i]["wr"]['wr_addr'],
                           strm_wr_data_w2e_esto=self.strm_packet_w2e_esto[i]["wr"]['wr_data'],
                           strm_rd_en_w2e_esto=self.strm_packet_w2e_esto[i]["rdrq"]['rd_en'],
                           strm_rd_src_tile_w2e_esto=self.strm_packet_w2e_esto[i]["rdrq"]['rd_src_tile'],
                           strm_rd_addr_w2e_esto=self.strm_packet_w2e_esto[i]["rdrq"]['rd_addr'],
                           strm_rd_data_w2e_esto=self.strm_packet_w2e_esto[i]["rdrs"]['rd_data'],
                           strm_rd_dst_tile_w2e_esto=self.strm_packet_w2e_esto[i]["rdrs"]['rd_dst_tile'],
                           strm_rd_data_valid_w2e_esto=self.strm_packet_w2e_esto[i]["rdrs"]['rd_data_valid'],

                           strm_wr_en_w2e_wsti=self.strm_packet_w2e_wsti[i]["wr"]['wr_en'],
                           strm_wr_strb_w2e_wsti=self.strm_packet_w2e_wsti[i]["wr"]['wr_strb'],
                           strm_wr_addr_w2e_wsti=self.strm_packet_w2e_wsti[i]["wr"]['wr_addr'],
                           strm_wr_data_w2e_wsti=self.strm_packet_w2e_wsti[i]["wr"]['wr_data'],
                           strm_rd_en_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrq"]['rd_en'],
                           strm_rd_src_tile_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrq"]['rd_src_tile'],
                           strm_rd_addr_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrq"]['rd_addr'],
                           strm_rd_data_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrs"]['rd_data'],
                           strm_rd_dst_tile_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrs"]['rd_dst_tile'],
                           strm_rd_data_valid_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrs"]['rd_data_valid'],

                           strm_wr_en_e2w_wsto=self.strm_packet_e2w_wsto[i]["wr"]['wr_en'],
                           strm_wr_strb_e2w_wsto=self.strm_packet_e2w_wsto[i]["wr"]['wr_strb'],
                           strm_wr_addr_e2w_wsto=self.strm_packet_e2w_wsto[i]["wr"]['wr_addr'],
                           strm_wr_data_e2w_wsto=self.strm_packet_e2w_wsto[i]["wr"]['wr_data'],
                           strm_rd_en_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrq"]['rd_en'],
                           strm_rd_src_tile_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrq"]['rd_src_tile'],
                           strm_rd_addr_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrq"]['rd_addr'],
                           strm_rd_data_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrs"]['rd_data'],
                           strm_rd_dst_tile_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrs"]['rd_dst_tile'],
                           strm_rd_data_valid_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrs"]['rd_data_valid'],

                           pcfg_rd_en_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrq"]['rd_en'],
                           pcfg_rd_src_tile_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrq"]['rd_src_tile'],
                           pcfg_rd_addr_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrq"]['rd_addr'],
                           pcfg_rd_data_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrs"]['rd_data'],
                           pcfg_rd_dst_tile_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrs"]['rd_dst_tile'],
                           pcfg_rd_data_valid_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrs"]['rd_data_valid'],

                           pcfg_rd_en_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrq"]['rd_en'],
                           pcfg_rd_src_tile_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrq"]['rd_src_tile'],
                           pcfg_rd_addr_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrq"]['rd_addr'],
                           pcfg_rd_data_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrs"]['rd_data'],
                           pcfg_rd_dst_tile_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrs"]['rd_dst_tile'],
                           pcfg_rd_data_valid_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrs"]['rd_data_valid'],

                           pcfg_rd_en_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrq"]['rd_en'],
                           pcfg_rd_src_tile_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrq"]['rd_src_tile'],
                           pcfg_rd_addr_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrq"]['rd_addr'],
                           pcfg_rd_data_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrs"]['rd_data'],
                           pcfg_rd_dst_tile_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrs"]['rd_dst_tile'],
                           pcfg_rd_data_valid_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrs"]['rd_data_valid'],

                           pcfg_rd_en_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrq"]['rd_en'],
                           pcfg_rd_src_tile_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrq"]['rd_src_tile'],
                           pcfg_rd_addr_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrq"]['rd_addr'],
                           pcfg_rd_data_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrs"]['rd_data'],
                           pcfg_rd_dst_tile_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrs"]['rd_dst_tile'],
                           pcfg_rd_data_valid_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrs"]['rd_data_valid'],

                           if_cfg_est_m_wr_en=self.if_cfg_list[i + 1].wr_en,
                           if_cfg_est_m_wr_addr=self.if_cfg_list[i + 1].wr_addr,
                           if_cfg_est_m_wr_data=self.if_cfg_list[i + 1].wr_data,
                           if_cfg_est_m_rd_en=self.if_cfg_list[i + 1].rd_en,
                           if_cfg_est_m_rd_addr=self.if_cfg_list[i + 1].rd_addr,
                           if_cfg_est_m_rd_data=self.if_cfg_list[i + 1].rd_data,
                           if_cfg_est_m_rd_data_valid=self.if_cfg_list[i + 1].rd_data_valid,

                           if_cfg_wst_s_wr_en=self.if_cfg_list[i].wr_en,
                           if_cfg_wst_s_wr_addr=self.if_cfg_list[i].wr_addr,
                           if_cfg_wst_s_wr_data=self.if_cfg_list[i].wr_data,
                           if_cfg_wst_s_rd_en=self.if_cfg_list[i].rd_en,
                           if_cfg_wst_s_rd_addr=self.if_cfg_list[i].rd_addr,
                           if_cfg_wst_s_rd_data=self.if_cfg_list[i].rd_data,
                           if_cfg_wst_s_rd_data_valid=self.if_cfg_list[i].rd_data_valid,

                           if_sram_cfg_est_m_wr_en=self.if_sram_cfg_list[i + 1].wr_en,
                           if_sram_cfg_est_m_wr_addr=self.if_sram_cfg_list[i + 1].wr_addr,
                           if_sram_cfg_est_m_wr_data=self.if_sram_cfg_list[i + 1].wr_data,
                           if_sram_cfg_est_m_rd_en=self.if_sram_cfg_list[i + 1].rd_en,
                           if_sram_cfg_est_m_rd_addr=self.if_sram_cfg_list[i + 1].rd_addr,
                           if_sram_cfg_est_m_rd_data=self.if_sram_cfg_list[i + 1].rd_data,
                           if_sram_cfg_est_m_rd_data_valid=self.if_sram_cfg_list[i + 1].rd_data_valid,

                           if_sram_cfg_wst_s_wr_en=self.if_sram_cfg_list[i].wr_en,
                           if_sram_cfg_wst_s_wr_addr=self.if_sram_cfg_list[i].wr_addr,
                           if_sram_cfg_wst_s_wr_data=self.if_sram_cfg_list[i].wr_data,
                           if_sram_cfg_wst_s_rd_en=self.if_sram_cfg_list[i].rd_en,
                           if_sram_cfg_wst_s_rd_addr=self.if_sram_cfg_list[i].rd_addr,
                           if_sram_cfg_wst_s_rd_data=self.if_sram_cfg_list[i].rd_data,
                           if_sram_cfg_wst_s_rd_data_valid=self.if_sram_cfg_list[i].rd_data_valid,

                           cfg_tile_connected_wsti=self.cfg_tile_connected[i],
                           cfg_tile_connected_esto=self.cfg_tile_connected[i + 1],
                           cfg_pcfg_tile_connected_wsti=self.cfg_pcfg_tile_connected[i],
                           cfg_pcfg_tile_connected_esto=self.cfg_pcfg_tile_connected[i + 1],

                           strm_data_f2g=self.strm_data_f2g_d[i],
                           strm_data_valid_f2g=self.strm_data_valid_f2g_d[i],
                           strm_data_g2f=self.strm_data_g2f_w[i],
                           strm_data_valid_g2f=self.strm_data_valid_g2f_w[i],

                           cgra_cfg_g2f_cfg_wr_en=self.cgra_cfg_g2f_cfg_wr_en_w[i],
                           cgra_cfg_g2f_cfg_rd_en=self.cgra_cfg_g2f_cfg_rd_en_w[i],
                           cgra_cfg_g2f_cfg_addr=self.cgra_cfg_g2f_cfg_addr_w[i],
                           cgra_cfg_g2f_cfg_data=self.cgra_cfg_g2f_cfg_data_w[i],

                           cgra_cfg_pcfg_wsti_wr_en=self.cgra_cfg_pcfg_wsti_wr_en[i],
                           cgra_cfg_pcfg_wsti_rd_en=self.cgra_cfg_pcfg_wsti_rd_en[i],
                           cgra_cfg_pcfg_wsti_addr=self.cgra_cfg_pcfg_wsti_addr[i],
                           cgra_cfg_pcfg_wsti_data=self.cgra_cfg_pcfg_wsti_data[i],

                           cgra_cfg_pcfg_esto_wr_en=self.cgra_cfg_pcfg_esto_wr_en[i],
                           cgra_cfg_pcfg_esto_rd_en=self.cgra_cfg_pcfg_esto_rd_en[i],
                           cgra_cfg_pcfg_esto_addr=self.cgra_cfg_pcfg_esto_addr[i],
                           cgra_cfg_pcfg_esto_data=self.cgra_cfg_pcfg_esto_data[i],

                           cgra_cfg_jtag_wsti_wr_en=self.cgra_cfg_jtag_wsti_wr_en[i],
                           cgra_cfg_jtag_wsti_rd_en=self.cgra_cfg_jtag_wsti_rd_en[i],
                           cgra_cfg_jtag_wsti_addr=self.cgra_cfg_jtag_wsti_addr[i],
                           cgra_cfg_jtag_wsti_data=self.cgra_cfg_jtag_wsti_data[i],

                           cgra_cfg_jtag_esto_wr_en=self.cgra_cfg_jtag_esto_wr_en[i],
                           cgra_cfg_jtag_esto_rd_en=self.cgra_cfg_jtag_esto_rd_en[i],
                           cgra_cfg_jtag_esto_addr=self.cgra_cfg_jtag_esto_addr[i],
                           cgra_cfg_jtag_esto_data=self.cgra_cfg_jtag_esto_data[i],

                           cgra_cfg_jtag_wsti_rd_en_bypass=self.cgra_cfg_jtag_wsti_rd_en_bypass[i],
                           cgra_cfg_jtag_wsti_addr_bypass=self.cgra_cfg_jtag_wsti_addr_bypass[i],
                           cgra_cfg_jtag_esto_rd_en_bypass=self.cgra_cfg_jtag_esto_rd_en_bypass[i],
                           cgra_cfg_jtag_esto_addr_bypass=self.cgra_cfg_jtag_esto_addr_bypass[i],

                           strm_g2f_start_pulse=self.strm_g2f_start_pulse_d[i],
                           strm_f2g_start_pulse=self.strm_f2g_start_pulse_d[i],
                           pcfg_start_pulse=self.pcfg_start_pulse_d[i],
                           strm_f2g_interrupt_pulse=self.strm_f2g_interrupt_pulse_w[i],
                           strm_g2f_interrupt_pulse=self.strm_g2f_interrupt_pulse_w[i],
                           pcfg_g2f_interrupt_pulse=self.pcfg_g2f_interrupt_pulse_w[i])

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def interrupt_pipeline(self):
        if self.reset:
            for i in range(self._params.num_glb_tiles):
                self.strm_f2g_interrupt_pulse_d[i] = 0
                self.strm_g2f_interrupt_pulse_d[i] = 0
                self.pcfg_g2f_interrupt_pulse_d[i] = 0
        else:
            for i in range(self._params.num_glb_tiles):
                self.strm_f2g_interrupt_pulse_d[i] = self.strm_f2g_interrupt_pulse_w[i]
                self.strm_g2f_interrupt_pulse_d[i] = self.strm_g2f_interrupt_pulse_w[i]
                self.pcfg_g2f_interrupt_pulse_d[i] = self.pcfg_g2f_interrupt_pulse_w[i]

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def strm_data_pipeline(self):
        if self.reset:
            for i in range(self._params.num_glb_tiles):
                self.strm_data_g2f_d[i] = 0
                self.strm_data_valid_g2f_d[i] = 0
                self.strm_data_f2g_d[i] = 0
                self.strm_data_valid_f2g_d[i] = 0
        else:
            for i in range(self._params.num_glb_tiles):
                self.strm_data_g2f_d[i] = self.strm_data_g2f_w[i]
                self.strm_data_valid_g2f_d[i] = self.strm_data_valid_g2f_w[i]
                self.strm_data_f2g_d[i] = self.strm_data_f2g_w[i]
                self.strm_data_valid_f2g_d[i] = self.strm_data_valid_f2g_w[i]

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def cgra_cfg_pcfg_pipeline(self):
        if self.reset:
            for i in range(self._params.num_glb_tiles):
                self.cgra_cfg_g2f_cfg_wr_en_d[i] = 0
                self.cgra_cfg_g2f_cfg_rd_en_d[i] = 0
                self.cgra_cfg_g2f_cfg_addr_d[i] = 0
                self.cgra_cfg_g2f_cfg_data_d[i] = 0
        else:
            for i in range(self._params.num_glb_tiles):
                self.cgra_cfg_g2f_cfg_wr_en_d[i] = self.cgra_cfg_g2f_cfg_wr_en_w[i]
                self.cgra_cfg_g2f_cfg_rd_en_d[i] = self.cgra_cfg_g2f_cfg_rd_en_w[i]
                self.cgra_cfg_g2f_cfg_addr_d[i] = self.cgra_cfg_g2f_cfg_addr_w[i]
                self.cgra_cfg_g2f_cfg_data_d[i] = self.cgra_cfg_g2f_cfg_data_w[i]


def GlobalBufferMagma(params: GlobalBufferParams):
    dut = GlobalBuffer(params)
    circ = to_magma(dut, flatten_array=True)

    return FromMagma(circ)
