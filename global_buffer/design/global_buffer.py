from kratos import Generator, always_ff, posedge, always_comb, clock_en, clog2, const, concat
from kratos.util import to_magma
from global_buffer.design.glb_tile import GlbTile
from global_buffer.design.glb_tile_ifc import GlbTileInterface
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen
from global_buffer.design.glb_crossbar import GlbCrossbar
from gemstone.generator.from_magma import FromMagma


class GlobalBuffer(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("global_buffer")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.glb_clk_en_master = self.input("glb_clk_en_master", self._params.num_glb_tiles)
        self.glb_clk_en_bank_master = self.input("glb_clk_en_bank_master", self._params.num_glb_tiles)
        self.pcfg_broadcast_stall = self.input("pcfg_broadcast_stall", self._params.num_glb_tiles)
        self.flush_crossbar_sel = self.input("flush_crossbar_sel", clog2(
            self._params.num_glb_tiles) * self._params.num_groups)
        self.reset = self.reset("reset")

        self.proc_wr_en = self.input("proc_wr_en", 1)
        self.proc_wr_strb = self.input("proc_wr_strb", self._params.bank_strb_width)
        self.proc_wr_addr = self.input("proc_wr_addr", self._params.glb_addr_width)
        self.proc_wr_data = self.input("proc_wr_data", self._params.bank_data_width)
        self.proc_rd_en = self.input("proc_rd_en", 1)
        self.proc_rd_addr = self.input("proc_rd_addr", self._params.glb_addr_width)
        self.proc_rd_data = self.output("proc_rd_data", self._params.bank_data_width)
        self.proc_rd_data_valid = self.output("proc_rd_data_valid", 1)

        self.if_cfg_wr_en = self.input("if_cfg_wr_en", 1)
        self.if_cfg_wr_clk_en = self.input("if_cfg_wr_clk_en", 1)
        self.if_cfg_wr_addr = self.input("if_cfg_wr_addr", self._params.axi_addr_width)
        self.if_cfg_wr_data = self.input("if_cfg_wr_data", self._params.axi_data_width)
        self.if_cfg_rd_en = self.input("if_cfg_rd_en", 1)
        self.if_cfg_rd_clk_en = self.input("if_cfg_rd_clk_en", 1)
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
        self.strm_data_flush_g2f = self.output("strm_data_flush_g2f", 1, size=self._params.num_groups, packed=True)

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

        # local parameters
        self.bank_lsb_data_width = self._params.axi_data_width
        self.bank_msb_data_width = self._params.bank_data_width - self._params.axi_data_width

        # local variables
        self.data_flush = self.var("data_flush", 1, size=self._params.num_glb_tiles, packed=True)
        self.proc_rd_type_e = self.enum("proc_rd_type_e", {"axi": 0, "jtag": 1})
        self.proc_rd_type = self.var("proc_rd_type", self.proc_rd_type_e)
        self.proc_rd_addr_sel = self.var("proc_rd_addr_sel", 1)
        self.proc_wr_en_d = self.var("proc_wr_en_d", 1)
        self.proc_wr_strb_d = self.var("proc_wr_strb_d", self._params.bank_strb_width)
        self.proc_wr_addr_d = self.var("proc_wr_addr_d", self._params.glb_addr_width)
        self.proc_wr_data_d = self.var("proc_wr_data_d", self._params.bank_data_width)
        self.proc_rd_en_d = self.var("proc_rd_en_d", 1)
        self.proc_rd_addr_d = self.var("proc_rd_addr_d", self._params.glb_addr_width)

        self.sram_cfg_wr_en_d = self.var("sram_cfg_wr_en_d", 1)
        self.sram_cfg_wr_strb_d = self.var("sram_cfg_wr_strb_d", self._params.bank_strb_width)
        self.sram_cfg_wr_addr_d = self.var("sram_cfg_wr_addr_d", self._params.glb_addr_width)
        self.sram_cfg_wr_data_d = self.var("sram_cfg_wr_data_d", self._params.bank_data_width)
        self.sram_cfg_rd_en_d = self.var("sram_cfg_rd_en_d", 1)
        self.sram_cfg_rd_addr_d = self.var("sram_cfg_rd_addr_d", self._params.glb_addr_width)

        self.cgra_cfg_jtag_gc2glb_wr_en_d = self.var("cgra_cfg_jtag_gc2glb_wr_en_d", 1)
        self.cgra_cfg_jtag_gc2glb_rd_en_d = self.var("cgra_cfg_jtag_gc2glb_rd_en_d", 1)
        self.cgra_cfg_jtag_gc2glb_addr_d = self.var("cgra_cfg_jtag_gc2glb_addr_d", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_gc2glb_data_d = self.var("cgra_cfg_jtag_gc2glb_data_d", self._params.cgra_cfg_data_width)

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

        self.cgra_cfg_jtag_wr_en_wsti = self.var(
            "cgra_cfg_jtag_wr_en_wsti", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_rd_en_wsti = self.var(
            "cgra_cfg_jtag_rd_en_wsti", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_addr_wsti = self.var(
            "cgra_cfg_jtag_addr_wsti", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_data_wsti = self.var(
            "cgra_cfg_jtag_data_wsti", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_jtag_wr_en_esto = self.var(
            "cgra_cfg_jtag_wr_en_esto", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_rd_en_esto = self.var(
            "cgra_cfg_jtag_rd_en_esto", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_addr_esto = self.var(
            "cgra_cfg_jtag_addr_esto", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_data_esto = self.var(
            "cgra_cfg_jtag_data_esto", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_jtag_rd_en_bypass_wsti = self.var("cgra_cfg_jtag_rd_en_bypass_wsti", 1,
                                                        size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_addr_bypass_wsti = self.var("cgra_cfg_jtag_addr_bypass_wsti",
                                                       self._params.cgra_cfg_addr_width,
                                                       size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_rd_en_bypass_esto = self.var("cgra_cfg_jtag_rd_en_bypass_esto", 1,
                                                        size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_addr_bypass_esto = self.var("cgra_cfg_jtag_addr_bypass_esto",
                                                       self._params.cgra_cfg_addr_width,
                                                       size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_pcfg_wr_en_w2e_wsti = self.var(
            "cgra_cfg_pcfg_wr_en_wsti", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_rd_en_w2e_wsti = self.var(
            "cgra_cfg_pcfg_rd_en_wsti", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_addr_w2e_wsti = self.var(
            "cgra_cfg_pcfg_addr_wsti", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_data_w2e_wsti = self.var(
            "cgra_cfg_pcfg_data_wsti", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_pcfg_wr_en_w2e_esto = self.var(
            "cgra_cfg_pcfg_wr_en_esto", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_rd_en_w2e_esto = self.var(
            "cgra_cfg_pcfg_rd_en_esto", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_addr_w2e_esto = self.var(
            "cgra_cfg_pcfg_addr_esto", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_data_w2e_esto = self.var(
            "cgra_cfg_pcfg_data_esto", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_pcfg_wr_en_e2w_esti = self.var(
            "cgra_cfg_pcfg_wr_en_esti", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_rd_en_e2w_esti = self.var(
            "cgra_cfg_pcfg_rd_en_esti", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_addr_e2w_esti = self.var(
            "cgra_cfg_pcfg_addr_esti", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_data_e2w_esti = self.var(
            "cgra_cfg_pcfg_data_esti", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_pcfg_wr_en_e2w_wsto = self.var(
            "cgra_cfg_pcfg_wr_en_wsto", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_rd_en_e2w_wsto = self.var(
            "cgra_cfg_pcfg_rd_en_wsto", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_addr_e2w_wsto = self.var(
            "cgra_cfg_pcfg_addr_wsto", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_pcfg_data_e2w_wsto = self.var(
            "cgra_cfg_pcfg_data_wsto", self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.strm_f2g_interrupt_pulse_w = self.var("strm_f2g_interrupt_pulse_w", self._params.num_glb_tiles)
        self.strm_f2g_interrupt_pulse_d = self.var("strm_f2g_interrupt_pulse_d", self._params.num_glb_tiles)
        self.wire(self.strm_f2g_interrupt_pulse_d, self.strm_f2g_interrupt_pulse)

        self.strm_g2f_interrupt_pulse_w = self.var("strm_g2f_interrupt_pulse_w", self._params.num_glb_tiles)
        self.strm_g2f_interrupt_pulse_d = self.var("strm_g2f_interrupt_pulse_d", self._params.num_glb_tiles)
        self.wire(self.strm_g2f_interrupt_pulse_d, self.strm_g2f_interrupt_pulse)

        self.pcfg_g2f_interrupt_pulse_w = self.var("pcfg_g2f_interrupt_pulse_w", self._params.num_glb_tiles)
        self.pcfg_g2f_interrupt_pulse_d = self.var("pcfg_g2f_interrupt_pulse_d", self._params.num_glb_tiles)
        self.wire(self.pcfg_g2f_interrupt_pulse_d, self.pcfg_g2f_interrupt_pulse)

        # interface
        if_proc_tile2tile = GlbTileInterface(addr_width=self._params.glb_addr_width,
                                             data_width=self._params.bank_data_width, is_clk_en=True, is_strb=True)
        if_cfg_tile2tile = GlbTileInterface(addr_width=self._params.axi_addr_width,
                                            data_width=self._params.axi_data_width, is_clk_en=True, is_strb=False)
        if_sram_cfg_tile2tile = GlbTileInterface(addr_width=self._params.glb_addr_width,
                                                 data_width=self._params.axi_data_width, is_clk_en=True, is_strb=False)

        self.if_proc_list = []
        self.if_cfg_list = []
        self.if_sram_cfg_list = []
        for i in range(self._params.num_glb_tiles + 1):
            self.if_proc_list.append(self.interface(
                if_proc_tile2tile, f"if_proc_tile2tile_{i}"))
            self.if_cfg_list.append(self.interface(
                if_cfg_tile2tile, f"if_cfg_tile2tile_{i}"))
            self.if_sram_cfg_list.append(self.interface(
                if_sram_cfg_tile2tile, f"if_sram_cfg_tile2tile_{i}"))

        # GLS pipeline
        self.strm_g2f_start_pulse_d = self.var("strm_g2f_start_pulse_d", self._params.num_glb_tiles)
        self.strm_f2g_start_pulse_d = self.var("strm_f2g_start_pulse_d", self._params.num_glb_tiles)
        self.pcfg_start_pulse_d = self.var("pcfg_start_pulse_d", self._params.num_glb_tiles)
        self.gls_in = concat(self.strm_g2f_start_pulse, self.strm_f2g_start_pulse, self.pcfg_start_pulse)
        self.gls_out = concat(self.strm_g2f_start_pulse_d, self.strm_f2g_start_pulse_d, self.pcfg_start_pulse_d)

        self.gls_pipeline = Pipeline(width=self.gls_in.width, depth=self._params.gls_pipeline_depth)
        self.add_child("gls_pipeline",
                       self.gls_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.gls_in,
                       out_=self.gls_out)

        # GLB Tiles
        self.glb_tile = []
        for i in range(self._params.num_glb_tiles):
            self.glb_tile.append(GlbTile(_params=self._params))

        self.wire(self.if_proc_list[-1].rd_data, 0)
        self.wire(self.if_proc_list[-1].rd_data_valid, 0)
        self.wire(self.if_cfg_list[-1].rd_data, 0)
        self.wire(self.if_cfg_list[-1].rd_data_valid, 0)
        self.wire(self.if_sram_cfg_list[-1].rd_data, 0)
        self.wire(self.if_sram_cfg_list[-1].rd_data_valid, 0)

        self.add_glb_tile()
        self.add_always(self.proc_pipeline)
        self.add_always(self.sram_cfg_pipeline)
        self.add_always(self.left_edge_proc_wr_ff)
        self.add_always(self.left_edge_proc_rd_ff)
        self.add_always(self.left_edge_proc_rd_out)
        self.add_proc_clk_en()
        self.add_always(self.left_edge_cfg_ff)
        self.add_always(self.left_edge_cgra_cfg_ff)
        self.tile2tile_e2w_struct_wiring()
        self.tile2tile_w2e_struct_wiring()
        self.add_always(self.tile2tile_w2e_cfg_wiring)
        self.add_always(self.tile2tile_e2w_cfg_wiring)
        self.add_always(self.interrupt_pipeline)

        # Directly assign rd_data output ports at the left side
        self.wire(self.if_cfg_rd_data, self.if_cfg_list[0].rd_data)
        self.wire(self.if_cfg_rd_data_valid, self.if_cfg_list[0].rd_data_valid)

        # Add flush signal crossbar
        self.flush_crossbar = GlbCrossbar(width=1, num_input=self._params.num_glb_tiles,
                                          num_output=self._params.num_groups)
        self.flush_crossbar_sel_w = self.var("flush_crossbar_sel_w", clog2(self._params.num_glb_tiles),
                                             size=self._params.num_groups, packed=True)
        for i in range(self._params.num_groups):
            self.wire(self.flush_crossbar_sel_w[i],
                      self.flush_crossbar_sel[(i + 1) * clog2(self._params.num_glb_tiles) - 1,
                                              i * clog2(self._params.num_glb_tiles)])
        self.add_child("flush_crossbar",
                       self.flush_crossbar,
                       in_=self.data_flush,
                       sel_=self.flush_crossbar_sel_w,
                       out_=self.strm_data_flush_g2f)

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def proc_pipeline(self):
        if self.reset:
            self.proc_wr_en_d = 0
            self.proc_wr_strb_d = 0
            self.proc_wr_addr_d = 0
            self.proc_wr_data_d = 0
            self.proc_rd_en_d = 0
            self.proc_rd_addr_d = 0
        else:
            self.proc_wr_en_d = self.proc_wr_en
            self.proc_wr_strb_d = self.proc_wr_strb
            self.proc_wr_addr_d = self.proc_wr_addr
            self.proc_wr_data_d = self.proc_wr_data
            self.proc_rd_en_d = self.proc_rd_en
            self.proc_rd_addr_d = self.proc_rd_addr

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def sram_cfg_pipeline(self):
        if self.reset:
            self.sram_cfg_wr_en_d = 0
            self.sram_cfg_wr_strb_d = 0
            self.sram_cfg_wr_addr_d = 0
            self.sram_cfg_wr_data_d = 0
            self.sram_cfg_rd_en_d = 0
            self.sram_cfg_rd_addr_d = 0
        else:
            self.sram_cfg_wr_en_d = self.if_sram_cfg_wr_en
            self.sram_cfg_wr_addr_d = self.if_sram_cfg_wr_addr
            if self.if_sram_cfg_wr_addr[self._params.bank_byte_offset - 1] == 0:
                self.sram_cfg_wr_data_d = concat(const(0, self.bank_msb_data_width), self.if_sram_cfg_wr_data)
                self.sram_cfg_wr_strb_d = concat(const(0, self.bank_msb_data_width // 8),
                                                 const(2**(self.bank_lsb_data_width // 8) - 1,
                                                       self.bank_lsb_data_width // 8))
            else:
                self.sram_cfg_wr_data_d = concat(
                    self.if_sram_cfg_wr_data[self.bank_msb_data_width - 1, 0], const(0, self.bank_lsb_data_width))
                self.sram_cfg_wr_strb_d = concat(const(2**(self.bank_msb_data_width // 8) - 1,
                                                       self.bank_msb_data_width // 8),
                                                 const(0, self.bank_lsb_data_width // 8))
            self.sram_cfg_rd_en_d = self.if_sram_cfg_rd_en
            self.sram_cfg_rd_addr_d = self.if_sram_cfg_rd_addr

    def add_proc_clk_en(self):
        self.wr_clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_wr_delay + self._params.proc_clk_en_margin)
        self.proc_wr_clk_en = self.var("proc_wr_clk_en", 1)
        self.add_child("proc_wr_clk_en_gen",
                       self.wr_clk_en_gen,
                       clk=self.clk,
                       reset=self.reset,
                       enable=self.proc_wr_en_d | self.sram_cfg_wr_en_d,
                       clk_en=self.proc_wr_clk_en
                       )
        self.wire(self.if_proc_list[0].wr_clk_en, self.proc_wr_clk_en)
        self.rd_clk_en_gen = GlbClkEnGen(cnt=2 * self._params.num_glb_tiles
                                         + self._params.tile2sram_rd_delay + self._params.proc_clk_en_margin)
        self.proc_rd_clk_en = self.var("proc_rd_clk_en", 1)
        self.add_child("proc_rd_clk_en_gen",
                       self.rd_clk_en_gen,
                       clk=self.clk,
                       reset=self.reset,
                       enable=self.proc_rd_en_d | self.sram_cfg_rd_en_d,
                       clk_en=self.proc_rd_clk_en
                       )
        self.wire(self.if_proc_list[0].rd_clk_en, self.proc_rd_clk_en)

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def left_edge_proc_wr_ff(self):
        if self.reset:
            self.if_proc_list[0].wr_en = 0
            self.if_proc_list[0].wr_strb = 0
            self.if_proc_list[0].wr_addr = 0
            self.if_proc_list[0].wr_data = 0
        else:
            if self.proc_wr_en_d:
                self.if_proc_list[0].wr_en = self.proc_wr_en_d
                self.if_proc_list[0].wr_strb = self.proc_wr_strb_d
                self.if_proc_list[0].wr_addr = self.proc_wr_addr_d
                self.if_proc_list[0].wr_data = self.proc_wr_data_d
            elif self.sram_cfg_wr_en_d:
                self.if_proc_list[0].wr_en = self.sram_cfg_wr_en_d
                self.if_proc_list[0].wr_strb = self.sram_cfg_wr_strb_d
                self.if_proc_list[0].wr_addr = self.sram_cfg_wr_addr_d
                self.if_proc_list[0].wr_data = self.sram_cfg_wr_data_d
            else:
                self.if_proc_list[0].wr_en = self.proc_wr_en_d
                self.if_proc_list[0].wr_strb = self.proc_wr_strb_d
                self.if_proc_list[0].wr_addr = self.proc_wr_addr_d
                self.if_proc_list[0].wr_data = self.proc_wr_data_d

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def left_edge_proc_rd_ff(self):
        if self.reset:
            self.if_proc_list[0].rd_en = 0
            self.if_proc_list[0].rd_addr = 0
            self.proc_rd_type = self.proc_rd_type_e.axi
            self.proc_rd_addr_sel = 0
        else:
            if self.proc_rd_en_d:
                self.if_proc_list[0].rd_en = self.proc_rd_en_d
                self.if_proc_list[0].rd_addr = self.proc_rd_addr_d
                self.proc_rd_type = self.proc_rd_type_e.axi
                self.proc_rd_addr_sel = 0
            elif self.sram_cfg_rd_en_d:
                self.if_proc_list[0].rd_en = self.sram_cfg_rd_en_d
                self.if_proc_list[0].rd_addr = self.sram_cfg_rd_addr_d
                self.proc_rd_addr_sel = self.sram_cfg_rd_addr_d[self._params.bank_byte_offset - 1]
                self.proc_rd_type = self.proc_rd_type_e.jtag
            else:
                self.if_proc_list[0].rd_en = self.proc_rd_en_d
                self.if_proc_list[0].rd_addr = self.proc_rd_addr_d
                self.proc_rd_type = self.proc_rd_type
                self.proc_rd_addr_sel = self.proc_rd_addr_sel

    @ always_comb
    def left_edge_proc_rd_out(self):
        if self.proc_rd_type == self.proc_rd_type_e.axi:
            self.proc_rd_data = self.if_proc_list[0].rd_data
            self.proc_rd_data_valid = self.if_proc_list[0].rd_data_valid
            self.if_sram_cfg_rd_data = 0
            self.if_sram_cfg_rd_data_valid = 0
        elif self.proc_rd_type == self.proc_rd_type_e.jtag:
            self.proc_rd_data = 0
            self.proc_rd_data_valid = 0
            if self.proc_rd_addr_sel == 0:
                self.if_sram_cfg_rd_data = self.if_proc_list[0].rd_data[self._params.axi_data_width - 1, 0]
            else:
                self.if_sram_cfg_rd_data = self.if_proc_list[0].rd_data[self._params.axi_data_width
                                                                        * 2 - 1, self._params.axi_data_width]
            self.if_sram_cfg_rd_data_valid = self.if_proc_list[0].rd_data_valid
        else:
            self.proc_rd_data = self.if_proc_list[0].rd_data
            self.proc_rd_data_valid = self.if_proc_list[0].rd_data_valid
            self.if_sram_cfg_rd_data = 0
            self.if_sram_cfg_rd_data_valid = 0

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def left_edge_cfg_ff(self):
        if self.reset:
            self.if_cfg_list[0].wr_en = 0
            self.if_cfg_list[0].wr_clk_en = 0
            self.if_cfg_list[0].wr_addr = 0
            self.if_cfg_list[0].wr_data = 0
            self.if_cfg_list[0].rd_en = 0
            self.if_cfg_list[0].rd_clk_en = 0
            self.if_cfg_list[0].rd_addr = 0
        else:
            self.if_cfg_list[0].wr_en = self.if_cfg_wr_en
            self.if_cfg_list[0].wr_clk_en = self.if_cfg_wr_clk_en
            self.if_cfg_list[0].wr_addr = self.if_cfg_wr_addr
            self.if_cfg_list[0].wr_data = self.if_cfg_wr_data
            self.if_cfg_list[0].rd_en = self.if_cfg_rd_en
            self.if_cfg_list[0].rd_clk_en = self.if_cfg_rd_clk_en
            self.if_cfg_list[0].rd_addr = self.if_cfg_rd_addr

    @ always_ff((posedge, "clk"), (posedge, "reset"))
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

    # NOTE: Kratos limitation. Struct wiring cannot be easily done using always_comb
    def tile2tile_e2w_struct_wiring(self):
        self.wire(self.strm_packet_e2w_esti[self._params.num_glb_tiles - 1], 0)
        self.wire(self.pcfg_packet_e2w_esti[self._params.num_glb_tiles - 1], 0)
        for i in range(self._params.num_glb_tiles - 1):
            self.wire(self.strm_packet_e2w_esti[i], self.strm_packet_e2w_wsto[i + 1])
            self.wire(self.pcfg_packet_e2w_esti[i], self.pcfg_packet_e2w_wsto[i + 1])

    def tile2tile_w2e_struct_wiring(self):
        self.wire(self.strm_packet_w2e_wsti[0], 0)
        self.wire(self.pcfg_packet_w2e_wsti[0], 0)
        for i in range(1, self._params.num_glb_tiles):
            self.wire(self.strm_packet_w2e_wsti[i], self.strm_packet_w2e_esto[i - 1])
            self.wire(self.pcfg_packet_w2e_wsti[i], self.pcfg_packet_w2e_esto[i - 1])

    @ always_comb
    def tile2tile_e2w_cfg_wiring(self):
        for i in range(self._params.num_glb_tiles):
            if i == self._params.num_glb_tiles - 1:
                self.cgra_cfg_pcfg_rd_en_e2w_esti[i] = 0
                self.cgra_cfg_pcfg_wr_en_e2w_esti[i] = 0
                self.cgra_cfg_pcfg_addr_e2w_esti[i] = 0
                self.cgra_cfg_pcfg_data_e2w_esti[i] = 0
            else:
                self.cgra_cfg_pcfg_rd_en_e2w_esti[i] = self.cgra_cfg_pcfg_rd_en_e2w_wsto[i + 1]
                self.cgra_cfg_pcfg_wr_en_e2w_esti[i] = self.cgra_cfg_pcfg_wr_en_e2w_wsto[i + 1]
                self.cgra_cfg_pcfg_addr_e2w_esti[i] = self.cgra_cfg_pcfg_addr_e2w_wsto[i + 1]
                self.cgra_cfg_pcfg_data_e2w_esti[i] = self.cgra_cfg_pcfg_data_e2w_wsto[i + 1]

    @ always_comb
    def tile2tile_w2e_cfg_wiring(self):
        for i in range(0, self._params.num_glb_tiles):
            if i == 0:
                self.cgra_cfg_jtag_rd_en_wsti[i] = 0
                self.cgra_cfg_jtag_wr_en_wsti[i] = self.cgra_cfg_jtag_gc2glb_wr_en_d
                self.cgra_cfg_jtag_addr_wsti[i] = self.cgra_cfg_jtag_gc2glb_addr_d
                self.cgra_cfg_jtag_data_wsti[i] = self.cgra_cfg_jtag_gc2glb_data_d

                self.cgra_cfg_jtag_rd_en_bypass_wsti[i] = self.cgra_cfg_jtag_gc2glb_rd_en_d
                self.cgra_cfg_jtag_addr_bypass_wsti[i] = self.cgra_cfg_jtag_gc2glb_addr_d

                self.cgra_cfg_pcfg_rd_en_w2e_wsti[i] = 0
                self.cgra_cfg_pcfg_wr_en_w2e_wsti[i] = 0
                self.cgra_cfg_pcfg_addr_w2e_wsti[i] = 0
                self.cgra_cfg_pcfg_data_w2e_wsti[i] = 0
            else:
                self.cgra_cfg_jtag_rd_en_wsti[i] = self.cgra_cfg_jtag_rd_en_esto[i - 1]
                self.cgra_cfg_jtag_wr_en_wsti[i] = self.cgra_cfg_jtag_wr_en_esto[i - 1]
                self.cgra_cfg_jtag_addr_wsti[i] = self.cgra_cfg_jtag_addr_esto[i - 1]
                self.cgra_cfg_jtag_data_wsti[i] = self.cgra_cfg_jtag_data_esto[i - 1]

                self.cgra_cfg_jtag_rd_en_bypass_wsti[i] = self.cgra_cfg_jtag_rd_en_bypass_esto[i - 1]
                self.cgra_cfg_jtag_addr_bypass_wsti[i] = self.cgra_cfg_jtag_addr_bypass_esto[i - 1]

                self.cgra_cfg_pcfg_rd_en_w2e_wsti[i] = self.cgra_cfg_pcfg_rd_en_w2e_esto[i - 1]
                self.cgra_cfg_pcfg_wr_en_w2e_wsti[i] = self.cgra_cfg_pcfg_wr_en_w2e_esto[i - 1]
                self.cgra_cfg_pcfg_addr_w2e_wsti[i] = self.cgra_cfg_pcfg_addr_w2e_esto[i - 1]
                self.cgra_cfg_pcfg_data_w2e_wsti[i] = self.cgra_cfg_pcfg_data_w2e_esto[i - 1]

    def add_glb_tile(self):
        for i in range(self._params.num_glb_tiles):
            self.add_child(f"glb_tile_gen_{i}",
                           self.glb_tile[i],
                           clk=self.clk,
                           clk_en_pcfg_broadcast=clock_en(~self.pcfg_broadcast_stall[i]),
                           clk_en_master=clock_en(self.glb_clk_en_master[i]),
                           clk_en_bank_master=clock_en(self.glb_clk_en_bank_master[i]),
                           reset=self.reset,
                           glb_tile_id=i,

                           # proc
                           if_proc_est_m_wr_en=self.if_proc_list[i + 1].wr_en,
                           if_proc_est_m_wr_clk_en=self.if_proc_list[i + 1].wr_clk_en,
                           if_proc_est_m_wr_addr=self.if_proc_list[i + 1].wr_addr,
                           if_proc_est_m_wr_data=self.if_proc_list[i + 1].wr_data,
                           if_proc_est_m_wr_strb=self.if_proc_list[i + 1].wr_strb,
                           if_proc_est_m_rd_en=self.if_proc_list[i + 1].rd_en,
                           if_proc_est_m_rd_clk_en=self.if_proc_list[i + 1].rd_clk_en,
                           if_proc_est_m_rd_addr=self.if_proc_list[i + 1].rd_addr,
                           if_proc_est_m_rd_data=self.if_proc_list[i + 1].rd_data,
                           if_proc_est_m_rd_data_valid=self.if_proc_list[i + 1].rd_data_valid,

                           if_proc_wst_s_wr_en=self.if_proc_list[i].wr_en,
                           if_proc_wst_s_wr_clk_en=self.if_proc_list[i].wr_clk_en,
                           if_proc_wst_s_wr_addr=self.if_proc_list[i].wr_addr,
                           if_proc_wst_s_wr_data=self.if_proc_list[i].wr_data,
                           if_proc_wst_s_wr_strb=self.if_proc_list[i].wr_strb,
                           if_proc_wst_s_rd_en=self.if_proc_list[i].rd_en,
                           if_proc_wst_s_rd_clk_en=self.if_proc_list[i].rd_clk_en,
                           if_proc_wst_s_rd_addr=self.if_proc_list[i].rd_addr,
                           if_proc_wst_s_rd_data=self.if_proc_list[i].rd_data,
                           if_proc_wst_s_rd_data_valid=self.if_proc_list[i].rd_data_valid,

                           # strm
                           strm_wr_en_e2w_esti=self.strm_packet_e2w_esti[i]["wr"]['wr_en'],
                           strm_wr_strb_e2w_esti=self.strm_packet_e2w_esti[i]["wr"]['wr_strb'],
                           strm_wr_addr_e2w_esti=self.strm_packet_e2w_esti[i]["wr"]['wr_addr'],
                           strm_wr_data_e2w_esti=self.strm_packet_e2w_esti[i]["wr"]['wr_data'],
                           strm_rd_en_e2w_esti=self.strm_packet_e2w_esti[i]["rdrq"]['rd_en'],
                           strm_rd_addr_e2w_esti=self.strm_packet_e2w_esti[i]["rdrq"]['rd_addr'],
                           strm_rd_data_e2w_esti=self.strm_packet_e2w_esti[i]["rdrs"]['rd_data'],
                           strm_rd_data_valid_e2w_esti=self.strm_packet_e2w_esti[i]["rdrs"]['rd_data_valid'],

                           strm_wr_en_w2e_esto=self.strm_packet_w2e_esto[i]["wr"]['wr_en'],
                           strm_wr_strb_w2e_esto=self.strm_packet_w2e_esto[i]["wr"]['wr_strb'],
                           strm_wr_addr_w2e_esto=self.strm_packet_w2e_esto[i]["wr"]['wr_addr'],
                           strm_wr_data_w2e_esto=self.strm_packet_w2e_esto[i]["wr"]['wr_data'],
                           strm_rd_en_w2e_esto=self.strm_packet_w2e_esto[i]["rdrq"]['rd_en'],
                           strm_rd_addr_w2e_esto=self.strm_packet_w2e_esto[i]["rdrq"]['rd_addr'],
                           strm_rd_data_w2e_esto=self.strm_packet_w2e_esto[i]["rdrs"]['rd_data'],
                           strm_rd_data_valid_w2e_esto=self.strm_packet_w2e_esto[i]["rdrs"]['rd_data_valid'],

                           strm_wr_en_w2e_wsti=self.strm_packet_w2e_wsti[i]["wr"]['wr_en'],
                           strm_wr_strb_w2e_wsti=self.strm_packet_w2e_wsti[i]["wr"]['wr_strb'],
                           strm_wr_addr_w2e_wsti=self.strm_packet_w2e_wsti[i]["wr"]['wr_addr'],
                           strm_wr_data_w2e_wsti=self.strm_packet_w2e_wsti[i]["wr"]['wr_data'],
                           strm_rd_en_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrq"]['rd_en'],
                           strm_rd_addr_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrq"]['rd_addr'],
                           strm_rd_data_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrs"]['rd_data'],
                           strm_rd_data_valid_w2e_wsti=self.strm_packet_w2e_wsti[i]["rdrs"]['rd_data_valid'],

                           strm_wr_en_e2w_wsto=self.strm_packet_e2w_wsto[i]["wr"]['wr_en'],
                           strm_wr_strb_e2w_wsto=self.strm_packet_e2w_wsto[i]["wr"]['wr_strb'],
                           strm_wr_addr_e2w_wsto=self.strm_packet_e2w_wsto[i]["wr"]['wr_addr'],
                           strm_wr_data_e2w_wsto=self.strm_packet_e2w_wsto[i]["wr"]['wr_data'],
                           strm_rd_en_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrq"]['rd_en'],
                           strm_rd_addr_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrq"]['rd_addr'],
                           strm_rd_data_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrs"]['rd_data'],
                           strm_rd_data_valid_e2w_wsto=self.strm_packet_e2w_wsto[i]["rdrs"]['rd_data_valid'],

                           # pcfg
                           pcfg_rd_en_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrq"]['rd_en'],
                           pcfg_rd_addr_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrq"]['rd_addr'],
                           pcfg_rd_data_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrs"]['rd_data'],
                           pcfg_rd_data_valid_e2w_esti=self.pcfg_packet_e2w_esti[i]["rdrs"]['rd_data_valid'],

                           pcfg_rd_en_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrq"]['rd_en'],
                           pcfg_rd_addr_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrq"]['rd_addr'],
                           pcfg_rd_data_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrs"]['rd_data'],
                           pcfg_rd_data_valid_w2e_esto=self.pcfg_packet_w2e_esto[i]["rdrs"]['rd_data_valid'],

                           pcfg_rd_en_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrq"]['rd_en'],
                           pcfg_rd_addr_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrq"]['rd_addr'],
                           pcfg_rd_data_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrs"]['rd_data'],
                           pcfg_rd_data_valid_w2e_wsti=self.pcfg_packet_w2e_wsti[i]["rdrs"]['rd_data_valid'],

                           pcfg_rd_en_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrq"]['rd_en'],
                           pcfg_rd_addr_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrq"]['rd_addr'],
                           pcfg_rd_data_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrs"]['rd_data'],
                           pcfg_rd_data_valid_e2w_wsto=self.pcfg_packet_e2w_wsto[i]["rdrs"]['rd_data_valid'],

                           # cfg
                           if_cfg_est_m_wr_en=self.if_cfg_list[i + 1].wr_en,
                           if_cfg_est_m_wr_clk_en=self.if_cfg_list[i + 1].wr_clk_en,
                           if_cfg_est_m_wr_addr=self.if_cfg_list[i + 1].wr_addr,
                           if_cfg_est_m_wr_data=self.if_cfg_list[i + 1].wr_data,
                           if_cfg_est_m_rd_en=self.if_cfg_list[i + 1].rd_en,
                           if_cfg_est_m_rd_clk_en=self.if_cfg_list[i + 1].rd_clk_en,
                           if_cfg_est_m_rd_addr=self.if_cfg_list[i + 1].rd_addr,
                           if_cfg_est_m_rd_data=self.if_cfg_list[i + 1].rd_data,
                           if_cfg_est_m_rd_data_valid=self.if_cfg_list[i + 1].rd_data_valid,

                           if_cfg_wst_s_wr_en=self.if_cfg_list[i].wr_en,
                           if_cfg_wst_s_wr_clk_en=self.if_cfg_list[i].wr_clk_en,
                           if_cfg_wst_s_wr_addr=self.if_cfg_list[i].wr_addr,
                           if_cfg_wst_s_wr_data=self.if_cfg_list[i].wr_data,
                           if_cfg_wst_s_rd_en=self.if_cfg_list[i].rd_en,
                           if_cfg_wst_s_rd_clk_en=self.if_cfg_list[i].rd_clk_en,
                           if_cfg_wst_s_rd_addr=self.if_cfg_list[i].rd_addr,
                           if_cfg_wst_s_rd_data=self.if_cfg_list[i].rd_data,
                           if_cfg_wst_s_rd_data_valid=self.if_cfg_list[i].rd_data_valid,

                           cfg_tile_connected_wsti=self.cfg_tile_connected[i],
                           cfg_tile_connected_esto=self.cfg_tile_connected[i + 1],
                           cfg_pcfg_tile_connected_wsti=self.cfg_pcfg_tile_connected[i],
                           cfg_pcfg_tile_connected_esto=self.cfg_pcfg_tile_connected[i + 1],

                           strm_data_f2g=self.strm_data_f2g[i],
                           strm_data_valid_f2g=self.strm_data_valid_f2g[i],
                           strm_data_g2f=self.strm_data_g2f[i],
                           strm_data_valid_g2f=self.strm_data_valid_g2f[i],
                           data_flush=self.data_flush[i],

                           cgra_cfg_g2f_cfg_wr_en=self.cgra_cfg_g2f_cfg_wr_en[i],
                           cgra_cfg_g2f_cfg_rd_en=self.cgra_cfg_g2f_cfg_rd_en[i],
                           cgra_cfg_g2f_cfg_addr=self.cgra_cfg_g2f_cfg_addr[i],
                           cgra_cfg_g2f_cfg_data=self.cgra_cfg_g2f_cfg_data[i],

                           cgra_cfg_pcfg_wr_en_w2e_wsti=self.cgra_cfg_pcfg_wr_en_w2e_wsti[i],
                           cgra_cfg_pcfg_rd_en_w2e_wsti=self.cgra_cfg_pcfg_rd_en_w2e_wsti[i],
                           cgra_cfg_pcfg_addr_w2e_wsti=self.cgra_cfg_pcfg_addr_w2e_wsti[i],
                           cgra_cfg_pcfg_data_w2e_wsti=self.cgra_cfg_pcfg_data_w2e_wsti[i],

                           cgra_cfg_pcfg_wr_en_w2e_esto=self.cgra_cfg_pcfg_wr_en_w2e_esto[i],
                           cgra_cfg_pcfg_rd_en_w2e_esto=self.cgra_cfg_pcfg_rd_en_w2e_esto[i],
                           cgra_cfg_pcfg_addr_w2e_esto=self.cgra_cfg_pcfg_addr_w2e_esto[i],
                           cgra_cfg_pcfg_data_w2e_esto=self.cgra_cfg_pcfg_data_w2e_esto[i],

                           cgra_cfg_pcfg_wr_en_e2w_esti=self.cgra_cfg_pcfg_wr_en_e2w_esti[i],
                           cgra_cfg_pcfg_rd_en_e2w_esti=self.cgra_cfg_pcfg_rd_en_e2w_esti[i],
                           cgra_cfg_pcfg_addr_e2w_esti=self.cgra_cfg_pcfg_addr_e2w_esti[i],
                           cgra_cfg_pcfg_data_e2w_esti=self.cgra_cfg_pcfg_data_e2w_esti[i],

                           cgra_cfg_pcfg_wr_en_e2w_wsto=self.cgra_cfg_pcfg_wr_en_e2w_wsto[i],
                           cgra_cfg_pcfg_rd_en_e2w_wsto=self.cgra_cfg_pcfg_rd_en_e2w_wsto[i],
                           cgra_cfg_pcfg_addr_e2w_wsto=self.cgra_cfg_pcfg_addr_e2w_wsto[i],
                           cgra_cfg_pcfg_data_e2w_wsto=self.cgra_cfg_pcfg_data_e2w_wsto[i],

                           cgra_cfg_jtag_wr_en_wsti=self.cgra_cfg_jtag_wr_en_wsti[i],
                           cgra_cfg_jtag_rd_en_wsti=self.cgra_cfg_jtag_rd_en_wsti[i],
                           cgra_cfg_jtag_addr_wsti=self.cgra_cfg_jtag_addr_wsti[i],
                           cgra_cfg_jtag_data_wsti=self.cgra_cfg_jtag_data_wsti[i],

                           cgra_cfg_jtag_wr_en_esto=self.cgra_cfg_jtag_wr_en_esto[i],
                           cgra_cfg_jtag_rd_en_esto=self.cgra_cfg_jtag_rd_en_esto[i],
                           cgra_cfg_jtag_addr_esto=self.cgra_cfg_jtag_addr_esto[i],
                           cgra_cfg_jtag_data_esto=self.cgra_cfg_jtag_data_esto[i],

                           cgra_cfg_jtag_rd_en_bypass_wsti=self.cgra_cfg_jtag_rd_en_bypass_wsti[i],
                           cgra_cfg_jtag_addr_bypass_wsti=self.cgra_cfg_jtag_addr_bypass_wsti[i],
                           cgra_cfg_jtag_rd_en_bypass_esto=self.cgra_cfg_jtag_rd_en_bypass_esto[i],
                           cgra_cfg_jtag_addr_bypass_esto=self.cgra_cfg_jtag_addr_bypass_esto[i],

                           strm_g2f_start_pulse=self.strm_g2f_start_pulse_d[i],
                           strm_f2g_start_pulse=self.strm_f2g_start_pulse_d[i],
                           pcfg_start_pulse=self.pcfg_start_pulse_d[i],
                           strm_f2g_interrupt_pulse=self.strm_f2g_interrupt_pulse_w[i],
                           strm_g2f_interrupt_pulse=self.strm_g2f_interrupt_pulse_w[i],
                           pcfg_g2f_interrupt_pulse=self.pcfg_g2f_interrupt_pulse_w[i])

    @ always_ff((posedge, "clk"), (posedge, "reset"))
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


def GlobalBufferMagma(params: GlobalBufferParams):
    dut = GlobalBuffer(params)
    circ = to_magma(dut, flatten_array=True)

    return FromMagma(circ)
