from kratos import Generator, always_ff, always_comb, posedge, resize, clog2, ext, const, clock_en
from global_buffer.design.glb_loop_iter import GlbLoopIter
from global_buffer.design.glb_sched_gen import GlbSchedGen
from global_buffer.design.glb_addr_gen import GlbAddrGen
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen
from global_buffer.design.fifo import FIFO


class GlbLoadDma(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_load_dma")
        self._params = _params
        self.header = GlbHeader(self._params)
        assert self._params.bank_data_width == self._params.cgra_data_width * 4
        assert self._params.tile2sram_rd_delay >= self._params.flush_crossbar_pipeline_depth

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.data_g2f = self.output("data_g2f", width=self._params.cgra_data_width,
                                    size=self._params.cgra_per_glb, packed=True)
        self.data_g2f_vld = self.output("data_g2f_vld", 1, size=self._params.cgra_per_glb, packed=True)
        self.data_g2f_rdy = self.input("data_g2f_rdy", 1, size=self._params.cgra_per_glb, packed=True)

        self.ctrl_g2f = self.output("ctrl_g2f", 1, size=self._params.cgra_per_glb, packed=True)

        self.data_flush = self.output("data_flush", 1)

        self.rdrq_packet_dma2bank = self.output("rdrq_packet_dma2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2ring = self.output("rdrq_packet_dma2ring", self.header.rdrq_packet_t)
        self.rdrs_packet_bank2dma = self.input("rdrs_packet_bank2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_ring2dma = self.input("rdrs_packet_ring2dma", self.header.rdrs_packet_t)

        self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
        self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)
        self.cfg_ld_dma_num_repeat = self.input("cfg_ld_dma_num_repeat", clog2(self._params.queue_depth) + 1)
        self.cfg_ld_dma_ctrl_valid_mode = self.input("cfg_ld_dma_ctrl_valid_mode", 2)
        self.cfg_ld_dma_ctrl_flush_mode = self.input("cfg_ld_dma_ctrl_flush_mode", 1)
        self.cfg_ld_dma_ctrl_mode = self.input("cfg_ld_dma_ctrl_mode", 2)
        self.cfg_data_network_latency = self.input("cfg_data_network_latency", self._params.latency_width)
        self.cfg_ld_dma_header = self.input(
            "cfg_ld_dma_header", self.header.cfg_load_dma_header_t, size=self._params.queue_depth)
        self.cfg_data_network_g2f_mux = self.input("cfg_data_network_g2f_mux", self._params.cgra_per_glb)

        self.clk_en_dma2bank = self.output("clk_en_dma2bank", 1)
        self.ld_dma_start_pulse = self.input("ld_dma_start_pulse", 1)
        self.ld_dma_done_interrupt = self.output("ld_dma_done_interrupt", 1)

        # local variables
        self.data_flush_w = self.var("data_flush_w", 1)
        self.rdrq_packet_dma2bank_w = self.var("rdrq_packet_dma2bank_w", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2ring_w = self.var("rdrq_packet_dma2ring_w", self.header.rdrq_packet_t)
        self.rdrs_packet = self.var("rdrs_packet", self.header.rdrs_packet_t)
        self.data_g2f_w = self.var("data_g2f_w", width=self._params.cgra_data_width,
                                   size=self._params.cgra_per_glb, packed=True)
        self.data_g2f_vld_w = self.var("data_g2f_vld_w", 1, size=self._params.cgra_per_glb, packed=True)
        self.ctrl_g2f_w = self.var("ctrl_g2f_w", 1, size=self._params.cgra_per_glb, packed=True)

        self.ld_dma_done_pulse = self.var("ld_dma_done_pulse", 1)
        self.ld_dma_done_pulse_latch = self.var("ld_dma_done_pulse_latch", 1)
        self.ld_dma_done_pulse_anded = self.var("ld_dma_done_pulse_anded", 1)
        self.ld_dma_done_pulse_last = self.var("ld_dma_done_pulse_last", 1)
        self.ld_dma_done_pulse_pipeline_out = self.var("ld_dma_done_pulse_pipeline_out", 1)
        self.strm_data = self.var("strm_data", self._params.cgra_data_width)
        self.strm_data_valid = self.var("strm_data_valid", 1)
        self.strm_ctrl_muxed = self.var("strm_ctrl_muxed", 1)
        self.strm_data_sel_w = self.var(
            "strm_data_sel_w", self._params.bank_byte_offset - self._params.cgra_byte_offset)
        self.strm_data_sel = self.var("strm_data_sel", self._params.bank_byte_offset - self._params.cgra_byte_offset)

        self.strm_rd_en_w = self.var("strm_rd_en_w", 1)
        self.strm_rd_addr_w = self.var("strm_rd_addr_w", self._params.glb_addr_width)
        self.last_strm_rd_addr_r = self.var("last_strm_rd_addr_r", self._params.glb_addr_width)

        self.ld_dma_start_pulse_next = self.var("ld_dma_start_pulse_next", 1)
        self.ld_dma_start_pulse_r = self.var("ld_dma_start_pulse_r", 1)
        self.is_first = self.var("is_first", 1)

        self.ld_dma_done_pulse_w = self.var("ld_dma_done_pulse_w", 1)

        self.is_cached = self.var("is_cached", 1)
        self.bank_rdrq_rd_en = self.var("bank_rdrq_rd_en", 1)
        self.bank_rdrq_rd_addr = self.var("bank_rdrq_rd_addr", self._params.glb_addr_width)
        self.bank_rdrs_data_cache_r = self.var("bank_rdrs_data_cache_r", self._params.bank_data_width)

        self.strm_run = self.var("strm_run", 1)
        self.loop_done = self.var("loop_done", 1)
        self.cycle_valid = self.var("cycle_valid", 1)
        self.cycle_count = self.var("cycle_count", self._params.cycle_count_width)
        self.cycle_current_addr = self.var("cycle_current_addr", self._params.cycle_count_width)
        self.data_current_addr = self.var("data_current_addr", self._params.glb_addr_width + 1)
        self.loop_mux_sel = self.var("loop_mux_sel", clog2(self._params.load_dma_loop_level))
        self.repeat_cnt = self.var("repeat_cnt", clog2(self._params.queue_depth) + 1)

        if self._params.queue_depth != 1:
            self.queue_sel_r = self.var("queue_sel_r", max(1, clog2(self.repeat_cnt.width)))

        # ready_valid controller
        self.cycle_counter_en = self.var("cycle_counter_en", 1)
        self.iter_step_valid = self.var("iter_step_valid", 1)
        self.fifo_push_ready = self.var("fifo_push_ready", 1)
        self.data_dma2fifo = self.var("data_dma2fifo", self._params.cgra_data_width)
        self.data_fifo2cgra = self.var("data_fifo2cgra", self._params.cgra_data_width)
        self.fifo_push = self.var("fifo_push", 1)
        self.fifo_pop = self.var("fifo_pop", 1)
        self.fifo_full = self.var("fifo_full", 1)
        self.fifo_empty = self.var("fifo_empty", 1)
        self.fifo_almost_full = self.var("fifo_almost_full", 1)
        self.fifo_almost_empty = self.var("fifo_almost_empty", 1)
        self.fifo_depth = self._params.max_num_chain * 2 + self._params.tile2sram_rd_delay

        self.data_g2f_rdy_muxed = self.var("data_g2f_rdy_muxed", 1, size=self._params.cgra_per_glb, packed=True)
        self.fifo2skid_rdy = self.var("fifo2skid_rdy", 1, size=self._params.cgra_per_glb, packed=True)
        self.fifo2skid_rdy_muxed = self.var("fifo2skid_rdy_muxed", 1)
        self.fifo2skid_vld = self.var("fifo2skid_vld", 1, size=self._params.cgra_per_glb, packed=True)
        self.fifo2skid_vld_muxed = self.var("fifo2skid_vld_muxed", 1)
        self.skid_in = self.var("skid_in", self._params.cgra_data_width, size=self._params.cgra_per_glb, packed=True)
        self.skid_out = self.var("skid_out", self._params.cgra_data_width, size=self._params.cgra_per_glb, packed=True)
        self.skid_push = self.var("skid_push", 1, size=self._params.cgra_per_glb, packed=True)
        self.skid_pop = self.var("skid_pop", 1, size=self._params.cgra_per_glb, packed=True)
        self.skid_full = self.var("skid_full", 1, size=self._params.cgra_per_glb, packed=True)
        self.skid_empty = self.var("skid_empty", 1, size=self._params.cgra_per_glb, packed=True)
        self.all_skid_empty = self.var("all_skid_empty", 1)

        self.add_fifo()
        self.add_skid()
        self.add_always(self.fifo_to_skid)
        self.add_always(self.data_g2f_rdy_muxed_logic)
        self.add_always(self.all_skid_empty_logic)

        # Current dma header
        self.current_dma_header = self.var("current_dma_header", self.header.cfg_load_dma_header_t)
        if self._params.queue_depth == 1:
            self.wire(self.cfg_ld_dma_header, self.current_dma_header)
        else:
            self.wire(self.cfg_ld_dma_header[self.queue_sel_r], self.current_dma_header)

        if self._params.queue_depth != 1:
            self.add_always(self.queue_sel_ff)

        self.add_always(self.iter_step_logic)
        self.add_always(self.repeat_cnt_ff)
        self.add_always(self.cycle_counter)
        self.add_always(self.is_first_ff)
        self.add_always(self.strm_run_ff)
        self.add_strm_data_start_pulse_pipeline()
        self.add_strm_rd_en_pipeline()
        self.add_strm_data_sel_pipeline()
        self.add_always(self.ld_dma_start_pulse_logic)
        self.add_always(self.ld_dma_start_pulse_ff)
        self.add_always(self.strm_data_flush_mux)
        self.add_always(self.ctrl_mux)
        self.add_always(self.ld_dma_done_pulse_logic)
        self.add_always(self.strm_rdrq_packet_logic)
        self.add_always(self.last_strm_rd_addr_ff)
        self.add_always(self.rdrq_packet_logic)
        self.add_always(self.rdrq_packet_ff)
        self.add_always(self.bank_rdrq_packet_logic)
        self.add_always(self.rdrs_packet_logic)
        self.add_always(self.bank_rdrs_data_cache_ff)
        self.add_always(self.strm_data_logic)
        self.add_always(self.done_pulse_ctrl)
        self.add_always(self.done_pulse_muxed)
        self.add_always(self.done_pulse_anded_comb)
        self.add_ld_dma_done_pulse_pipeline()
        self.add_done_pulse_last_pipeline()
        self.add_always(self.interrupt_ff)
        self.add_dma2bank_clk_en()
        self.add_pipeline_ctrl()
        self.add_pipeline_flush()

        # Loop iteration shared for cycle and data
        self.loop_iter = GlbLoopIter(self._params, loop_level=self._params.load_dma_loop_level)
        self.add_child("loop_iter",
                       self.loop_iter,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       step=self.iter_step_valid,
                       mux_sel_out=self.loop_mux_sel,
                       restart=self.loop_done)
        self.wire(self.loop_iter.dim, self.current_dma_header[f"dim"])
        for i in range(self._params.load_dma_loop_level):
            self.wire(self.loop_iter.ranges[i], self.current_dma_header[f"range_{i}"])

        # Cycle stride
        self.wire(self.cycle_counter_en, self.cfg_ld_dma_ctrl_valid_mode != self._params.ld_dma_valid_mode_ready_valid)
        self.cycle_stride_sched_gen = GlbSchedGen(self._params)
        self.add_child("cycle_stride_sched_gen",
                       self.cycle_stride_sched_gen,
                       clk=self.clk,
                       clk_en=clock_en(self.cycle_counter_en),
                       reset=self.reset,
                       restart=self.ld_dma_start_pulse_r,
                       cycle_count=self.cycle_count,
                       current_addr=self.cycle_current_addr,
                       finished=self.loop_done,
                       valid_output=self.cycle_valid)

        self.cycle_stride_addr_gen = GlbAddrGen(self._params, loop_level=self._params.load_dma_loop_level)
        self.cycle_stride_addr_gen.p_addr_width.value = self._params.cycle_count_width
        self.cycle_stride_addr_gen.p_loop_level.value = self._params.load_dma_loop_level
        self.add_child("cycle_stride_addr_gen",
                       self.cycle_stride_addr_gen,
                       clk=self.clk,
                       clk_en=clock_en(self.cycle_counter_en),
                       reset=self.reset,
                       restart=self.ld_dma_start_pulse_r,
                       step=self.iter_step_valid,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.cycle_current_addr)
        self.wire(self.cycle_stride_addr_gen.start_addr, self.current_dma_header[f"cycle_start_addr"])
        for i in range(self._params.load_dma_loop_level):
            self.wire(self.cycle_stride_addr_gen.strides[i],
                      self.current_dma_header[f"cycle_stride_{i}"])

        # Data stride
        self.data_stride_addr_gen = GlbAddrGen(self._params, loop_level=self._params.load_dma_loop_level)
        self.data_stride_addr_gen.p_addr_width.value = self._params.glb_addr_width + 1
        self.data_stride_addr_gen.p_loop_level.value = self._params.load_dma_loop_level
        self.add_child("data_stride_addr_gen",
                       self.data_stride_addr_gen,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       restart=self.ld_dma_start_pulse_r,
                       step=self.iter_step_valid,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.data_current_addr)
        self.wire(self.data_stride_addr_gen.start_addr, ext(self.current_dma_header[f"start_addr"],
                                                            self._params.glb_addr_width + 1))
        for i in range(self._params.load_dma_loop_level):
            self.wire(self.data_stride_addr_gen.strides[i], self.current_dma_header[f"stride_{i}"])

    # FIFO for ready/valid
    def add_fifo(self):
        self.fifo_almost_full_diff = self.var("fifo_almost_full_diff", clog2(self.fifo_depth))
        self.data_g2f_fifo = FIFO(self._params.cgra_data_width, self.fifo_depth)
        self.add_child("data_g2f_fifo",
                       self.data_g2f_fifo,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       flush=self.ld_dma_start_pulse_r,
                       data_in=self.data_dma2fifo,
                       data_out=self.data_fifo2cgra,
                       push=self.fifo_push,
                       pop=self.fifo_pop,
                       full=self.fifo_full,
                       empty=self.fifo_empty,
                       almost_full=self.fifo_almost_full,
                       almost_full_diff=self.fifo_almost_full_diff,
                       almost_empty_diff=const(2, clog2(self.fifo_depth)))

        self.wire(self.fifo_push_ready, ~self.fifo_almost_full)
        self.wire(self.data_dma2fifo, self.strm_data)
        self.wire(self.fifo_push, ~self.fifo_full & self.strm_data_valid)
        self.wire(self.fifo2skid_vld_muxed, ~self.fifo_empty)
        self.wire(self.fifo_pop, self.fifo2skid_vld_muxed & self.fifo2skid_rdy_muxed)
        self.add_always(self.almost_full_diff_logic)

    @ always_comb
    def fifo_to_skid(self):
        self.fifo2skid_rdy_muxed = 0
        for i in range(self._params.cgra_per_glb):
            if self.cfg_data_network_g2f_mux[i] == 1:
                self.fifo2skid_rdy_muxed = self.fifo2skid_rdy[i]
                self.fifo2skid_vld[i] = self.fifo2skid_vld_muxed
                self.skid_in[i] = self.data_fifo2cgra
            else:
                self.fifo2skid_rdy_muxed = self.fifo2skid_rdy_muxed
                self.fifo2skid_vld[i] = 0
                self.skid_in[i] = 0

    @ always_comb
    def data_g2f_rdy_muxed_logic(self):
        for i in range(self._params.cgra_per_glb):
            if self.cfg_ld_dma_ctrl_valid_mode == self._params.ld_dma_valid_mode_ready_valid:
                self.data_g2f_rdy_muxed[i] = self.data_g2f_rdy[i]
            else:
                self.data_g2f_rdy_muxed[i] = const(1, 1)

    # output fifo
    def add_skid(self):
        self.skid = []
        for i in range(self._params.cgra_per_glb):
            self.skid.append(FIFO(self._params.cgra_data_width, 2))
            self.add_child(f"data_g2f_skid_{i}",
                           self.skid[i],
                           clk=self.clk,
                           clk_en=const(1, 1),
                           reset=self.reset,
                           flush=self.ld_dma_start_pulse_r,
                           data_in=self.skid_in[i],
                           data_out=self.skid_out[i],
                           push=self.skid_push[i],
                           pop=self.skid_pop[i],
                           full=self.skid_full[i],
                           empty=self.skid_empty[i],
                           almost_full_diff=const(0, 1),
                           almost_empty_diff=const(0, 1))

            self.wire(self.skid_out[i], self.data_g2f[i])
            self.wire(self.fifo2skid_rdy[i], ~self.skid_full[i])
            self.wire(self.skid_push[i], self.fifo2skid_rdy[i] & self.fifo2skid_vld[i])

            self.wire(~self.skid_empty[i], self.data_g2f_vld[i])
            self.wire(self.skid_pop[i], ~self.skid_empty[i] & self.data_g2f_rdy_muxed[i])

    @always_comb
    def almost_full_diff_logic(self):
        self.fifo_almost_full_diff = resize(const(self._params.tile2sram_rd_delay + 2,
                                                  clog2(self.fifo_depth))
                                            + self.cfg_data_network_latency, clog2(self.fifo_depth))

    @ always_comb
    def iter_step_logic(self):
        if self.cycle_counter_en:
            self.iter_step_valid = self.cycle_valid
        else:
            self.iter_step_valid = self.strm_run & self.fifo_push_ready

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def queue_sel_ff(self):
        if self.reset:
            self.queue_sel_r = 0
        else:
            if self.cfg_ld_dma_ctrl_mode == 3:
                if self.ld_dma_done_pulse:
                    if (self.repeat_cnt + 1) < self.cfg_ld_dma_num_repeat:
                        self.queue_sel_r = self.queue_sel_r + 1
            else:
                self.queue_sel_r = 0

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def repeat_cnt_ff(self):
        if self.reset:
            self.repeat_cnt = 0
        else:
            if self.cfg_ld_dma_ctrl_mode == 2:
                if self.ld_dma_done_pulse:
                    if (self.repeat_cnt + 1) < self.cfg_ld_dma_num_repeat:
                        self.repeat_cnt += 1
            elif self.cfg_ld_dma_ctrl_mode == 3:
                if self.ld_dma_done_pulse:
                    if (((self.repeat_cnt + 1) < self.cfg_ld_dma_num_repeat)
                            & ((self.repeat_cnt + 1) < self._params.queue_depth)):
                        self.repeat_cnt += 1

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def is_first_ff(self):
        if self.reset:
            self.is_first = 0
        else:
            if self.ld_dma_start_pulse_r:
                self.is_first = 1
            elif self.bank_rdrq_rd_en:
                self.is_first = 0

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def strm_run_ff(self):
        if self.reset:
            self.strm_run = 0
        else:
            if self.ld_dma_start_pulse_r:
                self.strm_run = 1
            elif self.loop_done:
                self.strm_run = 0

    @ always_comb
    def ld_dma_start_pulse_logic(self):
        if self.cfg_ld_dma_ctrl_mode == 0:
            self.ld_dma_start_pulse_next = 0
        elif self.cfg_ld_dma_ctrl_mode == 1:
            self.ld_dma_start_pulse_next = (~self.strm_run) & self.ld_dma_start_pulse
        elif (self.cfg_ld_dma_ctrl_mode == 2) | (self.cfg_ld_dma_ctrl_mode == 3):
            self.ld_dma_start_pulse_next = (((~self.strm_run) & self.ld_dma_start_pulse)
                                            | ((self.ld_dma_done_pulse)
                                               & ((self.repeat_cnt + 1) < self.cfg_ld_dma_num_repeat)))
        else:
            self.ld_dma_start_pulse_next = 0

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def ld_dma_start_pulse_ff(self):
        if self.reset:
            self.ld_dma_start_pulse_r = 0
        else:
            if self.ld_dma_start_pulse_r:
                self.ld_dma_start_pulse_r = 0
            else:
                self.ld_dma_start_pulse_r = self.ld_dma_start_pulse_next

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def cycle_counter(self):
        if self.reset:
            self.cycle_count = 0
        else:
            if self.ld_dma_start_pulse_r:
                self.cycle_count = 0
            elif self.loop_done:
                self.cycle_count = 0
            elif self.cycle_counter_en & self.strm_run:
                self.cycle_count = self.cycle_count + 1

    @ always_comb
    def strm_data_flush_mux(self):
        if self.cfg_ld_dma_ctrl_flush_mode == self._params.ld_dma_flush_mode_external:
            self.data_flush_w = self.strm_data_start_pulse
            if self.cfg_ld_dma_ctrl_valid_mode == self._params.ld_dma_valid_mode_valid:
                self.strm_ctrl_muxed = self.strm_data_valid
            else:
                self.strm_ctrl_muxed = 0
        else:
            self.data_flush_w = 0
            if self.cfg_ld_dma_ctrl_valid_mode == self._params.ld_dma_valid_mode_valid:
                self.strm_ctrl_muxed = self.strm_data_valid
            else:
                self.strm_ctrl_muxed = self.strm_data_start_pulse

    @ always_comb
    def ctrl_mux(self):
        for i in range(self._params.cgra_per_glb):
            if self.cfg_data_network_g2f_mux[i] == 1:
                if self.cfg_ld_dma_ctrl_valid_mode != self._params.ld_dma_valid_mode_ready_valid:
                    self.ctrl_g2f_w[i] = self.strm_ctrl_muxed
                else:
                    self.ctrl_g2f_w[i] = 0
            else:
                self.ctrl_g2f_w[i] = 0

    def add_pipeline_ctrl(self):
        self.pipeline_ctrl_in = self.var("pipeline_ctrl_in", width=self._params.cgra_per_glb)
        self.pipeline_ctrl_out = self.var("pipeline_ctrl_out", width=self._params.cgra_per_glb)
        for i in range(self._params.cgra_per_glb):
            self.wire(self.pipeline_ctrl_in[i], self.ctrl_g2f_w[i])
        self.pipeline_ctrl = Pipeline(width=self._params.cgra_per_glb, depth=2)
        self.add_child("pipeline_ctrl",
                       self.pipeline_ctrl,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.pipeline_ctrl_in,
                       out_=self.pipeline_ctrl_out)

        for i in range(self._params.cgra_per_glb):
            self.wire(self.ctrl_g2f[i], self.pipeline_ctrl_out[i])

    def add_pipeline_flush(self):
        assert self._params.flush_crossbar_pipeline_depth <= 2
        self.pipeline_flush = Pipeline(width=1,
                                       depth=(2 - self._params.flush_crossbar_pipeline_depth))
        self.add_child("pipeline_flush",
                       self.pipeline_flush,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.data_flush_w,
                       out_=self.data_flush)

    @ always_comb
    def ld_dma_done_pulse_logic(self):
        self.ld_dma_done_pulse_w = self.strm_run & self.loop_done

    @ always_comb
    def strm_rdrq_packet_logic(self):
        self.strm_rd_en_w = self.iter_step_valid
        self.strm_rd_addr_w = resize(self.data_current_addr, self._params.glb_addr_width)

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def last_strm_rd_addr_ff(self):
        if self.reset:
            self.last_strm_rd_addr_r = 0
        else:
            if self.strm_rd_en_w:
                self.last_strm_rd_addr_r = self.strm_rd_addr_w

    @ always_comb
    def bank_rdrq_packet_logic(self):
        self.is_cached = (self.strm_rd_addr_w[self._params.glb_addr_width - 1, self._params.bank_byte_offset]
                          == self.last_strm_rd_addr_r[self._params.glb_addr_width - 1,
                                                      self._params.bank_byte_offset])
        self.bank_rdrq_rd_en = self.strm_rd_en_w & (self.is_first | (~self.is_cached))
        self.bank_rdrq_rd_addr = self.strm_rd_addr_w

    @ always_comb
    def rdrq_packet_logic(self):
        if self.cfg_tile_connected_next | self.cfg_tile_connected_prev:
            self.rdrq_packet_dma2bank_w = 0
            self.rdrq_packet_dma2ring_w['rd_en'] = self.bank_rdrq_rd_en
            self.rdrq_packet_dma2ring_w['rd_addr'] = self.bank_rdrq_rd_addr
        else:
            self.rdrq_packet_dma2bank_w['rd_en'] = self.bank_rdrq_rd_en
            self.rdrq_packet_dma2bank_w['rd_addr'] = self.bank_rdrq_rd_addr
            self.rdrq_packet_dma2ring_w = 0

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_packet_ff(self):
        if self.reset:
            self.rdrq_packet_dma2bank = 0
            self.rdrq_packet_dma2ring = 0
        else:
            self.rdrq_packet_dma2bank = self.rdrq_packet_dma2bank_w
            self.rdrq_packet_dma2ring = self.rdrq_packet_dma2ring_w

    def add_dma2bank_clk_en(self):
        self.clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_rd_delay + self._params.rd_clk_en_margin)
        self.clk_en_gen.p_cnt.value = self._params.tile2sram_rd_delay + self._params.rd_clk_en_margin
        self.dma2bank_clk_en = self.var("dma2bank_clk_en", 1)
        self.add_child("dma2bank_clk_en_gen",
                       self.clk_en_gen,
                       clk=self.clk,
                       reset=self.reset,
                       enable=self.rdrq_packet_dma2bank_w['rd_en'],
                       clk_en=self.dma2bank_clk_en
                       )
        self.wire(self.clk_en_dma2bank, self.dma2bank_clk_en)

    @ always_comb
    def rdrs_packet_logic(self):
        if self.cfg_tile_connected_next | self.cfg_tile_connected_prev:
            self.rdrs_packet = self.rdrs_packet_ring2dma
        else:
            self.rdrs_packet = self.rdrs_packet_bank2dma

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def bank_rdrs_data_cache_ff(self):
        if self.reset:
            self.bank_rdrs_data_cache_r = 0
        else:
            if self.rdrs_packet['rd_data_valid']:
                self.bank_rdrs_data_cache_r = self.rdrs_packet['rd_data']

    @ always_comb
    def strm_data_logic(self):
        if self.strm_data_sel == 0:
            self.strm_data = self.bank_rdrs_data_cache_r[self._params.cgra_data_width - 1, 0]
        elif self.strm_data_sel == 1:
            self.strm_data = self.bank_rdrs_data_cache_r[self._params.cgra_data_width * 2 - 1,
                                                         self._params.cgra_data_width * 1]
        elif self.strm_data_sel == 2:
            self.strm_data = self.bank_rdrs_data_cache_r[self._params.cgra_data_width * 3 - 1,
                                                         self._params.cgra_data_width * 2]
        elif self.strm_data_sel == 3:
            self.strm_data = self.bank_rdrs_data_cache_r[self._params.cgra_data_width * 4 - 1,
                                                         self._params.cgra_data_width * 3]
        else:
            self.strm_data = self.bank_rdrs_data_cache_r[self._params.cgra_data_width - 1, 0]

    def add_strm_rd_en_pipeline(self):
        maximum_latency = (2 * self._params.max_num_chain
                           + self._params.chain_latency_overhead + self._params.tile2sram_rd_delay)
        latency_width = clog2(maximum_latency)
        self.strm_rd_en_d_arr = self.var(
            "strm_rd_en_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.strm_rd_en_pipeline = Pipeline(width=1,
                                            depth=maximum_latency,
                                            flatten_output=True)
        self.add_child("strm_rd_en_pipeline",
                       self.strm_rd_en_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.strm_rd_en_w,
                       out_=self.strm_rd_en_d_arr)

        self.wire(self.strm_data_valid, self.strm_rd_en_d_arr[resize(
            self.cfg_data_network_latency, latency_width) + self._params.tile2sram_rd_delay])

    def add_strm_data_sel_pipeline(self):
        maximum_latency = (2 * self._params.max_num_chain
                           + self._params.chain_latency_overhead + self._params.tile2sram_rd_delay)
        latency_width = clog2(maximum_latency)
        self.wire(self.strm_data_sel_w,
                  self.strm_rd_addr_w[self._params.bank_byte_offset - 1, self._params.cgra_byte_offset])
        self.strm_data_sel_arr = self.var("strm_data_sel_arr", width=self._params.bank_byte_offset
                                          - self._params.cgra_byte_offset, size=maximum_latency, explicit_array=True)
        self.strm_data_sel_pipeline = Pipeline(width=self._params.bank_byte_offset - self._params.cgra_byte_offset,
                                               depth=maximum_latency,
                                               flatten_output=True)
        self.add_child("strm_data_sel_pipeline",
                       self.strm_data_sel_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.strm_data_sel_w,
                       out_=self.strm_data_sel_arr)

        self.strm_data_sel = self.strm_data_sel_arr[resize(
            self.cfg_data_network_latency, latency_width) + self._params.tile2sram_rd_delay]

    def add_strm_data_start_pulse_pipeline(self):
        maximum_latency = (2 * self._params.max_num_chain
                           + self._params.chain_latency_overhead + self._params.tile2sram_rd_delay)
        latency_width = clog2(maximum_latency)
        self.strm_data_start_pulse_d_arr = self.var(
            "strm_data_start_pulse_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.strm_data_start_pulse_pipeline = Pipeline(width=1,
                                                       depth=maximum_latency,
                                                       flatten_output=True)
        self.add_child("strm_dma_start_pulse_pipeline",
                       self.strm_data_start_pulse_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.ld_dma_start_pulse_r,
                       out_=self.strm_data_start_pulse_d_arr)
        self.strm_data_start_pulse = self.var("strm_data_start_pulse", 1)
        self.wire(self.strm_data_start_pulse,
                  self.strm_data_start_pulse_d_arr[resize(self.cfg_data_network_latency, latency_width)
                                                   + self._params.tile2sram_rd_delay])

    def add_ld_dma_done_pulse_pipeline(self):
        maximum_latency = (2 * self._params.max_num_chain + self._params.chain_latency_overhead
                           + self._params.tile2sram_rd_delay + 2)
        latency_width = clog2(maximum_latency)
        self.ld_dma_done_pulse_d_arr = self.var(
            "ld_dma_done_pulse_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.ld_dma_done_pulse_pipeline = Pipeline(width=1,
                                                   depth=maximum_latency,
                                                   flatten_output=True)
        self.add_child("ld_dma_done_pulse_pipeline",
                       self.ld_dma_done_pulse_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.ld_dma_done_pulse_w,
                       out_=self.ld_dma_done_pulse_d_arr)
        self.wire(self.ld_dma_done_pulse_pipeline_out,
                  self.ld_dma_done_pulse_d_arr[resize(self.cfg_data_network_latency, latency_width)
                                               + self._params.tile2sram_rd_delay + 2])

    @ always_comb
    def all_skid_empty_logic(self):
        self.all_skid_empty = 1
        for i in range(self._params.cgra_per_glb):
            if self.cfg_data_network_g2f_mux[i]:
                self.all_skid_empty = self.all_skid_empty & self.skid_empty[i]
            else:
                self.all_skid_empty = self.all_skid_empty

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def done_pulse_ctrl(self):
        if self.reset:
            self.ld_dma_done_pulse_latch = 0
        else:
            if self.ld_dma_done_pulse_pipeline_out:
                self.ld_dma_done_pulse_latch = 1
            elif self.ld_dma_done_pulse_latch & self.all_skid_empty:
                self.ld_dma_done_pulse_latch = 0

    @ always_comb
    def done_pulse_anded_comb(self):
        self.ld_dma_done_pulse_anded = self.ld_dma_done_pulse_latch & self.all_skid_empty

    @ always_comb
    def done_pulse_muxed(self):
        if self.cfg_ld_dma_ctrl_valid_mode != self._params.ld_dma_valid_mode_ready_valid:
            self.ld_dma_done_pulse = self.ld_dma_done_pulse_pipeline_out
        else:
            self.ld_dma_done_pulse = self.ld_dma_done_pulse_anded

    def add_done_pulse_last_pipeline(self):
        self.interrupt_last_pipeline = Pipeline(width=1, depth=self._params.interrupt_cnt)
        self.add_child("ld_dma_interrupt_pipeline",
                       self.interrupt_last_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.ld_dma_done_pulse,
                       out_=self.ld_dma_done_pulse_last)

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def interrupt_ff(self):
        if self.reset:
            self.ld_dma_done_interrupt = 0
        else:
            if self.ld_dma_done_pulse:
                self.ld_dma_done_interrupt = 1
            elif self.ld_dma_done_pulse_last:
                self.ld_dma_done_interrupt = 0
