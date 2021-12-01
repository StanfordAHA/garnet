from kratos import Generator, always_ff, always_comb, posedge, concat, const, resize, ext, clog2
from global_buffer.design.glb_loop_iter import GlbLoopIter
from global_buffer.design.glb_sched_gen import GlbSchedGen
from global_buffer.design.glb_addr_gen import GlbAddrGen
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
import math


class GlbCoreStoreDma(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_core_store_dma")
        self._params = _params
        self.header = GlbHeader(self._params)
        assert self._params.bank_data_width == self._params.cgra_data_width * 4

        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")

        self.data_f2g = self.input(
            "data_f2g", width=self._params.cgra_data_width)
        self.data_valid_f2g = self.input("data_valid_f2g", width=1)

        self.wr_packet = self.output(
            "wr_packet", self.header.wr_packet_t)

        self.cfg_st_dma_num_repeat = self.input("cfg_st_dma_num_repeat", max(1, clog2(self._params.queue_depth)))
        self.cfg_st_dma_ctrl_mode = self.input("cfg_st_dma_ctrl_mode", 2)
        self.cfg_st_dma_ctrl_use_valid = self.input("cfg_st_dma_ctrl_use_valid", 1)
        self.cfg_data_network_latency = self.input(
            "cfg_data_network_latency", self._params.latency_width)
        self.cfg_st_dma_header = self.input(
            "cfg_st_dma_header", self.header.cfg_st_dma_header_t, size=self._params.queue_depth)

        self.st_dma_start_pulse = self.input("st_dma_start_pulse", 1)
        self.st_dma_done_pulse = self.output("st_dma_done_pulse", 1)

        # localparam
        self.default_latency = (self._params.glb_bank_memory_pipeline_depth
                                + self._params.sram_gen_pipeline_depth
                                + self._params.glb_switch_pipeline_depth
                                )
        # local variables
        self.strm_wr_data_w = self.var("strm_wr_data_w", width=self._params.cgra_data_width)
        self.strm_wr_addr_w = self.var("strm_wr_addr_w", width=self._params.glb_addr_width)
        self.strm_wr_en_w = self.var("strm_wr_en_w", width=1)

        self.num_cnt_next = self.var(
            "num_cnt_next", self._params.max_num_words_width)
        self.num_cnt_r = self.var(
            "num_cnt_r", self._params.max_num_words_width)
        self.is_first_word_next = self.var("is_first_word_next", 1)
        self.is_first_word_r = self.var("is_first_word_r", 1)
        self.cur_addr_next = self.var(
            "cur_addr_next", self._params.glb_addr_width)
        self.cur_addr_r = self.var("cur_addr_r", self._params.glb_addr_width)

        self.cache_data_r = self.var(
            "cache_data_r", self._params.bank_data_width)
        self.cache_data_next = self.var(
            "cache_data_next", self._params.bank_data_width)
        self.cache_strb_r = self.var(
            "cache_strb_r", math.ceil(self._params.bank_data_width / 8))
        self.cache_strb_next = self.var(
            "cache_strb_next", math.ceil(self._params.bank_data_width / 8))

        self.queue_sel_r = self.var("queue_sel_r", max(clog2(self._params.queue_depth), 1))
        self.queue_sel_w = self.var("queue_sel_w", max(clog2(self._params.queue_depth), 1))

        self.strm_done = self.var("strm_done", 1)
        self.strm_done_d1 = self.var("strm_done_d1", 1)
        self.done_pulse_w = self.var("done_pulse_w", 1)

        self.state_e = self.enum("state_e", {
            "off": 0, "idle": 1, "ready": 2, "acc1": 3, "acc2": 4, "acc3": 5, "acc4": 6, "done": 7})
        self.state_r = self.var("state_r", self.state_e)
        self.state_next = self.var("state_next", self.state_e)

        self.strm_run = self.var("strm_run", 1)
        self.loop_done = self.var("loop_done", 1)
        self.cycle_valid = self.var("cycle_valid", 1)
        self.cycle_valid_muxed = self.var("cycle_valid_muxed", 1)
        self.cycle_count = self.var("cycle_count", self._params.axi_data_width)
        self.cycle_current_addr = self.var("cycle_current_addr", self._params.axi_data_width)
        self.data_current_addr = self.var("data_current_addr", self._params.axi_data_width)
        self.loop_mux_sel = self.var("loop_mux_sel", clog2(self._params.loop_level))
        self.queue_sel_r = self.var("queue_sel_r", max(1, clog2(self._params.queue_depth)))
        self.repeat_cnt = self.var("repeat_cnt", max(1, clog2(self._params.queue_depth)))

        self.add_done_pulse_pipeline()
        self.add_always(self.data_f2g_pipeline)
        self.add_always(self.dma_validate_ff)
        self.add_always(self.dma_validate_pulse_gen)
        self.add_always(self.dma_invalidate_pulse_gen)
        self.add_always(self.assign_st_dma_header_hwclr)
        self.add_always(self.dma_header_ff)
        self.add_always(self.state_fsm_logic)
        self.add_always(self.state_fsm_ff)
        self.add_always(self.cache_ff)
        self.add_always(self.counter_ff)
        self.add_always(self.queue_sel_ff)
        self.add_always(self.queue_sel_logic)
        self.add_always(self.wr_packet_logic)
        self.add_always(self.strm_done_logic)
        self.add_always(self.strm_done_pipeline)
        self.add_always(self.strm_done_pulse_logic)

        # Loop iteration shared for cycle and data
        self.loop_iter = GlbLoopIter(self._params)
        self.add_child("loop_iter",
                       self.loop_iter,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       step=self.cycle_valid_muxed,
                       mux_sel_out=self.loop_mux_sel,
                       restart=self.loop_done)
        self.wire(self.loop_iter.dim, self.cfg_st_dma_header[self.queue_sel_r][f"dim"])
        for i in range(self._params.loop_level):
            self.wire(self.loop_iter.ranges[i], self.cfg_st_dma_header[self.queue_sel_r][f"range_{i}"])

        # Cycle stride
        self.cycle_stride_sched_gen = GlbSchedGen(self._params)
        self.add_child("cycle_stride_sched_gen",
                       self.cycle_stride_sched_gen,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       restart=self.st_dma_start_pulse_r,
                       cycle_count=self.cycle_count,
                       current_addr=self.cycle_current_addr,
                       finished=self.loop_done,
                       valid_output=self.cycle_valid)

        self.cycle_stride_addr_gen = GlbAddrGen(self._params)
        self.add_child("cycle_stride_addr_gen",
                       self.cycle_stride_addr_gen,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       restart=self.st_dma_start_pulse_r,
                       step=self.cycle_valid_muxed,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.cycle_current_addr)
        self.wire(self.cycle_stride_addr_gen.start_addr, ext(
            self.cfg_st_dma_header[self.queue_sel_r][f"cycle_start_addr"], self._params.axi_data_width))
        for i in range(self._params.loop_level):
            self.wire(self.cycle_stride_addr_gen.strides[i],
                      self.cfg_st_dma_header[self.queue_sel_r][f"cycle_stride_{i}"])

        # Data stride
        self.data_stride_addr_gen = GlbAddrGen(self._params)
        self.add_child("data_stride_addr_gen",
                       self.data_stride_addr_gen,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       restart=self.st_dma_start_pulse_r,
                       step=self.cycle_valid_muxed,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.data_current_addr)
        self.wire(self.data_stride_addr_gen.start_addr, ext(
            self.cfg_st_dma_header[self.queue_sel_r][f"start_addr"], self._params.axi_data_width))
        for i in range(self._params.loop_level):
            self.wire(self.data_stride_addr_gen.strides[i], self.cfg_st_dma_header[self.queue_sel_r][f"stride_{i}"])

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def queue_sel_ff(self):
        if self.reset:
            self.queue_sel_r = 0
            self.repeat_cnt = 0
        elif self.clk_en:
            if self.cfg_st_dma_ctrl_mode == 2:
                if self.st_dma_done_pulse:
                    if (self.repeat_cnt + 1) < self.cfg_st_dma_num_repeat:
                        self.repeat_cnt += 1
            elif self.cfg_st_dma_ctrl_mode == 3:
                if self.st_dma_done_pulse:
                    if (self.repeat_cnt + 1) < self.cfg_st_dma_num_repeat:
                        self.queue_sel_r = self.queue_sel_r + 1
                        self.repeat_cnt += 1
            else:
                self.queue_sel_r = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def is_last_ff(self):
        if self.reset:
            self.is_last = 0
        elif self.clk_en:
            if self.loop_done:
                self.is_last = 1
            elif self.bank_wr_en:
                self.is_last = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def strm_run_ff(self):
        if self.reset:
            self.strm_run = 0
        elif self.clk_en:
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
        elif self.clk_en:
            if self.st_dma_start_pulse_r:
                self.st_dma_start_pulse_r = 0
            else:
                self.st_dma_start_pulse_r = self.st_dma_start_pulse_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def cycle_counter(self):
        if self.reset:
            self.cycle_count = 0
        elif self.clk_en:
            if self.st_dma_start_pulse_r:
                self.cycle_count = 0
            elif self.loop_done:
                self.cycle_count = 0
            elif self.strm_run:
                self.cycle_count = self.cycle_count + 1

    @always_comb
    def cycle_valid_comb(self):
        if self.cfg_st_dma_ctrl_use_valid:
            self.cycle_valid_muxed = self.data_valid_f2g
        else:
            self.cycle_valid_muxed = self.cycle_valid

    # FIXME: Check if cycle_valid meets the timing with ld_dma.
    @always_comb
    def strm_wr_packet_comb(self):
        self.strm_wr_en_w = self.cycle_valid_muxed
        self.strm_wr_addr_w = resize(self.data_current_addr,
                                     self._params.glb_addr_width) << self._params.cgra_byte_offset
        self.strm_wr_data_w = self.data_f2g

    # @always_comb
    # def state_fsm_logic(self):
    #     self.cache_data_next = self.cache_data_r
    #     self.cache_strb_next = self.cache_strb_r
    #     self.num_cnt_next = self.num_cnt_r
    #     self.cur_addr_next = self.cur_addr_r
    #     self.state_next = self.state_r
    #     self.is_first_word_next = self.is_first_word_r
    #     if self.state_r == self.state_e.off:
    #         if self.cfg_st_dma_ctrl_mode != 0:
    #             self.state_next = self.state_e.idle
    #     elif self.state_r == self.state_e.idle:
    #         self.num_cnt_next = 0
    #         self.cur_addr_next = 0
    #         if ((self.dma_header_r[self.queue_sel_w]['validate'] == 1)
    #                 & (self.dma_header_r[self.queue_sel_w]['num_words'] != 0)):
    #             self.cur_addr_next = self.dma_header_r[self.queue_sel_w]['start_addr']
    #             self.num_cnt_next = self.dma_header_r[self.queue_sel_w]['num_words']
    #             self.is_first_word_next = 1
    #             if self.cur_addr_next[2, 1] == 0b00:
    #                 self.state_next = self.state_e.ready
    #             elif self.cur_addr_next[2, 1] == 0b01:
    #                 self.state_next = self.state_e.acc1
    #             elif self.cur_addr_next[2, 1] == 0b10:
    #                 self.state_next = self.state_e.acc2
    #             elif self.cur_addr_next[2, 1] == 0b11:
    #                 self.state_next = self.state_e.acc3
    #             else:
    #                 self.state_next = self.state_e.ready
    #     elif self.state_r == self.state_e.ready:
    #         if self.num_cnt_r == 0:
    #             self.state_next = self.state_e.done
    #         elif self.strm_wr_en_r == 1:
    #             self.is_first_word_next = 0
    #             self.cache_data_next[self._params.cgra_data_width
    #                                  - 1, 0] = self.strm_wr_data_r
    #             self.cache_strb_next[1, 0] = 0b11
    #             self.num_cnt_next = self.num_cnt_r - 1
    #             if ~self.is_first_word_r:
    #                 self.cur_addr_next = self.cur_addr_r + \
    #                     (self._params.cgra_data_width // 8)
    #             self.state_next = self.state_e.acc1
    #     elif self.state_r == self.state_e.acc1:
    #         if self.num_cnt_r == 0:
    #             self.state_next = self.state_e.done
    #         elif self.strm_wr_en_r == 1:
    #             self.is_first_word_next = 0
    #             self.cache_data_next[self._params.cgra_data_width * 2 - 1,
    #                                  self._params.cgra_data_width] = self.strm_wr_data_r
    #             self.cache_strb_next[3, 2] = 0b11
    #             self.num_cnt_next = self.num_cnt_r - 1
    #             if ~self.is_first_word_r:
    #                 self.cur_addr_next = self.cur_addr_r + \
    #                     (self._params.cgra_data_width // 8)
    #             self.state_next = self.state_e.acc2
    #     elif self.state_r == self.state_e.acc2:
    #         if self.num_cnt_r == 0:
    #             self.state_next = self.state_e.done
    #         elif self.strm_wr_en_r == 1:
    #             self.is_first_word_next = 0
    #             self.cache_data_next[self._params.cgra_data_width * 3 - 1,
    #                                  self._params.cgra_data_width * 2] = self.strm_wr_data_r
    #             self.cache_strb_next[5, 4] = 0b11
    #             self.num_cnt_next = self.num_cnt_r - 1
    #             if ~self.is_first_word_r:
    #                 self.cur_addr_next = self.cur_addr_r + \
    #                     (self._params.cgra_data_width // 8)
    #             self.state_next = self.state_e.acc3
    #     elif self.state_r == self.state_e.acc3:
    #         if self.num_cnt_r == 0:
    #             self.state_next = self.state_e.done
    #         elif self.strm_wr_en_r == 1:
    #             self.is_first_word_next = 0
    #             self.cache_data_next[self._params.cgra_data_width * 4 - 1,
    #                                  self._params.cgra_data_width * 3] = self.strm_wr_data_r
    #             self.cache_strb_next[7, 6] = 0b11
    #             self.num_cnt_next = self.num_cnt_r - 1
    #             if ~self.is_first_word_r:
    #                 self.cur_addr_next = self.cur_addr_r + \
    #                     (self._params.cgra_data_width // 8)
    #             self.state_next = self.state_e.acc4
    #     elif self.state_r == self.state_e.acc4:
    #         if self.num_cnt_r == 0:
    #             self.state_next = self.state_e.done
    #         elif self.strm_wr_en_r == 1:
    #             self.is_first_word_next = 0
    #             self.cache_data_next = ext(self.strm_wr_data_r, self._params.bank_data_width)
    #             self.cache_strb_next = concat(const(0, 6), const(0b11, 2))
    #             self.num_cnt_next = self.num_cnt_r - 1
    #             if ~self.is_first_word_r:
    #                 self.cur_addr_next = self.cur_addr_r + \
    #                     (self._params.cgra_data_width // 8)
    #             self.state_next = self.state_e.acc1
    #         else:
    #             self.cache_data_next = 0
    #             self.cache_strb_next = 0
    #             self.state_next = self.state_e.ready
    #     elif self.state_r == self.state_e.done:
    #         self.cache_data_next = 0
    #         self.cache_strb_next = 0
    #         self.num_cnt_next = 0
    #         self.state_next = self.state_e.idle
    #     else:
    #         self.cache_data_next = self.cache_data_r
    #         self.cache_strb_next = self.cache_strb_r
    #         self.num_cnt_next = self.num_cnt_r
    #         self.state_next = self.state_e.idle

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def last_strm_wr_addr_ff(self):
        if self.reset:
            self.last_strm_wr_addr_r = 0
        elif self.clk_en:
            if self.strm_wr_en_w:
                self.last_strm_wr_addr_r = self.strm_wr_addr_w

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def bank_wr_packet_cache_ff(self):
        if self.reset:
            self.bank_wr_strb_cache_r = 0
            self.bank_wr_data_cache_r = 0
        elif self.clk_en:
            if self.strm_wr_en_w:
                if self.strm_data_sel == 0:
                    self.bank_wr_strb_cache_r[] = 0
                    self.bank_wr_data_cache_r[] = 0

    @always_comb
    def bank_wr_packet_logic(self):
        self.bank_addr_match = (self.strm_wr_addr_w[self._params.glb_addr_width - 1, self._params.bank_byte_offset]
                                == self.last_strm_wr_addr_r[self._params.glb_addr_width - 1,
                                                            self._params.bank_byte_offset])
        self.bank_wr_en = ((self.strm_wr_en_w & (~self.bank_addr_match)) | self.is_last)
        self.bank_wr_addr = self.last_strm_wr_addr_r

    @always_comb
    def wr_packet_logic(self):
        if self.state_r == self.state_e.done:
            self.wr_packet['wr_en'] = 1
            self.wr_packet['wr_strb'] = self.cache_strb_r
            self.wr_packet['wr_data'] = self.cache_data_r
            self.wr_packet['wr_addr'] = self.cur_addr_r
        elif (self.state_r == self.state_e.acc4) & (self.num_cnt_r != 0):
            self.wr_packet['wr_en'] = 1
            self.wr_packet['wr_strb'] = self.cache_strb_r
            self.wr_packet['wr_data'] = self.cache_data_r
            self.wr_packet['wr_addr'] = concat(self.cur_addr_r[self._params.glb_addr_width - 1,
                                                               self._params.bank_byte_offset],
                                               const(0, self._params.bank_byte_offset))
        else:
            self.wr_packet['wr_en'] = 0
            self.wr_packet['wr_strb'] = 0
            self.wr_packet['wr_data'] = 0
            self.wr_packet['wr_addr'] = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def cache_ff(self):
        if self.reset:
            self.cache_data_r = 0
            self.cache_strb_r = 0
        elif self.clk_en:
            self.cache_data_r = self.cache_data_next
            self.cache_strb_r = self.cache_strb_next

    @always_comb
    def strm_done_logic(self):
        self.strm_done = (self.state_r == self.state_e.done)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def strm_done_pipeline(self):
        if self.reset:
            self.strm_done_d1 = 0
        elif self.clk_en:
            self.strm_done_d1 = self.strm_done

    @always_comb
    def strm_done_pulse_logic(self):
        self.done_pulse_w = self.loop_done & self.strm_run

    def add_done_pulse_pipeline(self):
        maximum_latency = 2 * self._params.num_glb_tiles + self.default_latency
        latency_width = clog2(maximum_latency)
        self.done_pulse_d_arr = self.var(
            "done_pulse_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.done_pulse_pipeline = Pipeline(width=1,
                                            depth=maximum_latency,
                                            flatten_output=True)
        self.add_child("done_pulse_pipeline",
                       self.done_pulse_pipeline,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       in_=self.done_pulse_w,
                       out_=self.done_pulse_d_arr)

        self.wire(self.st_dma_done_pulse,
                  self.done_pulse_d_arr[resize(self.cfg_data_network_latency, latency_width) + self.default_latency])
