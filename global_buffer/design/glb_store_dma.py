from kratos import Generator, always_ff, always_comb, posedge, const, resize, ext, clog2
from global_buffer.design.glb_loop_iter import GlbLoopIter
from global_buffer.design.glb_sched_gen import GlbSchedGen
from global_buffer.design.glb_addr_gen import GlbAddrGen
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen


class GlbStoreDma(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_store_dma")
        self._params = _params
        self.header = GlbHeader(self._params)
        assert self._params.bank_data_width == self._params.cgra_data_width * 4

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.clk_en_dma2bank = self.output("clk_en_dma2bank", 1)

        self.data_f2g = self.input("data_f2g", width=self._params.cgra_data_width,
                                   size=self._params.cgra_per_glb, packed=True)
        self.data_valid_f2g = self.input("data_valid_f2g", 1, size=self._params.cgra_per_glb, packed=True)

        self.wr_packet_dma2bank = self.output("wr_packet_dma2bank", self.header.wr_packet_t)
        self.wr_packet_dma2ring = self.output("wr_packet_dma2ring", self.header.wr_packet_t)

        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)
        self.cfg_st_dma_num_repeat = self.input("cfg_st_dma_num_repeat", clog2(self._params.queue_depth) + 1)
        self.cfg_st_dma_ctrl_mode = self.input("cfg_st_dma_ctrl_mode", 2)
        self.cfg_st_dma_ctrl_use_valid = self.input("cfg_st_dma_ctrl_use_valid", 1)
        self.cfg_data_network_latency = self.input("cfg_data_network_latency", self._params.latency_width)
        self.cfg_st_dma_header = self.input("cfg_st_dma_header", self.header.cfg_dma_header_t,
                                            size=self._params.queue_depth, explicit_array=True)
        self.cfg_data_network_f2g_mux = self.input("cfg_data_network_f2g_mux", self._params.cgra_per_glb)

        self.st_dma_start_pulse = self.input("st_dma_start_pulse", 1)
        self.st_dma_done_interrupt = self.output("st_dma_done_interrupt", 1)

        # localparam
        self.cgra_strb_width = self._params.cgra_data_width // 8
        self.cgra_strb_value = 2 ** (self._params.cgra_data_width // 8) - 1

        # local variables
        self.wr_packet_dma2bank_w = self.var("wr_packet_dma2bank_w", self.header.wr_packet_t)
        self.wr_packet_dma2ring_w = self.var("wr_packet_dma2ring_w", self.header.wr_packet_t)
        self.data_f2g_r = self.var("data_f2g_r", width=self._params.cgra_data_width,
                                   size=self._params.cgra_per_glb, packed=True)
        self.data_valid_f2g_r = self.var("data_valid_f2g_r", 1, size=self._params.cgra_per_glb, packed=True)
        self.strm_data = self.var("strm_data", width=self._params.cgra_data_width)
        self.strm_data_valid = self.var("strm_data_valid", width=1)
        self.st_dma_done_pulse = self.var("st_dma_done_pulse", 1)
        self.st_dma_done_pulse_last = self.var("st_dma_done_pulse_last", 1)
        self.strm_wr_data_w = self.var("strm_wr_data_w", width=self._params.cgra_data_width)
        self.strm_wr_addr_w = self.var("strm_wr_addr_w", width=self._params.glb_addr_width)
        self.last_strm_wr_addr_r = self.var("last_strm_wr_addr_r", width=self._params.glb_addr_width)
        self.strm_wr_en_w = self.var("strm_wr_en_w", width=1)
        self.strm_data_sel = self.var("strm_data_sel", self._params.bank_byte_offset - self._params.cgra_byte_offset)

        self.bank_addr_match = self.var("bank_addr_match", 1)
        self.bank_wr_en = self.var("bank_wr_en", 1)
        self.bank_wr_addr = self.var("bank_wr_addr", width=self._params.glb_addr_width)
        self.bank_wr_data_cache_r = self.var("bank_wr_data_cache_r", self._params.bank_data_width)
        self.bank_wr_data_cache_w = self.var("bank_wr_data_cache_w", self._params.bank_data_width)
        self.bank_wr_strb_cache_r = self.var("bank_wr_strb_cache_r", self._params.bank_strb_width)
        self.bank_wr_strb_cache_w = self.var("bank_wr_strb_cache_w", self._params.bank_strb_width)

        self.done_pulse_w = self.var("done_pulse_w", 1)
        self.st_dma_start_pulse_next = self.var("st_dma_start_pulse_next", 1)
        self.st_dma_start_pulse_r = self.var("st_dma_start_pulse_r", 1)
        self.is_first = self.var("is_first", 1)
        self.is_last = self.var("is_last", 1)
        self.strm_run = self.var("strm_run", 1)
        self.loop_done = self.var("loop_done", 1)
        self.cycle_valid = self.var("cycle_valid", 1)
        self.cycle_valid_muxed = self.var("cycle_valid_muxed", 1)
        self.cycle_count = self.var("cycle_count", self._params.cycle_count_width)
        self.cycle_current_addr = self.var("cycle_current_addr", self._params.cycle_count_width)
        self.data_current_addr = self.var("data_current_addr", self._params.glb_addr_width + 1)
        self.loop_mux_sel = self.var("loop_mux_sel", clog2(self._params.loop_level))
        self.repeat_cnt = self.var("repeat_cnt", clog2(self._params.queue_depth) + 1)

        if self._params.queue_depth != 1:
            self.queue_sel_r = self.var("queue_sel_r", max(1, clog2(self.repeat_cnt.width)))

        # Current dma header
        self.current_dma_header = self.var("current_dma_header", self.header.cfg_dma_header_t)
        if self._params.queue_depth == 1:
            self.wire(self.cfg_st_dma_header, self.current_dma_header)
        else:
            self.wire(self.cfg_st_dma_header[self.queue_sel_r], self.current_dma_header)

        if self._params.queue_depth != 1:
            self.add_always(self.queue_sel_ff)

        self.add_always(self.repeat_cnt_ff)
        self.add_always(self.is_first_ff)
        self.add_always(self.is_last_ff)
        self.add_always(self.strm_run_ff)
        self.add_always(self.st_dma_start_pulse_logic)
        self.add_always(self.st_dma_start_pulse_ff)
        self.add_always(self.cycle_counter)
        self.add_always(self.data_f2g_ff)
        self.add_always(self.data_f2g_logic)
        self.add_always(self.cycle_valid_comb)
        self.add_always(self.strm_wr_packet_comb)
        self.add_always(self.last_strm_wr_addr_ff)
        self.add_always(self.strm_data_sel_comb)
        self.add_always(self.bank_wr_packet_cache_comb)
        self.add_always(self.bank_wr_packet_cache_ff)
        self.add_always(self.bank_wr_packet_logic)
        self.add_always(self.wr_packet_ff)
        self.add_always(self.wr_packet_logic)
        self.add_dma2bank_clk_en()
        self.add_always(self.strm_done_pulse_logic)
        self.add_done_pulse_pipeline()
        self.add_done_pulse_last_pipeline()
        self.add_always(self.interrupt_ff)

        # Loop iteration shared for cycle and data
        self.loop_iter = GlbLoopIter(self._params)
        self.add_child("loop_iter",
                       self.loop_iter,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       step=self.cycle_valid_muxed,
                       mux_sel_out=self.loop_mux_sel,
                       restart=self.loop_done)
        self.wire(self.loop_iter.dim, self.current_dma_header[f"dim"])
        for i in range(self._params.loop_level):
            self.wire(self.loop_iter.ranges[i], self.current_dma_header[f"range_{i}"])

        # Cycle stride
        self.cycle_stride_sched_gen = GlbSchedGen(self._params)
        self.add_child("cycle_stride_sched_gen",
                       self.cycle_stride_sched_gen,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       restart=self.st_dma_start_pulse_r,
                       cycle_count=self.cycle_count,
                       current_addr=self.cycle_current_addr,
                       finished=self.loop_done,
                       valid_output=self.cycle_valid)

        self.cycle_stride_addr_gen = GlbAddrGen(self._params)
        self.cycle_stride_addr_gen.p_addr_width.value = self._params.cycle_count_width
        self.add_child("cycle_stride_addr_gen",
                       self.cycle_stride_addr_gen,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       restart=self.st_dma_start_pulse_r,
                       step=self.cycle_valid_muxed,
                       mux_sel=self.loop_mux_sel)
        self.wire(self.cycle_stride_addr_gen.addr_out, self.cycle_current_addr)
        self.wire(self.cycle_stride_addr_gen.start_addr, self.current_dma_header[f"cycle_start_addr"])
        for i in range(self._params.loop_level):
            self.wire(self.cycle_stride_addr_gen.strides[i],
                      self.current_dma_header[f"cycle_stride_{i}"])

        # Data stride
        self.data_stride_addr_gen = GlbAddrGen(self._params)
        self.data_stride_addr_gen.p_addr_width.value = self._params.glb_addr_width + 1
        self.add_child("data_stride_addr_gen",
                       self.data_stride_addr_gen,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       restart=self.st_dma_start_pulse_r,
                       step=self.cycle_valid_muxed,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.data_current_addr)
        self.wire(self.data_stride_addr_gen.start_addr, ext(self.current_dma_header[f"start_addr"],
                                                            self._params.glb_addr_width + 1))
        for i in range(self._params.loop_level):
            self.wire(self.data_stride_addr_gen.strides[i], self.current_dma_header[f"stride_{i}"])

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def repeat_cnt_ff(self):
        if self.reset:
            self.repeat_cnt = 0
        else:
            if self.cfg_st_dma_ctrl_mode == 2:
                if self.st_dma_done_pulse:
                    if (self.repeat_cnt + 1) < self.cfg_st_dma_num_repeat:
                        self.repeat_cnt += 1
            elif self.cfg_st_dma_ctrl_mode == 3:
                if self.st_dma_done_pulse:
                    if (((self.repeat_cnt + 1) < self.cfg_st_dma_num_repeat)
                            & ((self.repeat_cnt + 1) < self._params.queue_depth)):
                        self.repeat_cnt += 1

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def queue_sel_ff(self):
        if self.reset:
            self.queue_sel_r = 0
        else:
            if self.cfg_st_dma_ctrl_mode == 3:
                if self.st_dma_done_pulse:
                    if (self.repeat_cnt + 1) < self.cfg_st_dma_num_repeat:
                        self.queue_sel_r = self.queue_sel_r + 1
            else:
                self.queue_sel_r = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def is_first_ff(self):
        if self.reset:
            self.is_first = 0
        else:
            if self.st_dma_start_pulse_r:
                self.is_first = 1
            elif self.strm_wr_en_w:
                self.is_first = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def is_last_ff(self):
        if self.reset:
            self.is_last = 0
        else:
            if self.loop_done:
                self.is_last = 1
            elif self.bank_wr_en:
                self.is_last = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def strm_run_ff(self):
        if self.reset:
            self.strm_run = 0
        else:
            if self.st_dma_start_pulse_r:
                self.strm_run = 1
            elif self.loop_done:
                self.strm_run = 0

    @always_comb
    def st_dma_start_pulse_logic(self):
        if self.cfg_st_dma_ctrl_mode == 0:
            self.st_dma_start_pulse_next = 0
        elif self.cfg_st_dma_ctrl_mode == 1:
            self.st_dma_start_pulse_next = (~self.strm_run) & self.st_dma_start_pulse
        elif (self.cfg_st_dma_ctrl_mode == 2) | (self.cfg_st_dma_ctrl_mode == 3):
            self.st_dma_start_pulse_next = (((~self.strm_run) & self.st_dma_start_pulse)
                                            | ((self.st_dma_done_pulse)
                                               & ((self.repeat_cnt + 1) < self.cfg_st_dma_num_repeat)))
        else:
            self.st_dma_start_pulse_next = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def st_dma_start_pulse_ff(self):
        if self.reset:
            self.st_dma_start_pulse_r = 0
        else:
            if self.st_dma_start_pulse_r:
                self.st_dma_start_pulse_r = 0
            else:
                self.st_dma_start_pulse_r = self.st_dma_start_pulse_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def cycle_counter(self):
        if self.reset:
            self.cycle_count = 0
        else:
            if self.st_dma_start_pulse_r:
                self.cycle_count = 0
            elif self.loop_done:
                self.cycle_count = 0
            elif self.strm_run:
                self.cycle_count = self.cycle_count + 1

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def data_f2g_ff(self):
        if self.reset:
            self.data_f2g_r = 0
            self.data_valid_f2g_r = 0
        else:
            for i in range(self._params.cgra_per_glb):
                self.data_f2g_r[i] = self.data_f2g[i]
                self.data_valid_f2g_r[i] = self.data_valid_f2g[i]

    @always_comb
    def data_f2g_logic(self):
        self.strm_data = 0
        self.strm_data_valid = 0
        for i in range(self._params.cgra_per_glb):
            if self.cfg_data_network_f2g_mux[i] == 1:
                self.strm_data = self.data_f2g_r[i]
                self.strm_data_valid = self.data_valid_f2g_r[i]
            else:
                self.strm_data = self.strm_data
                self.strm_data_valid = self.strm_data_valid

    @always_comb
    def cycle_valid_comb(self):
        if self.cfg_st_dma_ctrl_use_valid:
            self.cycle_valid_muxed = self.strm_data_valid
        else:
            self.cycle_valid_muxed = self.cycle_valid

    @always_comb
    def strm_wr_packet_comb(self):
        self.strm_wr_en_w = self.cycle_valid_muxed
        self.strm_wr_addr_w = resize(self.data_current_addr, self._params.glb_addr_width)
        self.strm_wr_data_w = self.strm_data

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def last_strm_wr_addr_ff(self):
        if self.reset:
            self.last_strm_wr_addr_r = 0
        else:
            if self.strm_wr_en_w:
                self.last_strm_wr_addr_r = self.strm_wr_addr_w

    @always_comb
    def strm_data_sel_comb(self):
        self.strm_data_sel = self.strm_wr_addr_w[self._params.bank_byte_offset - 1, self._params.cgra_byte_offset]

    @always_comb
    def bank_wr_packet_cache_comb(self):
        self.bank_wr_strb_cache_w = self.bank_wr_strb_cache_r
        self.bank_wr_data_cache_w = self.bank_wr_data_cache_r
        # First, if cached data is written to memory, clear it.
        if self.bank_wr_en:
            self.bank_wr_strb_cache_w = 0
            self.bank_wr_data_cache_w = 0
        # Next, save data to cache
        if self.strm_wr_en_w:
            if self.strm_data_sel == 0:
                self.bank_wr_strb_cache_w[self.cgra_strb_width - 1,
                                          0] = const(self.cgra_strb_value, self.cgra_strb_width)
                self.bank_wr_data_cache_w[self._params.cgra_data_width - 1, 0] = self.strm_wr_data_w
            elif self.strm_data_sel == 1:
                self.bank_wr_strb_cache_w[self.cgra_strb_width * 2 - 1,
                                          self.cgra_strb_width] = const(self.cgra_strb_value,
                                                                        self.cgra_strb_width)
                self.bank_wr_data_cache_w[self._params.cgra_data_width * 2 - 1,
                                          self._params.cgra_data_width] = self.strm_wr_data_w
            elif self.strm_data_sel == 2:
                self.bank_wr_strb_cache_w[self.cgra_strb_width * 3 - 1,
                                          self.cgra_strb_width * 2] = const(self.cgra_strb_value,
                                                                            self.cgra_strb_width)
                self.bank_wr_data_cache_w[self._params.cgra_data_width * 3 - 1,
                                          self._params.cgra_data_width * 2] = self.strm_wr_data_w
            elif self.strm_data_sel == 3:
                self.bank_wr_strb_cache_w[self.cgra_strb_width * 4 - 1,
                                          self.cgra_strb_width * 3] = const(self.cgra_strb_value,
                                                                            self.cgra_strb_width)
                self.bank_wr_data_cache_w[self._params.cgra_data_width * 4 - 1,
                                          self._params.cgra_data_width * 3] = self.strm_wr_data_w
            else:
                self.bank_wr_strb_cache_w = self.bank_wr_strb_cache_r
                self.bank_wr_data_cache_w = self.bank_wr_data_cache_r

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def bank_wr_packet_cache_ff(self):
        if self.reset:
            self.bank_wr_strb_cache_r = 0
            self.bank_wr_data_cache_r = 0
        else:
            self.bank_wr_strb_cache_r = self.bank_wr_strb_cache_w
            self.bank_wr_data_cache_r = self.bank_wr_data_cache_w

    @always_comb
    def bank_wr_packet_logic(self):
        self.bank_addr_match = (self.strm_wr_addr_w[self._params.glb_addr_width - 1, self._params.bank_byte_offset]
                                == self.last_strm_wr_addr_r[self._params.glb_addr_width - 1,
                                                            self._params.bank_byte_offset])
        self.bank_wr_en = ((self.strm_wr_en_w & (~self.bank_addr_match) & (~self.is_first)) | self.is_last)
        self.bank_wr_addr = self.last_strm_wr_addr_r

    @always_comb
    def wr_packet_logic(self):
        if self.cfg_tile_connected_next | self.cfg_tile_connected_prev:
            self.wr_packet_dma2bank_w = 0
            self.wr_packet_dma2ring_w['wr_en'] = self.bank_wr_en
            self.wr_packet_dma2ring_w['wr_strb'] = self.bank_wr_strb_cache_r
            self.wr_packet_dma2ring_w['wr_data'] = self.bank_wr_data_cache_r
            self.wr_packet_dma2ring_w['wr_addr'] = self.bank_wr_addr
        else:
            self.wr_packet_dma2bank_w['wr_en'] = self.bank_wr_en
            self.wr_packet_dma2bank_w['wr_strb'] = self.bank_wr_strb_cache_r
            self.wr_packet_dma2bank_w['wr_data'] = self.bank_wr_data_cache_r
            self.wr_packet_dma2bank_w['wr_addr'] = self.bank_wr_addr
            self.wr_packet_dma2ring_w = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def wr_packet_ff(self):
        if self.reset:
            self.wr_packet_dma2bank = 0
            self.wr_packet_dma2ring = 0
        else:
            self.wr_packet_dma2bank = self.wr_packet_dma2bank_w
            self.wr_packet_dma2ring = self.wr_packet_dma2ring_w

    def add_dma2bank_clk_en(self):
        self.clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_wr_delay + self._params.wr_clk_en_margin)
        self.dma2bank_clk_en = self.var("dma2bank_clk_en", 1)
        self.add_child("dma2bank_clk_en_gen",
                       self.clk_en_gen,
                       clk=self.clk,
                       reset=self.reset,
                       enable=self.wr_packet_dma2bank_w['wr_en'],
                       clk_en=self.dma2bank_clk_en
                       )
        self.wire(self.clk_en_dma2bank, self.dma2bank_clk_en)

    @always_comb
    def strm_done_pulse_logic(self):
        self.done_pulse_w = self.loop_done & self.strm_run

    def add_done_pulse_pipeline(self):
        maximum_latency = (2 * self._params.num_glb_tiles + self._params.tile2sram_wr_delay
                           + self._params.chain_latency_overhead)
        latency_width = clog2(maximum_latency)
        self.done_pulse_d_arr = self.var(
            "done_pulse_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.done_pulse_pipeline = Pipeline(width=1,
                                            depth=maximum_latency,
                                            flatten_output=True)
        self.add_child("done_pulse_pipeline",
                       self.done_pulse_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.done_pulse_w,
                       out_=self.done_pulse_d_arr)

        self.wire(self.st_dma_done_pulse,
                  self.done_pulse_d_arr[(resize(self.cfg_data_network_latency, latency_width)
                                         + self._params.tile2sram_wr_delay)])

    def add_done_pulse_last_pipeline(self):
        self.interrupt_last_pipeline = Pipeline(width=1, depth=self._params.interrupt_cnt)
        self.add_child("st_dma_interrupt_pipeline",
                       self.interrupt_last_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.st_dma_done_pulse,
                       out_=self.st_dma_done_pulse_last)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def interrupt_ff(self):
        if self.reset:
            self.st_dma_done_interrupt = 0
        else:
            if self.st_dma_done_pulse:
                self.st_dma_done_interrupt = 1
            elif self.st_dma_done_pulse_last:
                self.st_dma_done_interrupt = 0
