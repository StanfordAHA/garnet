from kratos import Generator, always_ff, always_comb, posedge, const, clog2, resize
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen


class GlbPcfgDma(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_pcfg_dma")
        self._params = _params
        self.header = GlbHeader(self._params)
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.cgra_cfg_pcfg = self.output("cgra_cfg_pcfg", self.header.cgra_cfg_t)

        self.rdrq_packet_dma2bank = self.output("rdrq_packet_dma2bank", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2ring = self.output("rdrq_packet_dma2ring", self.header.rdrq_packet_t)
        self.rdrs_packet_bank2dma = self.input("rdrs_packet_bank2dma", self.header.rdrs_packet_t)
        self.rdrs_packet_ring2dma = self.input("rdrs_packet_ring2dma", self.header.rdrs_packet_t)

        self.cfg_pcfg_tile_connected_prev = self.input("cfg_pcfg_tile_connected_prev", 1)
        self.cfg_pcfg_tile_connected_next = self.input("cfg_pcfg_tile_connected_next", 1)
        self.cfg_pcfg_dma_ctrl_mode = self.input("cfg_pcfg_dma_ctrl_mode", 1)
        self.cfg_pcfg_dma_ctrl_relocation_value = self.input(
            "cfg_pcfg_dma_ctrl_relocation_value", self._params.cgra_cfg_addr_width // 2)
        self.cfg_pcfg_dma_ctrl_relocation_is_msb = self.input("cfg_pcfg_dma_ctrl_relocation_is_msb", 1)
        self.cfg_pcfg_dma_header = self.input("cfg_pcfg_dma_header", self.header.cfg_pcfg_dma_header_t)
        self.cfg_pcfg_network_latency = self.input("cfg_pcfg_network_latency", self._params.latency_width)

        self.pcfg_dma_start_pulse = self.input("pcfg_dma_start_pulse", 1)
        self.pcfg_dma_done_interrupt = self.output("pcfg_dma_done_interrupt", 1)

        self.clk_en_dma2bank = self.output("clk_en_dma2bank", 1)

        # localparam
        self.bank_data_byte_offset = self._params.bank_strb_width

        # local variables
        self.rdrq_packet_dma2bank_w = self.var("rdrq_packet_dma2bank_w", self.header.rdrq_packet_t)
        self.rdrq_packet_dma2ring_w = self.var("rdrq_packet_dma2ring_w", self.header.rdrq_packet_t)
        self.rdrs_packet = self.var("rdrs_packet", self.header.rdrs_packet_t)
        self.pcfg_done_pulse = self.var("pcfg_done_pulse", 1)
        self.pcfg_done_pulse_last = self.var("pcfg_done_pulse_last", 1)
        self.is_running_r = self.var("is_running_r", 1)
        self.start_pulse_r = self.var("start_pulse_r", 1)
        self.done_pulse_r = self.var("done_pulse_r", 1)
        self.num_cfg_cnt_r = self.var("num_cfg_cnt_r", self._params.max_num_cfg_width)
        self.num_cfg_cnt_next = self.var("num_cfg_cnt_next", self._params.max_num_cfg_width)
        self.addr_r = self.var("addr_r", self._params.glb_addr_width)
        self.addr_next = self.var("addr_next", self._params.glb_addr_width)
        self.rdrq_packet_rd_en_r = self.var("rdrq_packet_rd_en_r", 1)
        self.rdrq_packet_rd_en_next = self.var("rdrq_packet_rd_en_next", 1)
        self.rdrq_packet_rd_addr_r = self.var("rdrq_packet_rd_addr_r", self._params.glb_addr_width)
        self.rdrq_packet_rd_addr_next = self.var("rdrq_packet_rd_addr_next", self._params.glb_addr_width)
        self.rdrs_packet_rd_data_r = self.var("rdrs_packet_rd_data_r", self._params.bank_data_width)
        self.rdrs_packet_rd_data_valid_r = self.var("rdrs_packet_rd_data_valid_r", 1)

        # Add always statements
        self.add_always(self.start_pulse_ff)
        self.add_always(self.done_pulse_ff)
        self.add_always(self.is_running_ff)
        self.add_always(self.adgn_logic)
        self.add_always(self.adgn_ff)
        self.add_always(self.rdrq_packet_counter)
        self.add_always(self.rdrq_packet_ff)
        self.add_always(self.rdrs_packet_ff)
        self.add_always(self.rdrq_packet_logic)
        self.add_always(self.rdrs_packet_logic)
        self.add_always(self.cgra_cfg_output_logic)
        self.add_done_pulse_pipeline()
        self.add_done_pulse_last_pipeline()
        self.add_always(self.interrupt_ff)
        self.add_dma2bank_clk_en()

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def start_pulse_ff(self):
        if self.reset:
            self.start_pulse_r = 0
        elif ((self.cfg_pcfg_dma_ctrl_mode == 1) & (~self.is_running_r) & (self.pcfg_dma_start_pulse)):
            self.start_pulse_r = 1
        else:
            self.start_pulse_r = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def done_pulse_ff(self):
        if self.reset:
            self.done_pulse_r = 0
        elif ((self.is_running_r) & (self.num_cfg_cnt_r == 0)):
            self.done_pulse_r = 1
        else:
            self.done_pulse_r = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def is_running_ff(self):
        if self.reset:
            self.is_running_r = 0
        elif self.start_pulse_r:
            self.is_running_r = 1
        elif ((self.is_running_r == 1) & (self.num_cfg_cnt_r == 0)):
            self.is_running_r = 0

    @always_comb
    def adgn_logic(self):
        if self.start_pulse_r:
            self.num_cfg_cnt_next = self.cfg_pcfg_dma_header['num_cfg']
            self.addr_next = self.cfg_pcfg_dma_header['start_addr']
        elif ((self.is_running_r == 1) & (self.num_cfg_cnt_r > 0)):
            self.num_cfg_cnt_next = self.num_cfg_cnt_r - 1
            self.addr_next = self.addr_r + self.bank_data_byte_offset
        else:
            self.num_cfg_cnt_next = 0
            self.addr_next = 0

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def adgn_ff(self):
        if self.reset:
            self.num_cfg_cnt_r = 0
            self.addr_r = 0
        else:
            self.num_cfg_cnt_r = self.num_cfg_cnt_next
            self.addr_r = self.addr_next

    @always_comb
    def rdrq_packet_counter(self):
        if (self.is_running_r & (self.num_cfg_cnt_r > 0)):
            self.rdrq_packet_rd_en_next = 1
            self.rdrq_packet_rd_addr_next = self.addr_r
        else:
            self.rdrq_packet_rd_en_next = 0
            self.rdrq_packet_rd_addr_next = 0

    @always_comb
    def rdrq_packet_logic(self):
        if self.cfg_pcfg_tile_connected_next | self.cfg_pcfg_tile_connected_prev:
            self.rdrq_packet_dma2ring_w['rd_en'] = self.rdrq_packet_rd_en_next
            self.rdrq_packet_dma2ring_w['rd_addr'] = self.rdrq_packet_rd_addr_next
            self.rdrq_packet_dma2bank_w['rd_en'] = 0
            self.rdrq_packet_dma2bank_w['rd_addr'] = 0
        else:
            self.rdrq_packet_dma2ring_w['rd_en'] = 0
            self.rdrq_packet_dma2ring_w['rd_addr'] = 0
            self.rdrq_packet_dma2bank_w['rd_en'] = self.rdrq_packet_rd_en_next
            self.rdrq_packet_dma2bank_w['rd_addr'] = self.rdrq_packet_rd_addr_next

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrq_packet_ff(self):
        if self.reset:
            self.rdrq_packet_dma2ring = 0
            self.rdrq_packet_dma2bank = 0
        else:
            self.rdrq_packet_dma2ring = self.rdrq_packet_dma2ring_w
            self.rdrq_packet_dma2bank = self.rdrq_packet_dma2bank_w

    def add_dma2bank_clk_en(self):
        self.clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_rd_delay + self._params.rd_clk_en_margin)
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
        if self.cfg_pcfg_tile_connected_next | self.cfg_pcfg_tile_connected_prev:
            self.rdrs_packet = self.rdrs_packet_ring2dma
        else:
            self.rdrs_packet = self.rdrs_packet_bank2dma

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def rdrs_packet_ff(self):
        if self.reset:
            self.rdrs_packet_rd_data_r = 0
            self.rdrs_packet_rd_data_valid_r = 0
        elif self.rdrs_packet['rd_data_valid']:
            self.rdrs_packet_rd_data_r = self.rdrs_packet['rd_data']
            self.rdrs_packet_rd_data_valid_r = 1
        else:
            self.rdrs_packet_rd_data_r = 0
            self.rdrs_packet_rd_data_valid_r = 0

    @always_comb
    def cgra_cfg_output_logic(self):
        self.cgra_cfg_pcfg['rd_en'] = 0
        self.cgra_cfg_pcfg['wr_en'] = self.rdrs_packet_rd_data_valid_r
        self.cgra_cfg_pcfg['data'] = self.rdrs_packet_rd_data_r[self._params.cgra_cfg_data_width - 1, 0]
        # bitstream relocation
        if self.cfg_pcfg_dma_ctrl_relocation_is_msb:
            self.cgra_cfg_pcfg['addr'] = (self.rdrs_packet_rd_data_r[self._params.cgra_cfg_data_width
                                                                     + self._params.cgra_cfg_addr_width - 1,
                                                                     self._params.cgra_cfg_data_width]
                                          + (self.cfg_pcfg_dma_ctrl_relocation_value
                                             << (self._params.cgra_cfg_addr_width // 2)))
        else:
            self.cgra_cfg_pcfg['addr'] = (self.rdrs_packet_rd_data_r[self._params.cgra_cfg_data_width
                                                                     + self._params.cgra_cfg_addr_width - 1,
                                                                     self._params.cgra_cfg_data_width]
                                          + self.cfg_pcfg_dma_ctrl_relocation_value)

    def add_done_pulse_pipeline(self):
        maximum_latency = (3 * self._params.num_glb_tiles
                           + self._params.chain_latency_overhead + self._params.tile2sram_rd_delay)
        latency_width = clog2(maximum_latency)
        self.done_pulse_d_arr = self.var("done_pulse_d_arr", 1, size=maximum_latency, explicit_array=True)
        self.done_pulse_pipeline = Pipeline(width=1,
                                            depth=maximum_latency,
                                            flatten_output=True)
        self.add_child("done_pulse_pipeline",
                       self.done_pulse_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.done_pulse_r,
                       out_=self.done_pulse_d_arr)

        self.wire(self.pcfg_done_pulse,
                  self.done_pulse_d_arr[resize(self.cfg_pcfg_network_latency, latency_width)
                                        + self._params.tile2sram_rd_delay
                                        + self._params.num_glb_tiles])

    def add_done_pulse_last_pipeline(self):
        self.interrupt_last_pipeline = Pipeline(width=1, depth=self._params.interrupt_cnt)
        self.add_child("pcfg_dma_interrupt_pipeline",
                       self.interrupt_last_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.pcfg_done_pulse,
                       out_=self.pcfg_done_pulse_last)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def interrupt_ff(self):
        if self.reset:
            self.pcfg_dma_done_interrupt = 0
        else:
            if self.pcfg_done_pulse:
                self.pcfg_dma_done_interrupt = 1
            elif self.pcfg_done_pulse_last:
                self.pcfg_dma_done_interrupt = 0
