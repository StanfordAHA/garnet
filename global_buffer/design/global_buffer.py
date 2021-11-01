from kratos import Generator, always_ff, posedge, always_comb, clock_en, ext
from global_buffer.design.glb_tile import GlbTile
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.pipeline import Pipeline


class GlobalBuffer(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("global_buffer")
        self._params = _params
        self.header = GlbHeader(self._params)
        self.glb_top_pipeline_depth = 1

        self.clk = self.clock("clk")
        self.stall = self.input("stall", self._params.num_glb_tiles)
        self.reset = self.reset("reset")
        # TODO: Why cgra_stall has same width as num_glb_tiles
        self.cgra_stall_in = self.input(
            "cgra_stall_in", self._params.num_glb_tiles)
        self.cgra_stall = self.output(
            "cgra_stall", self._params.cgra_per_glb, size=self._params.num_glb_tiles, packed=True)

        self.proc_wr_en = self.input(
            "proc_wr_en", 1)
        self.proc_wr_strb = self.input(
            "proc_wr_strb", self._params.bank_data_width // 8)
        self.proc_wr_addr = self.input(
            "proc_wr_addr", self._params.glb_addr_width)
        self.proc_wr_data = self.input(
            "proc_wr_data", self._params.bank_data_width)
        self.proc_rd_en = self.input(
            "proc_rd_en", 1)
        self.proc_rd_addr = self.input(
            "proc_rd_addr", self._params.glb_addr_width)
        self.proc_rd_data = self.output(
            "proc_rd_data", self._params.bank_data_width)
        self.proc_rd_data_valid = self.output(
            "proc_rd_data_valid", 1)

        self.if_cfg_wr_en = self.input(
            "if_cfg_wr_en", 1)
        self.if_cfg_wr_addr = self.input(
            "if_cfg_wr_addr", self._params.axi_addr_width)
        self.if_cfg_wr_data = self.input(
            "if_cfg_wr_data", self._params.axi_data_width)
        self.if_cfg_rd_en = self.input(
            "if_cfg_rd_en", 1)
        self.if_cfg_rd_addr = self.input(
            "if_cfg_rd_addr", self._params.axi_addr_width)
        self.if_cfg_rd_data = self.output(
            "if_cfg_rd_data", self._params.axi_data_width)
        self.if_cfg_rd_data_valid = self.output(
            "if_cfg_rd_data_valid", 1)

        self.if_sram_cfg_wr_en = self.input(
            "if_sram_cfg_wr_en", 1)
        self.if_sram_cfg_wr_addr = self.input(
            "if_sram_cfg_wr_addr", self._params.glb_addr_width)
        self.if_sram_cfg_wr_data = self.input(
            "if_sram_cfg_wr_data", self._params.axi_data_width)
        self.if_sram_cfg_rd_en = self.input(
            "if_sram_cfg_rd_en", 1)
        self.if_sram_cfg_rd_addr = self.input(
            "if_sram_cfg_rd_addr", self._params.glb_addr_width)
        self.if_sram_cfg_rd_data = self.output(
            "if_sram_cfg_rd_data", self._params.axi_data_width)
        self.if_sram_cfg_rd_data_valid = self.output(
            "if_sram_cfg_rd_data_valid", 1)

        self.cgra_cfg_jtag_gc2glb_wr_en = self.input(
            "cgra_cfg_jtag_gc2glb_wr_en", 1)
        self.cgra_cfg_jtag_gc2glb_rd_en = self.input(
            "cgra_cfg_jtag_gc2glb_rd_en", 1)
        self.cgra_cfg_jtag_gc2glb_addr = self.input(
            "cgra_cfg_jtag_gc2glb_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_gc2glb_data = self.input(
            "cgra_cfg_jtag_gc2glb_data", self._params.cgra_cfg_data_width)

        self.stream_data_f2g = self.input(
            "stream_data_f2g", self._params.cgra_per_glb * self._params.cgra_data_width, size=self._params.num_glb_tiles, packed=True)
        self.stream_data_valid_f2g = self.input(
            "stream_data_valid_f2g", self._params.cgra_per_glb, size=self._params.num_glb_tiles, packed=True)
        self.stream_data_g2f = self.output(
            "stream_data_g2f", self._params.cgra_per_glb * self._params.cgra_data_width, size=self._params.num_glb_tiles, packed=True)
        self.stream_data_valid_g2f = self.output(
            "stream_data_valid_g2f", self._params.cgra_per_glb, size=self._params.num_glb_tiles, packed=True)

        self.cgra_cfg_g2f_cfg_wr_en = self.output(
            "cgra_cfg_g2f_cfg_wr_en", self._params.cgra_per_glb, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_g2f_cfg_rd_en = self.output(
            "cgra_cfg_g2f_cfg_rd_en", self._params.cgra_per_glb, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_g2f_cfg_addr = self.output(
            "cgra_cfg_g2f_cfg_addr", self._params.cgra_per_glb * self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_g2f_cfg_data = self.output(
            "cgra_cfg_g2f_cfg_data", self._params.cgra_per_glb * self._params.cgra_cfg_data_width, size=self._params.num_glb_tiles, packed=True)

        self.strm_start_pulse = self.input(
            "strm_start_pulse", self._params.num_glb_tiles)
        self.pcfg_start_pulse = self.input(
            "pcfg_start_pulse", self._params.num_glb_tiles)
        self.strm_f2g_interrupt_pulse = self.output(
            "strm_f2g_interrupt_pulse", self._params.num_glb_tiles)
        self.strm_g2f_interrupt_pulse = self.output(
            "strm_g2f_interrupt_pulse", self._params.num_glb_tiles)
        self.pcfg_g2f_interrupt_pulse = self.output(
            "pcfg_g2f_interrupt_pulse", self._params.num_glb_tiles)

        # local variables
        self.proc_packet_e2w_esti = self.var(
            "proc_packet_e2w_esti", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)
        self.proc_packet_w2e_wsti = self.var(
            "proc_packet_w2e_wsti", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)
        self.proc_packet_e2w_wsto = self.var(
            "proc_packet_e2w_wsto", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)
        self.proc_packet_w2e_esto = self.var(
            "proc_packet_w2e_esto", self.header.packet_t, size=self._params.num_glb_tiles, packed=True)

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

        self.cfg_tile_connected = self.var(
            "cfg_tile_connected", self._params.num_glb_tiles+1)
        self.cfg_pcfg_tile_connected = self.var(
            "cfg_pcfg_tile_connected", self._params.num_glb_tiles+1)
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

        self.cgra_cfg_jtag_wsti_rd_en_bypass = self.var(
            "cgra_cfg_jtag_wsti_rd_en_bypass", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_wsti_addr_bypass = self.var(
            "cgra_cfg_jtag_wsti_addr_bypass", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_esto_rd_en_bypass = self.var(
            "cgra_cfg_jtag_esto_rd_en_bypass", 1, size=self._params.num_glb_tiles, packed=True)
        self.cgra_cfg_jtag_esto_addr_bypass = self.var(
            "cgra_cfg_jtag_esto_addr_bypass", self._params.cgra_cfg_addr_width, size=self._params.num_glb_tiles, packed=True)

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

        self.glb_tile = []
        for i in range(self._params.num_glb_tiles):
            self.glb_tile.append(GlbTile(_params=self._params))

        # TODO:
        for i in range(self._params.num_glb_tiles):
            self.wire(self.cgra_stall[i], ext(
                self.cgra_stall_in[i], self._params.cgra_per_glb))

        self.add_glb_tile()
        self.add_always(self.left_edge_proc_ff)
        self.add_always(self.left_edge_cfg_ff)
        self.add_always(self.left_edge_sram_cfg_ff)
        self.add_always(self.left_edge_logic)
        self.add_always(self.right_edge_proc_logic)
        self.add_always(self.right_edge_logic)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def left_edge_proc_ff(self):
        if self.reset:
            self.proc_packet_w2e_wsti[0]['wr_en'] = 0
            self.proc_packet_w2e_wsti[0]['wr_strb'] = 0
            self.proc_packet_w2e_wsti[0]['wr_addr'] = 0
            self.proc_packet_w2e_wsti[0]['wr_data'] = 0
            self.proc_packet_w2e_wsti[0]['rd_en'] = 0
            self.proc_packet_w2e_wsti[0]['rd_addr'] = 0
            self.proc_rd_data = 0
            self.proc_rd_data_valid = 0
        else:
            self.proc_packet_w2e_wsti[0]['wr_en'] = self.proc_wr_en
            self.proc_packet_w2e_wsti[0]['wr_strb'] = self.proc_wr_strb
            self.proc_packet_w2e_wsti[0]['wr_addr'] = self.proc_wr_addr
            self.proc_packet_w2e_wsti[0]['wr_data'] = self.proc_wr_data
            self.proc_packet_w2e_wsti[0]['rd_en'] = self.proc_rd_en
            self.proc_packet_w2e_wsti[0]['rd_addr'] = self.proc_rd_addr
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

    @always_comb
    def left_edge_logic(self):
        self.strm_packet_w2e_wsti[0] = 0
        self.pcfg_packet_w2e_wsti[0] = 0

    @always_comb
    def right_edge_proc_logic(self):
        self.proc_packet_e2w_esti[self._params.num_glb_tiles -
                                  1] = self.proc_packet_w2e_esto[self._params.num_glb_tiles-1]

    @always_comb
    def right_edge_logic(self):
        self.strm_packet_e2w_esti[self._params.num_glb_tiles-1] = 0
        self.pcfg_packet_e2w_esti[self._params.num_glb_tiles-1] = 0

    # def add_pipeline(self):
    #     pipeline_in = concat(self.stall_w, self.cgra_stall_w, self.c)
    #     self.glb_top_pipeline = Pipeline(width=1, depth=self.glb_top_pipeline_depth)

    #     self.add_child("ld_dma_start_pulse_pipeline",
    #                    self.ld_dma_start_pulse_pipeline,
    #                    clk=self.clk,
    #                    clk_en=self.clk_en,
    #                    reset=self.reset,
    #                    in_=self.ld_dma_start_pulse_r,
    #                    out_=self.ld_dma_start_pulse_d2)

    #     fo
    #     if self.reset:
    #         self.stall_d = 0
    #         self.strm_start_pulse_d = 0
    #         self.pcfg_start_pulse_d = 0

    def add_glb_tile(self):
        for i in range(self._params.num_glb_tiles):
            self.add_child(f"glb_tile_{i}",
                                      self.glb_tile[i],
                                      clk=self.clk,
                                      clk_en=clock_en(~self.stall[i]),
                                      reset=self.reset,
                                      glb_tile_id=i,

                                      proc_wr_en_e2w_esti=self.proc_packet_e2w_esti[i]['wr_en'],
                                      proc_wr_strb_e2w_esti=self.proc_packet_e2w_esti[i]['wr_strb'],
                                      proc_wr_addr_e2w_esti=self.proc_packet_e2w_esti[i]['wr_addr'],
                                      proc_wr_data_e2w_esti=self.proc_packet_e2w_esti[i]['wr_data'],
                                      proc_rd_en_e2w_esti=self.proc_packet_e2w_esti[i]['rd_en'],
                                      proc_rd_addr_e2w_esti=self.proc_packet_e2w_esti[i]['rd_addr'],
                                      proc_rd_data_e2w_esti=self.proc_packet_e2w_esti[i]['rd_data'],
                                      proc_rd_data_valid_e2w_esti=self.proc_packet_e2w_esti[
                                          i]['rd_data_valid'],

                                      proc_wr_en_w2e_esto=self.proc_packet_w2e_esto[i]['wr_en'],
                                      proc_wr_strb_w2e_esto=self.proc_packet_w2e_esto[i]['wr_strb'],
                                      proc_wr_addr_w2e_esto=self.proc_packet_w2e_esto[i]['wr_addr'],
                                      proc_wr_data_w2e_esto=self.proc_packet_w2e_esto[i]['wr_data'],
                                      proc_rd_en_w2e_esto=self.proc_packet_w2e_esto[i]['rd_en'],
                                      proc_rd_addr_w2e_esto=self.proc_packet_w2e_esto[i]['rd_addr'],
                                      proc_rd_data_w2e_esto=self.proc_packet_w2e_esto[i]['rd_data'],
                                      proc_rd_data_valid_w2e_esto=self.proc_packet_w2e_esto[
                                          i]['rd_data_valid'],

                                      proc_wr_en_w2e_wsti=self.proc_packet_w2e_wsti[i]['wr_en'],
                                      proc_wr_strb_w2e_wsti=self.proc_packet_w2e_wsti[i]['wr_strb'],
                                      proc_wr_addr_w2e_wsti=self.proc_packet_w2e_wsti[i]['wr_addr'],
                                      proc_wr_data_w2e_wsti=self.proc_packet_w2e_wsti[i]['wr_data'],
                                      proc_rd_en_w2e_wsti=self.proc_packet_w2e_wsti[i]['rd_en'],
                                      proc_rd_addr_w2e_wsti=self.proc_packet_w2e_wsti[i]['rd_addr'],
                                      proc_rd_data_w2e_wsti=self.proc_packet_w2e_wsti[i]['rd_data'],
                                      proc_rd_data_valid_w2e_wsti=self.proc_packet_w2e_wsti[
                                          i]['rd_data_valid'],

                                      proc_wr_en_e2w_wsto=self.proc_packet_e2w_wsto[i]['wr_en'],
                                      proc_wr_strb_e2w_wsto=self.proc_packet_e2w_wsto[i]['wr_strb'],
                                      proc_wr_addr_e2w_wsto=self.proc_packet_e2w_wsto[i]['wr_addr'],
                                      proc_wr_data_e2w_wsto=self.proc_packet_e2w_wsto[i]['wr_data'],
                                      proc_rd_en_e2w_wsto=self.proc_packet_e2w_wsto[i]['rd_en'],
                                      proc_rd_addr_e2w_wsto=self.proc_packet_e2w_wsto[i]['rd_addr'],
                                      proc_rd_data_e2w_wsto=self.proc_packet_e2w_wsto[i]['rd_data'],
                                      proc_rd_data_valid_e2w_wsto=self.proc_packet_e2w_wsto[
                                          i]['rd_data_valid'],

                                      strm_wr_en_e2w_esti=self.strm_packet_e2w_esti[i]['wr_en'],
                                      strm_wr_strb_e2w_esti=self.strm_packet_e2w_esti[i]['wr_strb'],
                                      strm_wr_addr_e2w_esti=self.strm_packet_e2w_esti[i]['wr_addr'],
                                      strm_wr_data_e2w_esti=self.strm_packet_e2w_esti[i]['wr_data'],
                                      strm_rd_en_e2w_esti=self.strm_packet_e2w_esti[i]['rd_en'],
                                      strm_rd_addr_e2w_esti=self.strm_packet_e2w_esti[i]['rd_addr'],
                                      strm_rd_data_e2w_esti=self.strm_packet_e2w_esti[i]['rd_data'],
                                      strm_rd_data_valid_e2w_esti=self.strm_packet_e2w_esti[
                                          i]['rd_data_valid'],

                                      strm_wr_en_w2e_esto=self.strm_packet_w2e_esto[i]['wr_en'],
                                      strm_wr_strb_w2e_esto=self.strm_packet_w2e_esto[i]['wr_strb'],
                                      strm_wr_addr_w2e_esto=self.strm_packet_w2e_esto[i]['wr_addr'],
                                      strm_wr_data_w2e_esto=self.strm_packet_w2e_esto[i]['wr_data'],
                                      strm_rd_en_w2e_esto=self.strm_packet_w2e_esto[i]['rd_en'],
                                      strm_rd_addr_w2e_esto=self.strm_packet_w2e_esto[i]['rd_addr'],
                                      strm_rd_data_w2e_esto=self.strm_packet_w2e_esto[i]['rd_data'],
                                      strm_rd_data_valid_w2e_esto=self.strm_packet_w2e_esto[
                                          i]['rd_data_valid'],

                                      strm_wr_en_w2e_wsti=self.strm_packet_w2e_wsti[i]['wr_en'],
                                      strm_wr_strb_w2e_wsti=self.strm_packet_w2e_wsti[i]['wr_strb'],
                                      strm_wr_addr_w2e_wsti=self.strm_packet_w2e_wsti[i]['wr_addr'],
                                      strm_wr_data_w2e_wsti=self.strm_packet_w2e_wsti[i]['wr_data'],
                                      strm_rd_en_w2e_wsti=self.strm_packet_w2e_wsti[i]['rd_en'],
                                      strm_rd_addr_w2e_wsti=self.strm_packet_w2e_wsti[i]['rd_addr'],
                                      strm_rd_data_w2e_wsti=self.strm_packet_w2e_wsti[i]['rd_data'],
                                      strm_rd_data_valid_w2e_wsti=self.strm_packet_w2e_wsti[
                                          i]['rd_data_valid'],

                                      strm_wr_en_e2w_wsto=self.strm_packet_e2w_wsto[i]['wr_en'],
                                      strm_wr_strb_e2w_wsto=self.strm_packet_e2w_wsto[i]['wr_strb'],
                                      strm_wr_addr_e2w_wsto=self.strm_packet_e2w_wsto[i]['wr_addr'],
                                      strm_wr_data_e2w_wsto=self.strm_packet_e2w_wsto[i]['wr_data'],
                                      strm_rd_en_e2w_wsto=self.strm_packet_e2w_wsto[i]['rd_en'],
                                      strm_rd_addr_e2w_wsto=self.strm_packet_e2w_wsto[i]['rd_addr'],
                                      strm_rd_data_e2w_wsto=self.strm_packet_e2w_wsto[i]['rd_data'],
                                      strm_rd_data_valid_e2w_wsto=self.strm_packet_e2w_wsto[
                                          i]['rd_data_valid'],

                                      pcfg_rd_en_e2w_esti=self.pcfg_packet_e2w_esti[i]['rd_en'],
                                      pcfg_rd_addr_e2w_esti=self.pcfg_packet_e2w_esti[i]['rd_addr'],
                                      pcfg_rd_data_e2w_esti=self.pcfg_packet_e2w_esti[i]['rd_data'],
                                      pcfg_rd_data_valid_e2w_esti=self.pcfg_packet_e2w_esti[
                                          i]['rd_data_valid'],

                                      pcfg_rd_en_w2e_esto=self.pcfg_packet_w2e_esto[i]['rd_en'],
                                      pcfg_rd_addr_w2e_esto=self.pcfg_packet_w2e_esto[i]['rd_addr'],
                                      pcfg_rd_data_w2e_esto=self.pcfg_packet_w2e_esto[i]['rd_data'],
                                      pcfg_rd_data_valid_w2e_esto=self.pcfg_packet_w2e_esto[
                                          i]['rd_data_valid'],

                                      pcfg_rd_en_w2e_wsti=self.pcfg_packet_w2e_wsti[i]['rd_en'],
                                      pcfg_rd_addr_w2e_wsti=self.pcfg_packet_w2e_wsti[i]['rd_addr'],
                                      pcfg_rd_data_w2e_wsti=self.pcfg_packet_w2e_wsti[i]['rd_data'],
                                      pcfg_rd_data_valid_w2e_wsti=self.pcfg_packet_w2e_wsti[
                                          i]['rd_data_valid'],

                                      pcfg_rd_en_e2w_wsto=self.pcfg_packet_e2w_wsto[i]['rd_en'],
                                      pcfg_rd_addr_e2w_wsto=self.pcfg_packet_e2w_wsto[i]['rd_addr'],
                                      pcfg_rd_data_e2w_wsto=self.pcfg_packet_e2w_wsto[i]['rd_data'],
                                      pcfg_rd_data_valid_e2w_wsto=self.pcfg_packet_e2w_wsto[
                                          i]['rd_data_valid'],

                                      if_cfg_est_m_wr_en=self.if_cfg_list[i+1].wr_en,
                                      if_cfg_est_m_wr_addr=self.if_cfg_list[i+1].wr_addr,
                                      if_cfg_est_m_wr_data=self.if_cfg_list[i+1].wr_data,
                                      if_cfg_est_m_rd_en=self.if_cfg_list[i+1].rd_en,
                                      if_cfg_est_m_rd_addr=self.if_cfg_list[i+1].rd_addr,

                                      if_cfg_wst_s_wr_en=self.if_cfg_list[i].wr_en,
                                      if_cfg_wst_s_wr_addr=self.if_cfg_list[i].wr_addr,
                                      if_cfg_wst_s_wr_data=self.if_cfg_list[i].wr_data,
                                      if_cfg_wst_s_rd_en=self.if_cfg_list[i].rd_en,
                                      if_cfg_wst_s_rd_addr=self.if_cfg_list[i].rd_addr,
                                      if_cfg_wst_s_rd_data=self.if_cfg_list[i].rd_data,
                                      if_cfg_wst_s_rd_data_valid=self.if_cfg_list[i].rd_data_valid,

                                      if_sram_cfg_est_m_wr_en=self.if_sram_cfg_list[i+1].wr_en,
                                      if_sram_cfg_est_m_wr_addr=self.if_sram_cfg_list[i+1].wr_addr,
                                      if_sram_cfg_est_m_wr_data=self.if_sram_cfg_list[i+1].wr_data,
                                      if_sram_cfg_est_m_rd_en=self.if_sram_cfg_list[i+1].rd_en,
                                      if_sram_cfg_est_m_rd_addr=self.if_sram_cfg_list[i+1].rd_addr,

                                      if_sram_cfg_wst_s_wr_en=self.if_sram_cfg_list[i].wr_en,
                                      if_sram_cfg_wst_s_wr_addr=self.if_sram_cfg_list[i].wr_addr,
                                      if_sram_cfg_wst_s_wr_data=self.if_sram_cfg_list[i].wr_data,
                                      if_sram_cfg_wst_s_rd_en=self.if_sram_cfg_list[i].rd_en,
                                      if_sram_cfg_wst_s_rd_addr=self.if_sram_cfg_list[i].rd_addr,
                                      if_sram_cfg_wst_s_rd_data=self.if_sram_cfg_list[i].rd_data,
                                      if_sram_cfg_wst_s_rd_data_valid=self.if_sram_cfg_list[i].rd_data_valid,

                                      cfg_tile_connected_wsti=self.cfg_tile_connected[i],
                                      cfg_tile_connected_esto=self.cfg_tile_connected[i+1],
                                      cfg_pcfg_tile_connected_wsti=self.cfg_pcfg_tile_connected[i],
                                      cfg_pcfg_tile_connected_esto=self.cfg_pcfg_tile_connected[i+1],

                                      stream_data_f2g=self.stream_data_f2g[i],
                                      stream_data_valid_f2g=self.stream_data_valid_f2g[i],
                                      stream_data_g2f=self.stream_data_g2f[i],
                                      stream_data_valid_g2f=self.stream_data_valid_g2f[i],

                                      cgra_cfg_g2f_cfg_wr_en=self.cgra_cfg_g2f_cfg_wr_en[i],
                                      cgra_cfg_g2f_cfg_rd_en=self.cgra_cfg_g2f_cfg_rd_en[i],
                                      cgra_cfg_g2f_cfg_addr=self.cgra_cfg_g2f_cfg_addr[i],
                                      cgra_cfg_g2f_cfg_data=self.cgra_cfg_g2f_cfg_data[i],

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

                                      cgra_cfg_jtag_wsti_rd_en_bypass=self.cgra_cfg_jtag_wsti_rd_en_bypass[
                                          i],
                                      cgra_cfg_jtag_wsti_addr_bypass=self.cgra_cfg_jtag_wsti_addr_bypass[
                                          i],
                                      cgra_cfg_jtag_esto_rd_en_bypass=self.cgra_cfg_jtag_esto_rd_en_bypass[
                                          i],
                                      cgra_cfg_jtag_esto_addr_bypass=self.cgra_cfg_jtag_esto_addr_bypass[
                                          i],

                                      strm_start_pulse=self.strm_start_pulse[i],
                                      pcfg_start_pulse=self.pcfg_start_pulse[i],
                                      strm_f2g_interrupt_pulse=self.strm_f2g_interrupt_pulse[i],
                                      strm_g2f_interrupt_pulse=self.strm_g2f_interrupt_pulse[i],
                                      pcfg_g2f_interrupt_pulse=self.pcfg_g2f_interrupt_pulse[i])

            # TODO: Due to Kratos bug, I wire these interface ports manually
            if i == (self._params.num_glb_tiles - 1):
                self.wire(self.glb_tile[i].if_cfg_est_m_rd_data, 0)
                self.wire(self.glb_tile[i].if_cfg_est_m_rd_data_valid, 0)
                self.wire(self.glb_tile[i].if_sram_cfg_est_m_rd_data, 0)
                self.wire(self.glb_tile[i].if_sram_cfg_est_m_rd_data_valid, 0)
            else:
                self.wire(self.glb_tile[i].if_cfg_est_m_rd_data,
                          self.if_cfg_list[i+1].rd_data)
                self.wire(self.glb_tile[i].if_cfg_est_m_rd_data_valid,
                          self.if_cfg_list[i+1].rd_data_valid)
                self.wire(self.glb_tile[i].if_sram_cfg_est_m_rd_data,
                          self.if_sram_cfg_list[i+1].rd_data)
                self.wire(self.glb_tile[i].if_sram_cfg_est_m_rd_data_valid,
                          self.if_sram_cfg_list[i+1].rd_data_valid)
