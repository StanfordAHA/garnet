from kratos import Generator, always_ff, always_comb, posedge, resize, clog2, ext, const, clock_en
import kratos as kts
from global_buffer.design.glb_loop_iter import GlbLoopIter
from global_buffer.design.glb_sched_gen import GlbSchedGen
from global_buffer.design.glb_addr_gen import GlbAddrGen
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen
from global_buffer.design.fifo import FIFO


class GlbLoadDma_E64_MB(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_load_dma")
        self._params = _params
        self.header = GlbHeader(self._params)
        assert self._params.bank_data_width == self._params.cgra_data_width * 4
        assert self._params.tile2sram_rd_delay >= self._params.flush_crossbar_pipeline_depth

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.num_packets = 4
        self.data_g2f = self.output("data_g2f", width=self._params.cgra_data_width,
                                    size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.data_g2f_vld = self.output("data_g2f_vld", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.data_g2f_rdy = self.input("data_g2f_rdy", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)

        self.ctrl_g2f = self.output("ctrl_g2f", 1, size=self._params.cgra_per_glb, packed=True)

        self.data_flush = self.output("data_flush", 1)

        self.rdrq_packet_dma2bank = self.output("rdrq_packet_dma2bank", self.header.rdrq_packet_t)
        self.rdrs_packet_bank2dma = self.input("rdrs_packet_bank2dma", self.header.rdrs_packet_t, size=_params.banks_per_tile)
        if self._params.include_glb_ring_switch:
            self.rdrq_packet_dma2ring = self.output("rdrq_packet_dma2ring", self.header.rdrq_packet_t)
            self.rdrs_packet_ring2dma = self.input("rdrs_packet_ring2dma", self.header.rdrs_packet_t)

            self.cfg_tile_connected_prev = self.input("cfg_tile_connected_prev", 1)
            self.cfg_tile_connected_next = self.input("cfg_tile_connected_next", 1)

        self.cfg_ld_dma_num_repeat = self.input("cfg_ld_dma_num_repeat", clog2(self._params.queue_depth) + 1)
        self.cfg_ld_dma_ctrl_valid_mode = self.input("cfg_ld_dma_ctrl_valid_mode", 2)
        self.cfg_ld_dma_ctrl_flush_mode = self.input("cfg_ld_dma_ctrl_flush_mode", 1)
        self.cfg_ld_dma_ctrl_mode = self.input("cfg_ld_dma_ctrl_mode", 3)

        self.cfg_data_network_latency = self.input("cfg_data_network_latency", self._params.latency_width)
        self.cfg_ld_dma_header = self.input(
            "cfg_ld_dma_header", self.header.cfg_load_dma_header_t, size=self._params.queue_depth)
        self.cfg_data_network_g2f_mux = self.input("cfg_data_network_g2f_mux", self._params.cgra_per_glb)

        # Exchange 64 (configuration). Contains info about multi-bank mode as well
        self.cfg_exchange_64_mode = self.input("cfg_exchange_64_mode", 2)

        self.clk_en_dma2bank = self.output("clk_en_dma2bank", 1)
        self.ld_dma_start_pulse = self.input("ld_dma_start_pulse", 1)
        self.ld_dma_done_interrupt = self.output("ld_dma_done_interrupt", 1)

        # local variables
        self.data_flush_w = self.var("data_flush_w", 1)
        self.rdrq_packet_dma2bank_w = self.var("rdrq_packet_dma2bank_w", self.header.rdrq_packet_t)
        if self._params.include_glb_ring_switch:
            self.rdrq_packet_dma2ring_w = self.var("rdrq_packet_dma2ring_w", self.header.rdrq_packet_t)
        self.rdrs_packet = self.var("rdrs_packet", self.header.rdrs_packet_t, size=_params.banks_per_tile)
        self.data_g2f_w = self.var("data_g2f_w", width=self._params.cgra_data_width,
                                   size=self._params.cgra_per_glb, packed=True)
        self.data_g2f_vld_w = self.var("data_g2f_vld_w", 1, size=self._params.cgra_per_glb, packed=True)
        self.ctrl_g2f_w = self.var("ctrl_g2f_w", 1, size=self._params.cgra_per_glb, packed=True)

        self.ld_dma_done_pulse = self.var("ld_dma_done_pulse", 1)
        self.ld_dma_done_pulse_latch = self.var("ld_dma_done_pulse_latch", 1)
        self.ld_dma_done_pulse_anded = self.var("ld_dma_done_pulse_anded", 1)
        self.ld_dma_done_pulse_last = self.var("ld_dma_done_pulse_last", 1)
        self.ld_dma_done_pulse_pipeline_out = self.var("ld_dma_done_pulse_pipeline_out", 1)
        self.strm_data = self.var("strm_data", self._params.cgra_data_width, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.strm_data_valid = self.var("strm_data_valid", 1, size=self._params.cgra_per_glb, packed=True)
        self.strm_ctrl_muxed = self.var("strm_ctrl_muxed", 1)
        self.strm_data_sel_w = self.var(
            "strm_data_sel_w", self._params.bank_byte_offset - self._params.cgra_byte_offset)
        self.strm_data_sel = self.var("strm_data_sel", self._params.bank_byte_offset - self._params.cgra_byte_offset)

        self.strm_rd_en_w = self.var("strm_rd_en_w", 1)
        self.strm_rd_addr_w = self.var("strm_rd_addr_w", self._params.glb_addr_width)
        self.last_strm_rd_addr_r = self.var("last_strm_rd_addr_r", self._params.glb_addr_width)

        self.ld_dma_start_pulse_next = self.var("ld_dma_start_pulse_next", 1)
        self.ld_dma_start_pulse_r = self.var("ld_dma_start_pulse_r", 1)

        self.ld_dma_start_pulse_emit_flush_r = self.var("ld_dma_start_pulse_emit_flush_r", 1)

        self.is_first = self.var("is_first", 1)

        self.ld_dma_done_pulse_w = self.var("ld_dma_done_pulse_w", 1)

        self.is_cached = self.var("is_cached", 1)
        self.bank_rdrq_rd_en = self.var("bank_rdrq_rd_en", 1)
        self.bank_rdrq_rd_addr = self.var("bank_rdrq_rd_addr", self._params.glb_addr_width)
        self.bank_rdrs_data_cache_r = self.var("bank_rdrs_data_cache_r", self._params.bank_data_width, size=self._params.cgra_per_glb, packed=True)

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

        self.exchange_64_mode_on = self.var("exchange_64_mode_on", 1)
        self.multi_bank_mode_on = self.var("multi_bank_mode_on", 1)

        # ready_valid controller
        self.cycle_counter_en = self.var("cycle_counter_en", 1)
        self.iter_step_valid = self.var("iter_step_valid", 1)
        self.fifo_push_ready = self.var("fifo_push_ready", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.packet_64_push_ready = self.var("packet_64_push_ready", 1, size=[self._params.cgra_per_glb], packed=True)
        self.packet_128_push_ready = self.var("packet_128_push_ready", 1)
        self.data_dma2fifo = self.var("data_dma2fifo", self._params.cgra_data_width, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.data_fifo2cgra = self.var("data_fifo2cgra", self._params.cgra_data_width, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo_push = self.var("fifo_push", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo_pop_cond = self.var("fifo_pop_cond", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo_pop = self.var("fifo_pop", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.packet_64_pop = self.var("packet_64_pop", 1, size=[self._params.cgra_per_glb], packed=True)
        self.packet_128_pop = self.var("packet_128_pop", 1)
        self.fifo_full = self.var("fifo_full", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo_empty = self.var("fifo_empty", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo_almost_full = self.var("fifo_almost_full", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo_depth = self._params.max_num_chain * 2 + self._params.tile2sram_rd_delay

        self.data_g2f_rdy_muxed = self.var("data_g2f_rdy_muxed", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo2skid_rdy = self.var("fifo2skid_rdy", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo2skid_rdy_muxed = self.var("fifo2skid_rdy_muxed", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo2skid_vld = self.var("fifo2skid_vld", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.fifo2skid_vld_muxed = self.var("fifo2skid_vld_muxed", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.skid_in = self.var("skid_in", self._params.cgra_data_width, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.skid_out = self.var("skid_out", self._params.cgra_data_width, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.skid_push = self.var("skid_push", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.skid_pop = self.var("skid_pop", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.skid_full = self.var("skid_full", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.skid_empty = self.var("skid_empty", 1, size=[self._params.cgra_per_glb, self.num_packets], packed=True)
        self.all_skid_empty = self.var("all_skid_empty", 1, size=[self.num_packets], packed=True)
        self.all_skid_empty_muxed = self.var("all_skid_empty_muxed", 1)

        self.add_fifo()
        self.add_skid()
        self.add_always(self.fifo_to_skid)
        self.add_always(self.data_g2f_rdy_muxed_logic)
        self.add_always(self.all_skid_empty_logic)
        self.add_always(self.all_skid_empty_muxed_logic)

        # E64/mutli-bank control
        self.wire(self.exchange_64_mode_on, self.cfg_exchange_64_mode[0])
        self.wire(self.multi_bank_mode_on, self.cfg_exchange_64_mode == self._params.exchange_64_multibank_mode)

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
        self.add_always(self.ld_dma_start_pulse_emit_flush_ff)
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
        self.wire(self.loop_iter.dim, self.current_dma_header["dim"])
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
                       bank_toggle_mode=const(0, 1),
                       mod_8_step=const(0, 1),
                       step=self.iter_step_valid,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.cycle_current_addr)
        self.wire(self.cycle_stride_addr_gen.start_addr, self.current_dma_header["cycle_start_addr"])
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
                       bank_toggle_mode=const(0, 1),
                       mod_8_step=const(0, 1),
                       step=self.iter_step_valid,
                       mux_sel=self.loop_mux_sel,
                       addr_out=self.data_current_addr)
        self.wire(self.data_stride_addr_gen.start_addr, ext(self.current_dma_header["start_addr"],
                                                            self._params.glb_addr_width + 1))
        for i in range(self._params.load_dma_loop_level):
            self.wire(self.data_stride_addr_gen.strides[i], self.current_dma_header[f"stride_{i}"])

    # FIFO for ready/valid
    def add_fifo(self):
        self.fifo_almost_full_diff = self.var("fifo_almost_full_diff", clog2(self.fifo_depth))
        for i in range(self._params.cgra_per_glb):
            for packet_16 in range(self.num_packets):
                self.data_g2f_fifo = FIFO(self._params.cgra_data_width, self.fifo_depth)
                self.add_child(f"data_g2f_fifo_{i}_packet_{packet_16}",
                            self.data_g2f_fifo,
                            clk=self.clk,
                            clk_en=const(1, 1),
                            reset=self.reset,
                            flush=self.ld_dma_start_pulse_r,
                            data_in=self.data_dma2fifo[i][packet_16],
                            data_out=self.data_fifo2cgra[i][packet_16],
                            push=self.fifo_push[i][packet_16],
                            pop=self.fifo_pop[i][packet_16],
                            full=self.fifo_full[i][packet_16],
                            empty=self.fifo_empty[i][packet_16],
                            almost_full=self.fifo_almost_full[i][packet_16],
                            almost_full_diff=self.fifo_almost_full_diff,
                            almost_empty_diff=const(2, clog2(self.fifo_depth)))

                # TODO: Using almost full here may cause issues
                # TODO: Maybe revisit this and make sure it isn't causing any unnecessary bubbles
                self.wire(self.fifo_push_ready[i][packet_16], ~self.fifo_almost_full[i][packet_16])
                self.wire(self.data_dma2fifo[i][packet_16], self.strm_data[i][packet_16])

                if (packet_16 == 0) & (i == 0):
                    self.wire(self.fifo_push[i][packet_16], ~self.fifo_full[i][packet_16] & self.strm_data_valid[i])
                else:
                    self.wire(self.fifo_push[i][packet_16], kts.ternary(self.exchange_64_mode_on, ~self.fifo_full[i][packet_16] & self.strm_data_valid[i], 0))

                self.wire(self.fifo2skid_vld_muxed[i][packet_16], ~self.fifo_empty[i][packet_16])
                self.wire(self.fifo_pop_cond[i][packet_16], self.fifo2skid_vld_muxed[i][packet_16] & self.fifo2skid_rdy_muxed[i][packet_16])

                if (packet_16 == 0) & (i == 0):
                    self.wire(self.fifo_pop[i][packet_16], kts.ternary(self.multi_bank_mode_on, self.packet_128_pop,
                                                                kts.ternary(self.exchange_64_mode_on, self.packet_64_pop[i],
                                                                            self.fifo_pop_cond[i][packet_16])))
                else:
                    self.wire(self.fifo_pop[i][packet_16], kts.ternary(self.multi_bank_mode_on, self.packet_128_pop, self.packet_64_pop[i]))

            # Synchronization
            self.wire(self.packet_64_pop[i], self.fifo_pop_cond[i][0] & self.fifo_pop_cond[i][1] & self.fifo_pop_cond[i][2] & self.fifo_pop_cond[i][3])
            self.wire(self.packet_64_push_ready[i], self.fifo_push_ready[i][0] & self.fifo_push_ready[i][1] & self.fifo_push_ready[i][2] & self.fifo_push_ready[i][3])

        # Synchonization
        self.wire(self.packet_128_pop, self.packet_64_pop[0] & self.packet_64_pop[1])
        self.wire(self.packet_128_push_ready, self.packet_64_push_ready[0] & self.packet_64_push_ready[1])
        self.add_always(self.almost_full_diff_logic)

    @always_comb
    def fifo_to_skid(self):
        for packet_16 in range(self.num_packets):
            for i in range(self._params.cgra_per_glb):
                self.fifo2skid_rdy_muxed[i][packet_16] = 0
                if self.multi_bank_mode_on:
                    self.fifo2skid_rdy_muxed[i][packet_16] = self.fifo2skid_rdy[i][packet_16]
                    self.fifo2skid_vld[i][packet_16] = self.fifo2skid_vld_muxed[i][packet_16]
                    self.skid_in[i][packet_16] = self.data_fifo2cgra[i][packet_16]

                else:
                    if self.cfg_data_network_g2f_mux[i] == 1:
                        self.fifo2skid_rdy_muxed[0][packet_16] = self.fifo2skid_rdy[i][packet_16]
                        self.fifo2skid_vld[i][packet_16] = self.fifo2skid_vld_muxed[0][packet_16]
                        self.skid_in[i][packet_16] = self.data_fifo2cgra[0][packet_16]
                    else:
                        self.fifo2skid_rdy_muxed[i][packet_16] = self.fifo2skid_rdy_muxed[i][packet_16]
                        self.fifo2skid_vld[i][packet_16] = 0
                        self.skid_in[i][packet_16] = 0

    @always_comb
    def data_g2f_rdy_muxed_logic(self):
        for packet_16 in range(self.num_packets):
            for i in range(self._params.cgra_per_glb):
                if self.cfg_ld_dma_ctrl_valid_mode == self._params.ld_dma_valid_mode_ready_valid:
                    self.data_g2f_rdy_muxed[i][packet_16] = self.data_g2f_rdy[i][packet_16]
                else:
                    self.data_g2f_rdy_muxed[i][packet_16] = const(1, 1)

    # output fifo
    def add_skid(self):
        for packet_16 in range(self.num_packets):
            self.skid = []
            for i in range(self._params.cgra_per_glb):
                self.skid.append(FIFO(self._params.cgra_data_width, 2))
                self.add_child(f"data_g2f_skid_{i}_{packet_16}",
                               self.skid[i],
                               clk=self.clk,
                               clk_en=const(1, 1),
                               reset=self.reset,
                               flush=self.ld_dma_start_pulse_r,
                               data_in=self.skid_in[i][packet_16],
                               data_out=self.skid_out[i][packet_16],
                               push=self.skid_push[i][packet_16],
                               pop=self.skid_pop[i][packet_16],
                               full=self.skid_full[i][packet_16],
                               empty=self.skid_empty[i][packet_16],
                               almost_full_diff=const(0, 1),
                               almost_empty_diff=const(0, 1))

                self.wire(self.skid_out[i][packet_16], self.data_g2f[i][packet_16])

                self.wire(self.fifo2skid_rdy[i][packet_16], ~self.skid_full[i][packet_16])

                # self.wire(self.skid_push[i][packet_16], self.fifo2skid_rdy[i][packet_16] & self.fifo2skid_vld[i][packet_16])
                self.wire(self.skid_push[i][packet_16], kts.ternary(self.multi_bank_mode_on, self.fifo_pop[i][packet_16],
                                                                    kts.ternary(self.cfg_data_network_g2f_mux[i] == 1, self.fifo_pop[0][packet_16], 0)))
                self.wire(~self.skid_empty[i][packet_16], self.data_g2f_vld[i][packet_16])

                self.wire(self.skid_pop[i][packet_16], ~self.skid_empty[i][packet_16] & self.data_g2f_rdy_muxed[i][packet_16])

    @always_comb
    def almost_full_diff_logic(self):
        self.fifo_almost_full_diff = resize(const(self._params.tile2sram_rd_delay + 2,
                                                  clog2(self.fifo_depth))
                                            + self.cfg_data_network_latency, clog2(self.fifo_depth))

    @always_comb
    def iter_step_logic(self):
        # Cycle_counter_en is a proxy for NOT in RV mode
        if self.cycle_counter_en:
            self.iter_step_valid = self.cycle_valid
        else:
            # synchronization logic here
            self.iter_step_valid = kts.ternary(self.multi_bank_mode_on, self.strm_run & self.packet_128_push_ready,
                                        kts.ternary(self.exchange_64_mode_on, self.strm_run & self.packet_64_push_ready[0],
                                                    self.strm_run & self.fifo_push_ready[0][0]))

    @always_ff((posedge, "clk"), (posedge, "reset"))
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

    @always_ff((posedge, "clk"), (posedge, "reset"))
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

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def is_first_ff(self):
        if self.reset:
            self.is_first = 0
        else:
            if self.ld_dma_start_pulse_r:
                self.is_first = 1
            elif self.bank_rdrq_rd_en:
                self.is_first = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def strm_run_ff(self):
        if self.reset:
            self.strm_run = 0
        else:
            if self.ld_dma_start_pulse_r:
                self.strm_run = 1
            elif self.loop_done:
                self.strm_run = 0

    @always_comb
    def ld_dma_start_pulse_logic(self):
        if (self.cfg_ld_dma_ctrl_mode == 0):
            self.ld_dma_start_pulse_next = 0

        # ctrl_mode == 4 is emit flush only mode
        elif ((self.cfg_ld_dma_ctrl_mode == 1) | (self.cfg_ld_dma_ctrl_mode == 4)):
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
        else:
            if self.cfg_ld_dma_ctrl_mode == 4:
                self.ld_dma_start_pulse_r = 0
            else:
                if self.ld_dma_start_pulse_r:
                    self.ld_dma_start_pulse_r = 0
                else:
                    self.ld_dma_start_pulse_r = self.ld_dma_start_pulse_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def ld_dma_start_pulse_emit_flush_ff(self):
        if self.reset:
            self.ld_dma_start_pulse_emit_flush_r = 0
        else:
            if self.ld_dma_start_pulse_emit_flush_r:
                self.ld_dma_start_pulse_emit_flush_r = 0
            else:
                self.ld_dma_start_pulse_emit_flush_r = self.ld_dma_start_pulse_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
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

    @always_comb
    def strm_data_flush_mux(self):
        if self.cfg_ld_dma_ctrl_flush_mode == self._params.ld_dma_flush_mode_external:
            self.data_flush_w = self.strm_data_start_pulse
            if self.cfg_ld_dma_ctrl_valid_mode == self._params.ld_dma_valid_mode_valid:
                self.strm_ctrl_muxed = self.strm_data_valid[0]
            else:
                self.strm_ctrl_muxed = 0
        else:
            self.data_flush_w = 0
            if self.cfg_ld_dma_ctrl_valid_mode == self._params.ld_dma_valid_mode_valid:
                self.strm_ctrl_muxed = self.strm_data_valid[0]
            else:
                self.strm_ctrl_muxed = self.strm_data_start_pulse

    @always_comb
    def ctrl_mux(self):
        for i in range(self._params.cgra_per_glb):
            if (self.cfg_data_network_g2f_mux[i] == 1) | (self.multi_bank_mode_on):
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
        assert self._params.flush_crossbar_pipeline_depth + self._params.config_port_pipeline_depth <= 2
        self.pipeline_flush = Pipeline(width=1,
                                       depth=(2 - self._params.flush_crossbar_pipeline_depth - self._params.config_port_pipeline_depth))
        self.add_child("pipeline_flush",
                       self.pipeline_flush,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.data_flush_w,
                       out_=self.data_flush)

    @always_comb
    def ld_dma_done_pulse_logic(self):
        self.ld_dma_done_pulse_w = self.strm_run & self.loop_done

    @always_comb
    def strm_rdrq_packet_logic(self):
        self.strm_rd_en_w = self.iter_step_valid
        self.strm_rd_addr_w = resize(self.data_current_addr, self._params.glb_addr_width)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def last_strm_rd_addr_ff(self):
        if self.reset:
            self.last_strm_rd_addr_r = 0
        else:
            if self.strm_rd_en_w:
                self.last_strm_rd_addr_r = self.strm_rd_addr_w

    @always_comb
    def bank_rdrq_packet_logic(self):
        self.is_cached = (self.strm_rd_addr_w[self._params.glb_addr_width - 1, self._params.bank_byte_offset]
                          == self.last_strm_rd_addr_r[self._params.glb_addr_width - 1,
                                                      self._params.bank_byte_offset])
        self.bank_rdrq_rd_en = self.strm_rd_en_w & (self.is_first | (~self.is_cached))
        self.bank_rdrq_rd_addr = self.strm_rd_addr_w

    @always_comb
    def rdrq_packet_logic(self):
        if self._params.include_glb_ring_switch:
            if self.cfg_tile_connected_next | self.cfg_tile_connected_prev:
                self.rdrq_packet_dma2bank_w = 0
                self.rdrq_packet_dma2ring_w['rd_en'] = self.bank_rdrq_rd_en
                self.rdrq_packet_dma2ring_w['rd_addr'] = self.bank_rdrq_rd_addr
            else:
                self.rdrq_packet_dma2bank_w['rd_en'] = self.bank_rdrq_rd_en
                self.rdrq_packet_dma2bank_w['rd_addr'] = self.bank_rdrq_rd_addr
                self.rdrq_packet_dma2ring_w = 0
        else:
            self.rdrq_packet_dma2bank_w['rd_en'] = self.bank_rdrq_rd_en
            self.rdrq_packet_dma2bank_w['rd_addr'] = self.bank_rdrq_rd_addr

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_packet_ff(self):
        if self.reset:
            self.rdrq_packet_dma2bank = 0
            if self._params.include_glb_ring_switch:
                self.rdrq_packet_dma2ring = 0
        else:
            self.rdrq_packet_dma2bank = self.rdrq_packet_dma2bank_w
            if self._params.include_glb_ring_switch:
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

    @always_comb
    def rdrs_packet_logic(self):
        if self._params.include_glb_ring_switch:
            #Not including multi-bank for ring path
            self.rdrs_packet = 0
            if self.cfg_tile_connected_next | self.cfg_tile_connected_prev:
                self.rdrs_packet[0] = self.rdrs_packet_ring2dma
            else:
                self.rdrs_packet = self.rdrs_packet_bank2dma
        else:
            self.rdrs_packet = self.rdrs_packet_bank2dma

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def bank_rdrs_data_cache_ff(self):
        if self.reset:
            self.bank_rdrs_data_cache_r = 0
        else:
            # Kratos won't support this for loop. Hard wire for now.
            # for i in range(self._params.cgra_per_glb):
            #     if self.rdrs_packet[i]['rd_data_valid']:
            #         self.bank_rdrs_data_cache_r[i] = self.rdrs_packet[i]['rd_data']

                if self.rdrs_packet[0]['rd_data_valid']:
                    self.bank_rdrs_data_cache_r[0] = self.rdrs_packet[0]['rd_data']

                if self.rdrs_packet[1]['rd_data_valid']:
                    self.bank_rdrs_data_cache_r[1] = self.rdrs_packet[1]['rd_data']

    @always_comb
    def strm_data_logic(self):
        # Assign strm_data[0]
        for i in range(self._params.cgra_per_glb):
            if self.exchange_64_mode_on:
                self.strm_data[i][0] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width - 1, 0]
            else:
                if self.strm_data_sel == 0:
                    self.strm_data[i][0] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width - 1, 0]
                elif self.strm_data_sel == 1:
                    self.strm_data[i][0] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width * 2 - 1,
                                                                          self._params.cgra_data_width * 1]
                elif self.strm_data_sel == 2:
                    self.strm_data[i][0] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width * 3 - 1,
                                                                          self._params.cgra_data_width * 2]
                elif self.strm_data_sel == 3:
                    self.strm_data[i][0] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width * 4 - 1,
                                                                          self._params.cgra_data_width * 3]
                else:
                    self.strm_data[i][0] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width - 1, 0]

            # Assign rest of strm_data packet
            if self.exchange_64_mode_on:
                self.strm_data[i][1] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width * 2 - 1,
                                                                      self._params.cgra_data_width * 1]
                self.strm_data[i][2] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width * 3 - 1,
                                                                      self._params.cgra_data_width * 2]
                self.strm_data[i][3] = self.bank_rdrs_data_cache_r[i][self._params.cgra_data_width * 4 - 1,
                                                                      self._params.cgra_data_width * 3]
            else:
                self.strm_data[i][1] = 0
                self.strm_data[i][2] = 0
                self.strm_data[i][3] = 0

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

        for i in range(self._params.cgra_per_glb):
            if i == 0:
                self.wire(self.strm_data_valid[i], self.strm_rd_en_d_arr[resize(
                    self.cfg_data_network_latency, latency_width) + self._params.tile2sram_rd_delay])
            else:
                self.wire(self.strm_data_valid[i], kts.ternary(self.multi_bank_mode_on, self.strm_rd_en_d_arr[resize(
                    self.cfg_data_network_latency, latency_width) + self._params.tile2sram_rd_delay], 0))

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
                       in_=self.ld_dma_start_pulse_emit_flush_r,
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

    @always_comb
    def all_skid_empty_logic(self):
        for packet_16 in range(self.num_packets):
            self.all_skid_empty[packet_16] = 1
            for i in range(self._params.cgra_per_glb):
                if self.cfg_data_network_g2f_mux[i] | self.multi_bank_mode_on:
                    self.all_skid_empty[packet_16] = self.all_skid_empty[packet_16] & self.skid_empty[i][packet_16]
                else:
                    self.all_skid_empty[packet_16] = self.all_skid_empty[packet_16]

    @always_comb
    def all_skid_empty_muxed_logic(self):
        self.wire(self.all_skid_empty_muxed, kts.ternary(self.exchange_64_mode_on, self.all_skid_empty[0] & self.all_skid_empty[1] & self.all_skid_empty[2] & self.all_skid_empty[3],
                                                         self.all_skid_empty[0]))

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def done_pulse_ctrl(self):
        if self.reset:
            self.ld_dma_done_pulse_latch = 0
        else:
            if self.ld_dma_done_pulse_pipeline_out:
                self.ld_dma_done_pulse_latch = 1
            elif self.ld_dma_done_pulse_latch & self.all_skid_empty_muxed:
                self.ld_dma_done_pulse_latch = 0

    @always_comb
    def done_pulse_anded_comb(self):
        self.ld_dma_done_pulse_anded = self.ld_dma_done_pulse_latch & self.all_skid_empty_muxed

    @always_comb
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

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def interrupt_ff(self):
        if self.reset:
            self.ld_dma_done_interrupt = 0
        else:
            if self.ld_dma_done_pulse:
                self.ld_dma_done_interrupt = 1
            elif self.ld_dma_done_pulse_last:
                self.ld_dma_done_interrupt = 0
