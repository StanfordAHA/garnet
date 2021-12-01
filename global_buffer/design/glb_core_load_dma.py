from kratos import Generator, always_ff, always_comb, posedge, resize, clog2, ext
from global_buffer.design.glb_loop_iter import GlbLoopIter
from global_buffer.design.glb_sched_gen import GlbSchedGen
from global_buffer.design.glb_addr_gen import GlbAddrGen
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader


class GlbCoreLoadDma(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_core_load_dma")
        self._params = _params
        self.header = GlbHeader(self._params)
        assert self._params.bank_data_width == self._params.cgra_data_width * 4

        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")

        self.data_g2f = self.output(
            "data_g2f", width=self._params.cgra_data_width)
        self.data_valid_g2f = self.output("data_valid_g2f", width=1)

        self.rdrq_packet = self.output(
            "rdrq_packet", self.header.rdrq_packet_t)
        self.rdrs_packet = self.input("rdrs_packet", self.header.rdrs_packet_t)

        self.cfg_ld_dma_num_repeat = self.input("cfg_ld_dma_num_repeat", max(1, clog2(self._params.queue_depth)))
        self.cfg_ld_dma_ctrl_use_valid = self.input(
            "cfg_ld_dma_ctrl_use_valid", 1)
        self.cfg_ld_dma_ctrl_mode = self.input("cfg_ld_dma_ctrl_mode", 2)
        self.cfg_data_network_latency = self.input(
            "cfg_data_network_latency", self._params.latency_width)
        self.cfg_ld_dma_header = self.input(
            "cfg_ld_dma_header", self.header.cfg_ld_dma_header_t, size=self._params.queue_depth)

        self.ld_dma_start_pulse = self.input("ld_dma_start_pulse", 1)
        self.ld_dma_done_pulse = self.output("ld_dma_done_pulse", 1)

        # local parameter
        self.default_latency = (self._params.glb_switch_pipeline_depth
                                + self._params.glb_bank_memory_pipeline_depth
                                + self._params.sram_gen_pipeline_depth
                                + self._params.sram_gen_output_pipeline_depth
                                + 1  # SRAM macro read latency
                                + self._params.glb_switch_pipeline_depth
                                + 2  # FIXME: Unnecessary delay of moving back and forth btw switch and router
                                + 1  # load_dma cache register delay
                                )

        # local variables
        self.strm_data = self.var("strm_data", self._params.cgra_data_width)
        self.strm_data_r = self.var(
            "strm_data_r", self._params.cgra_data_width)
        self.strm_data_valid = self.var("strm_data_valid", 1)
        self.strm_data_valid_r = self.var("strm_data_valid_r", 1)
        self.strm_data_sel = self.var(
            "strm_data_sel", self._params.bank_byte_offset - self._params.cgra_byte_offset)

        self.strm_rd_en_w = self.var("strm_rd_en_w", 1)
        self.strm_rd_addr_w = self.var(
            "strm_rd_addr_w", self._params.glb_addr_width)
        self.last_strm_rd_addr_r = self.var(
            "last_strm_rd_addr_r", self._params.glb_addr_width)

        self.ld_dma_start_pulse_next = self.var("ld_dma_start_pulse_next", 1)
        self.ld_dma_start_pulse_r = self.var("ld_dma_start_pulse_r", 1)
        self.is_first = self.var("is_first", 1)

        self.ld_dma_done_pulse_w = self.var("ld_dma_done_pulse_w", 1)

        self.bank_addr_match = self.var("bank_addr_match", 1)
        self.bank_rdrq_rd_en = self.var("bank_rdrq_rd_en", 1)
        self.bank_rdrq_rd_addr = self.var(
            "bank_rdrq_rd_addr", self._params.glb_addr_width)
        self.bank_rdrs_data_cache_r = self.var(
            "bank_rdrs_data_cache_r", self._params.bank_data_width)

        self.strm_run = self.var("strm_run", 1)
        self.loop_done = self.var("loop_done", 1)
        self.cycle_valid = self.var("cycle_valid", 1)
        self.cycle_count = self.var("cycle_count", self._params.axi_data_width)
        self.cycle_current_addr = self.var("cycle_current_addr", self._params.axi_data_width)
        self.data_current_addr = self.var("data_current_addr", self._params.axi_data_width)
        self.loop_mux_sel = self.var("loop_mux_sel", clog2(self._params.loop_level))
        self.queue_sel_r = self.var("queue_sel_r", max(1, clog2(self._params.queue_depth)))
        self.repeat_cnt = self.var("repeat_cnt", max(1, clog2(self._params.queue_depth)))

        self.add_always(self.cycle_counter)
        self.add_always(self.is_first_ff)
        self.add_always(self.strm_run_ff)
        self.add_always(self.strm_data_ff)
        self.add_strm_data_start_pulse_pipeline()
        self.add_ld_dma_done_pulse_pipeline()
        self.add_strm_rd_en_pipeline()
        self.add_strm_rd_addr_pipeline()
        self.add_always(self.ld_dma_start_pulse_logic)
        self.add_always(self.ld_dma_start_pulse_ff)
        self.add_always(self.strm_data_mux)
        self.add_always(self.ld_dma_done_pulse_logic)
        self.add_always(self.strm_rdrq_packet_ff)
        self.add_always(self.last_strm_rd_addr_ff)
        self.add_always(self.bank_rdrq_packet_logic)
        self.add_always(self.bank_rdrs_data_cache_ff)
        self.add_always(self.strm_data_logic)
        self.add_always(self.queue_sel_ff)

        # Loop iteration shared for cycle and data
        self.loop_iter = GlbLoopIter(self._params)
        self.add_child("loop_iter",
                       self.loop_iter,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       step=self.cycle_valid,
                       mux_sel_out=self.loop_mux_sel,
                       restart=self.loop_done)
        self.wire(self.loop_iter.dim, self.cfg_ld_dma_header[self.queue_sel_r][f"dim"])
        for i in range(self._params.loop_level):
            self.wire(self.loop_iter.ranges[i], self.cfg_ld_dma_header[self.queue_sel_r][f"range_{i}"])

        # Cycle stride
        self.cycle_stride_sched_gen = GlbSchedGen(self._params)
        self.add_child("cycle_stride_sched_gen",
                       self.cycle_stride_sched_gen,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       restart=self.ld_dma_start_pulse_r,
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
                       restart=self.ld_dma_start_pulse_r,
                       step=self.cycle_valid,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.cycle_current_addr)
        self.wire(self.cycle_stride_addr_gen.start_addr, ext(
            self.cfg_ld_dma_header[self.queue_sel_r][f"cycle_start_addr"], self._params.axi_data_width))
        for i in range(self._params.loop_level):
            self.wire(self.cycle_stride_addr_gen.strides[i],
                      self.cfg_ld_dma_header[self.queue_sel_r][f"cycle_stride_{i}"])

        # Data stride
        self.data_stride_addr_gen = GlbAddrGen(self._params)
        self.add_child("data_stride_addr_gen",
                       self.data_stride_addr_gen,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       restart=self.ld_dma_start_pulse_r,
                       step=self.cycle_valid,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.data_current_addr)
        self.wire(self.data_stride_addr_gen.start_addr, ext(
            self.cfg_ld_dma_header[self.queue_sel_r][f"start_addr"], self._params.axi_data_width))
        for i in range(self._params.loop_level):
            self.wire(self.data_stride_addr_gen.strides[i], self.cfg_ld_dma_header[self.queue_sel_r][f"stride_{i}"])

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def queue_sel_ff(self):
        if self.reset:
            self.queue_sel_r = 0
            self.repeat_cnt = 0
        elif self.clk_en:
            if self.cfg_ld_dma_ctrl_mode == 2:
                if self.ld_dma_done_pulse:
                    if (self.repeat_cnt + 1) < self.cfg_ld_dma_num_repeat:
                        self.repeat_cnt += 1
            elif self.cfg_ld_dma_ctrl_mode == 3:
                if self.ld_dma_done_pulse:
                    if (self.repeat_cnt + 1) < self.cfg_ld_dma_num_repeat:
                        self.queue_sel_r = self.queue_sel_r + 1
                        self.repeat_cnt += 1
            else:
                self.queue_sel_r = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def is_first_ff(self):
        if self.reset:
            self.is_first = 0
        elif self.clk_en:
            if self.ld_dma_start_pulse_r:
                self.is_first = 1
            elif self.bank_rdrq_rd_en:
                self.is_first = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def strm_run_ff(self):
        if self.reset:
            self.strm_run = 0
        elif self.clk_en:
            if self.ld_dma_start_pulse_r:
                self.strm_run = 1
            elif self.loop_done:
                self.strm_run = 0

    @always_comb
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

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def ld_dma_start_pulse_ff(self):
        if self.reset:
            self.ld_dma_start_pulse_r = 0
        elif self.clk_en:
            if self.ld_dma_start_pulse_r:
                self.ld_dma_start_pulse_r = 0
            else:
                self.ld_dma_start_pulse_r = self.ld_dma_start_pulse_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def cycle_counter(self):
        if self.reset:
            self.cycle_count = 0
        elif self.clk_en:
            if self.ld_dma_start_pulse_r:
                self.cycle_count = 0
            elif self.loop_done:
                self.cycle_count = 0
            elif self.strm_run:
                self.cycle_count = self.cycle_count + 1

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def strm_data_ff(self):
        if self.reset:
            self.strm_data_r = 0
            self.strm_data_valid_r = 0
        elif self.clk_en:
            self.strm_data_r = self.strm_data
            self.strm_data_valid_r = self.strm_data_valid

    @always_comb
    def strm_data_mux(self):
        if self.cfg_ld_dma_ctrl_use_valid:
            self.data_g2f = self.strm_data_r
            self.data_valid_g2f = self.strm_data_valid_r
        else:
            self.data_g2f = self.strm_data_r
            self.data_valid_g2f = self.strm_data_start_pulse

    @always_comb
    def ld_dma_done_pulse_logic(self):
        self.ld_dma_done_pulse_w = self.strm_run & self.loop_done

    @always_comb
    def strm_rdrq_packet_ff(self):
        self.strm_rd_en_w = self.cycle_valid
        self.strm_rd_addr_w = resize(self.data_current_addr,
                                     self._params.glb_addr_width) << self._params.cgra_byte_offset

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def last_strm_rd_addr_ff(self):
        if self.reset:
            self.last_strm_rd_addr_r = 0
        elif self.clk_en:
            if self.strm_rd_en_w:
                self.last_strm_rd_addr_r = self.strm_rd_addr_w

    @always_comb
    def bank_rdrq_packet_logic(self):
        self.bank_addr_match = (self.strm_rd_addr_w[self._params.glb_addr_width - 1, self._params.bank_byte_offset]
                                == self.last_strm_rd_addr_r[self._params.glb_addr_width - 1,
                                                            self._params.bank_byte_offset])
        self.bank_rdrq_rd_en = self.strm_rd_en_w & (self.is_first | (~self.bank_addr_match))
        self.bank_rdrq_rd_addr = self.strm_rd_addr_w
        self.rdrq_packet['rd_en'] = self.bank_rdrq_rd_en
        self.rdrq_packet['rd_addr'] = self.bank_rdrq_rd_addr

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def bank_rdrs_data_cache_ff(self):
        if self.reset:
            self.bank_rdrs_data_cache_r = 0
        elif self.clk_en:
            if self.rdrs_packet['rd_data_valid']:
                self.bank_rdrs_data_cache_r = self.rdrs_packet['rd_data']

    @always_comb
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
        maximum_latency = 2 * self._params.num_glb_tiles + self.default_latency
        latency_width = clog2(maximum_latency)
        self.strm_rd_en_d_arr = self.var(
            "strm_rd_en_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.strm_rd_en_pipeline = Pipeline(width=1,
                                            depth=maximum_latency,
                                            flatten_output=True)
        self.add_child("strm_rd_en_pipeline",
                       self.strm_rd_en_pipeline,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       in_=self.strm_rd_en_w,
                       out_=self.strm_rd_en_d_arr)

        self.wire(self.strm_data_valid, self.strm_rd_en_d_arr[resize(
            self.cfg_data_network_latency, latency_width) + self.default_latency])

    def add_strm_rd_addr_pipeline(self):
        maximum_latency = 2 * self._params.num_glb_tiles + self.default_latency
        latency_width = clog2(maximum_latency)
        self.strm_rd_addr_d_arr = self.var(
            "strm_rd_addr_d_arr", width=self._params.glb_addr_width, size=maximum_latency, explicit_array=True)
        self.strm_rd_addr_pipeline = Pipeline(width=self._params.glb_addr_width,
                                              depth=maximum_latency,
                                              flatten_output=True)
        self.add_child("strm_rd_addr_pipeline",
                       self.strm_rd_addr_pipeline,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       in_=self.strm_rd_addr_w,
                       out_=self.strm_rd_addr_d_arr)

        self.strm_data_sel = self.strm_rd_addr_d_arr[resize(self.cfg_data_network_latency, latency_width)
                                                     + self.default_latency][self._params.bank_byte_offset - 1,
                                                                             self._params.cgra_byte_offset]

    def add_strm_data_start_pulse_pipeline(self):
        maximum_latency = 2 * self._params.num_glb_tiles + self.default_latency + 2
        latency_width = clog2(maximum_latency)
        self.strm_data_start_pulse_d_arr = self.var(
            "strm_data_start_pulse_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.strm_data_start_pulse_pipeline = Pipeline(width=1,
                                                       depth=maximum_latency,
                                                       flatten_output=True)
        self.add_child("strm_dma_start_pulse_pipeline",
                       self.strm_data_start_pulse_pipeline,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       in_=self.ld_dma_start_pulse_r,
                       out_=self.strm_data_start_pulse_d_arr)
        self.strm_data_start_pulse = self.var("strm_data_start_pulse", 1)
        self.wire(self.strm_data_start_pulse,
                  self.strm_data_start_pulse_d_arr[resize(self.cfg_data_network_latency, latency_width)
                                                   + self.default_latency + 1])

    def add_ld_dma_done_pulse_pipeline(self):
        maximum_latency = 2 * self._params.num_glb_tiles + self.default_latency + 3
        latency_width = clog2(maximum_latency)
        self.ld_dma_done_pulse_d_arr = self.var(
            "ld_dma_done_pulse_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.ld_dma_done_pulse_pipeline = Pipeline(width=1,
                                                   depth=maximum_latency,
                                                   flatten_output=True)
        self.add_child("ld_dma_done_pulse_pipeline",
                       self.ld_dma_done_pulse_pipeline,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       in_=self.ld_dma_done_pulse_w,
                       out_=self.ld_dma_done_pulse_d_arr)
        self.wire(self.ld_dma_done_pulse,
                  self.ld_dma_done_pulse_d_arr[resize(self.cfg_data_network_latency, latency_width)
                                               + self.default_latency + 3])
