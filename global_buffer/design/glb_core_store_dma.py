from kratos import Generator, always_ff, always_comb, posedge, concat, const
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

        self.cfg_st_dma_ctrl_mode = self.input("cfg_st_dma_ctrl_mode", 2)
        self.cfg_data_network_latency = self.input(
            "cfg_data_network_latency", self._params.latency_width)
        self.cfg_st_dma_header = self.input(
            "cfg_st_dma_header", self.header.cfg_st_dma_header_t, size=self._params.queue_depth)
        self.st_dma_header_clr = self.output(
            "st_dma_header_clr", width=self._params.queue_depth)
        self.st_dma_done_pulse = self.output("st_dma_done_pulse", 1)

        # localparam
        self.default_latency = 3

        # local variables
        self.data_f2g_d1 = self.var(
            "data_f2g_d1", width=self._params.cgra_data_width)
        self.data_valid_f2g_d1 = self.var("data_valid_f2g_d1", width=1)

        self.dma_validate_r = self.var(
            "dma_validate_r", width=self._params.queue_depth)
        self.dma_validate_pulse = self.var(
            "dma_validate_pulse", width=self._params.queue_depth)
        self.dma_invalidate_pulse = self.var(
            "dma_invalidate_pulse", width=self._params.queue_depth)

        self.dma_header_r = self.var(
            "dma_header_r", self.header.cfg_st_dma_header_t, size=self._params.queue_depth)

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

        self.queue_sel_r = self.var("queue_sel_r", math.ceil(
            math.log(self._params.queue_depth, 2)))
        self.queue_sel_w = self.var("queue_sel_w", math.ceil(
            math.log(self._params.queue_depth, 2)))

        self.strm_done = self.var("strm_done", 1)
        self.strm_done_d1 = self.var("strm_done_d1", 1)
        self.done_pulse_w = self.var("done_pulse_w", 1)

        self.state_e = self.enum("state_e", {
            "off": 0, "idle": 1, "ready": 2, "acc1": 3, "acc2": 4, "acc3": 5, "acc4": 6, "done": 7})
        self.state_r = self.var("state_r", self.state_e)
        self.state_next = self.var("state_next", self.state_e)

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

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def data_f2g_pipeline(self):
        if self.reset:
            self.data_f2g_d1 = 0
            self.data_valid_f2g_d1 = 0
        elif self.clk_en:
            self.data_f2g_d1 = self.data_f2g
            self.data_valid_f2g_d1 = self.data_valid_f2g

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def dma_validate_ff(self):
        if self.reset:
            for i in range(self._params.queue_depth):
                self.dma_validate_r[i] = 0
        elif self.clk_en:
            for i in range(self._params.queue_depth):
                self.dma_validate_r[i] = self.cfg_st_dma_header[i]['validate']

    @always_comb
    def dma_validate_pulse_gen(self):
        for i in range(self._params.queue_depth):
            self.dma_validate_pulse[i] = self.cfg_st_dma_header[i]['validate'] & (
                ~self.dma_validate_r[i])

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def dma_invalidate_pulse_gen(self):
        if self.reset:
            for i in range(self._params.queue_depth):
                self.dma_invalidate_pulse[i] = 0
        elif self.clk_en:
            if ((self.state_r == self.state_e.idle)
                & (self.dma_header_r[self.queue_sel_w]['validate'])
                    & ~(self.dma_header_r[self.queue_sel_w]['num_words'] == 0)):
                self.dma_invalidate_pulse[self.queue_sel_w] = 1
            else:
                self.dma_invalidate_pulse[self.queue_sel_w] = 0

    @always_comb
    def assign_st_dma_header_hwclr(self):
        for i in range(self._params.queue_depth):
            self.st_dma_header_clr[i] = self.dma_invalidate_pulse[i]

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def dma_header_ff(self):
        if self.reset:
            for i in range(self._params.queue_depth):
                self.dma_header_r[i] = 0
        elif self.clk_en:
            for i in range(self._params.queue_depth):
                if self.dma_validate_pulse[i]:
                    self.dma_header_r[i] = self.cfg_st_dma_header[i]
                elif self.dma_invalidate_pulse[i]:
                    self.dma_header_r[i]['validate'] = 0

    @always_comb
    def state_fsm_logic(self):
        self.cache_data_next = self.cache_data_r
        self.cache_strb_next = self.cache_strb_r
        self.num_cnt_next = self.num_cnt_r
        self.cur_addr_next = self.cur_addr_r
        self.state_next = self.state_r
        self.is_first_word_next = self.is_first_word_r
        if self.state_r == self.state_e.off:
            if self.cfg_st_dma_ctrl_mode != 0:
                self.state_next = self.state_e.idle
        elif self.state_r == self.state_e.idle:
            self.num_cnt_next = 0
            self.cur_addr_next = 0
            if ((self.dma_header_r[self.queue_sel_w]['validate'] == 1) & (self.dma_header_r[self.queue_sel_w]['num_words'] != 0)):
                self.cur_addr_next = self.dma_header_r[self.queue_sel_w]['start_addr']
                self.num_cnt_next = self.dma_header_r[self.queue_sel_w]['num_words']
                self.is_first_word_next = 1
                if self.cur_addr_next[2, 1] == 0b00:
                    self.state_next = self.state_e.ready
                elif self.cur_addr_next[2, 1] == 0b01:
                    self.state_next = self.state_e.acc1
                elif self.cur_addr_next[2, 1] == 0b10:
                    self.state_next = self.state_e.acc2
                elif self.cur_addr_next[2, 1] == 0b11:
                    self.state_next = self.state_e.acc3
                else:
                    self.state_next = self.state_e.ready
        elif self.state_r == self.state_e.ready:
            if self.num_cnt_r == 0:
                self.state_next = self.state_e.done
            elif self.data_valid_f2g_d1 == 1:
                self.is_first_word_next = 0
                self.cache_data_next[self._params.cgra_data_width -
                                     1, 0] = self.data_f2g_d1
                self.cache_strb_next[1, 0] = 0b11
                self.num_cnt_next = self.num_cnt_r - 1
                if ~self.is_first_word_r:
                    self.cur_addr_next = self.cur_addr_r + \
                        (self._params.cgra_data_width // 8)
                self.state_next = self.state_e.acc1
        elif self.state_r == self.state_e.acc1:
            if self.num_cnt_r == 0:
                self.state_next = self.state_e.done
            elif self.data_valid_f2g_d1 == 1:
                self.is_first_word_next = 0
                self.cache_data_next[self._params.cgra_data_width * 2 - 1,
                                     self._params.cgra_data_width] = self.data_f2g_d1
                self.cache_strb_next[3, 2] = 0b11
                self.num_cnt_next = self.num_cnt_r - 1
                if ~self.is_first_word_r:
                    self.cur_addr_next = self.cur_addr_r + \
                        (self._params.cgra_data_width // 8)
                self.state_next = self.state_e.acc2
        elif self.state_r == self.state_e.acc2:
            if self.num_cnt_r == 0:
                self.state_next = self.state_e.done
            elif self.data_valid_f2g_d1 == 1:
                self.is_first_word_next = 0
                self.cache_data_next[self._params.cgra_data_width * 3 - 1,
                                     self._params.cgra_data_width * 2] = self.data_f2g_d1
                self.cache_strb_next[5, 4] = 0b11
                self.num_cnt_next = self.num_cnt_r - 1
                if ~self.is_first_word_r:
                    self.cur_addr_next = self.cur_addr_r + \
                        (self._params.cgra_data_width // 8)
                self.state_next = self.state_e.acc3
        elif self.state_r == self.state_e.acc3:
            if self.num_cnt_r == 0:
                self.state_next = self.state_e.done
            elif self.data_valid_f2g_d1 == 1:
                self.is_first_word_next = 0
                self.cache_data_next[self._params.cgra_data_width * 4 - 1,
                                     self._params.cgra_data_width * 3] = self.data_f2g_d1
                self.cache_strb_next[7, 6] = 0b11
                self.num_cnt_next = self.num_cnt_r - 1
                if ~self.is_first_word_r:
                    self.cur_addr_next = self.cur_addr_r + \
                        (self._params.cgra_data_width // 8)
                self.state_next = self.state_e.acc4
        elif self.state_r == self.state_e.acc4:
            if self.num_cnt_r == 0:
                self.state_next = self.state_e.done
            elif self.data_valid_f2g_d1 == 1:
                self.is_first_word_next = 0
                self.cache_data_next = concat(const(
                    0, self._params.bank_data_width-self._params.cgra_data_width), self.data_f2g_d1)
                self.cache_strb_next = concat(const(0, 6), const(0b11, 2))
                self.num_cnt_next = self.num_cnt_r - 1
                if ~self.is_first_word_r:
                    self.cur_addr_next = self.cur_addr_r + \
                        (self._params.cgra_data_width // 8)
                self.state_next = self.state_e.acc1
            else:
                self.cache_data_next = 0
                self.cache_strb_next = 0
                self.state_next = self.state_e.ready
        elif self.state_r == self.state_e.done:
            self.cache_data_next = 0
            self.cache_strb_next = 0
            self.num_cnt_next = 0
            self.state_next = self.state_e.idle
        else:
            self.cache_data_next = self.cache_data_r
            self.cache_strb_next = self.cache_strb_r
            self.num_cnt_next = self.num_cnt_r
            self.state_next = self.state_e.idle

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def state_fsm_ff(self):
        if self.reset:
            self.state_r = self.state_e.off
        elif self.clk_en:
            if self.cfg_st_dma_ctrl_mode == 0:
                self.state_r = self.state_e.off
            else:
                self.state_r = self.state_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def cache_ff(self):
        if self.reset:
            self.cache_data_r = 0
            self.cache_strb_r = 0
        elif self.clk_en:
            self.cache_data_r = self.cache_data_next
            self.cache_strb_r = self.cache_strb_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def counter_ff(self):
        if self.reset:
            self.num_cnt_r = 0
            self.cur_addr_r = 0
            self.is_first_word_r = 0
        elif self.clk_en:
            self.num_cnt_r = self.num_cnt_next
            self.cur_addr_r = self.cur_addr_next
            self.is_first_word_r = self.is_first_word_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def queue_sel_ff(self):
        if self.reset:
            self.queue_sel_r = 0
        elif self.clk_en:
            if self.state_r == self.state_e.idle:
                if self.cfg_st_dma_ctrl_mode == 0b11:
                    if self.dma_header_r[self.queue_sel_r]['validate'] & (self.dma_header_r[self.queue_sel_r]['num_words'] != 0):
                        self.queue_sel_r = self.queue_sel_r + 1
                else:
                    self.queue_sel_r = 0

    @always_comb
    def queue_sel_logic(self):
        if self.cfg_st_dma_ctrl_mode == 0b11:
            self.queue_sel_w = self.queue_sel_r
        else:
            self.queue_sel_w = 0

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
            self.wr_packet['wr_addr'] = self.cur_addr_r
        else:
            self.wr_packet['wr_en'] = 0
            self.wr_packet['wr_strb'] = 0
            self.wr_packet['wr_data'] = 0
            self.wr_packet['wr_addr'] = 0

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
        self.done_pulse_w = self.strm_done & (~self.strm_done_d1)

    def add_done_pulse_pipeline(self):
        # TODO: This maximum latency should be automatically set
        maximum_latency = 2 * self._params.num_glb_tiles + self.default_latency
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
                  self.done_pulse_d_arr[self.cfg_data_network_latency + self.default_latency])
