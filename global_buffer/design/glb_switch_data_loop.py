from kratos import Generator, always_ff, always_comb, posedge, concat, const, clog2, resize
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_tile_ifc import GlbTileInterface
from global_buffer.design.glb_tile_data_loop_ifc import GlbTileDataLoopInterface
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen
import os


class GlbSwitchDataLoop(Generator):
    def __init__(self, _params: GlobalBufferParams, ifc: GlbTileDataLoopInterface, wr_channel=True, rd_channel=True, num_tracks=1):
        name = "glb_switch_data_loop"
        if wr_channel:
            name += "_WR"
        if rd_channel:
            name += "_RD"
        super().__init__(name)

        self.wr_channel = wr_channel
        self.rd_channel = rd_channel
        assert self.wr_channel is True or self.rd_channel is True

        self._params = _params
        self.header = GlbHeader(self._params)
        self.mclk = self.clock("mclk")
        self.gclk = self.clock("gclk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)
        self.num_tracks = num_tracks

        self.ifc = ifc
        self.addr_width = self.ifc.addr_width
        self.data_width = self.ifc.data_width
        # It only works when data_width of interface is same as or half of the bank_data_width
        assert ((self.data_width == self._params.bank_data_width)
                | (self.data_width * 2 == self._params.bank_data_width))

        self.bank_lsb_data_width = self.data_width
        self.bank_msb_data_width = self._params.bank_data_width - self.data_width

        # port to switch
        self.clk_en_sw2bank = self.output("clk_en_sw2bank", 1)
        if self.wr_channel:
            self.wr_packet = self.output("wr_packet", self.header.wr_packet_t)
        
        if self.rd_channel:
            self.rdrq_packet = self.output("rdrq_packet", self.header.mu_rdrq_packet_t)
            self.rdrs_packet = self.input("rdrs_packet", self.header.rdrs_packet_t)

        # config port
        self.if_est_m = self.interface(self.ifc.master, "if_est_m", is_port=True)
        self.if_wst_s = self.interface(self.ifc.slave, "if_wst_s", is_port=True)

        # local variables
        self.if_wst_s_wr_clk_en_d = self.var("if_wst_s_wr_clk_en_d", 1)
        self.if_wst_s_rd_clk_en_d = self.var("if_wst_s_rd_clk_en_d", 1)
        self.if_est_m_wr_clk_en_sel_first_cycle = self.var("if_est_m_wr_clk_en_sel_first_cycle", 1)
        self.if_est_m_rd_clk_en_sel_first_cycle = self.var("if_est_m_rd_clk_en_sel_first_cycle", 1)
        self.if_est_m_wr_clk_en_sel_latch = self.var("if_est_m_wr_clk_en_sel_latch", 1)
        self.if_est_m_rd_clk_en_sel_latch = self.var("if_est_m_rd_clk_en_sel_latch", 1)
        self.if_est_m_wr_clk_en_sel = self.var("if_est_m_wr_clk_en_sel", 1)
        self.if_est_m_rd_clk_en_sel = self.var("if_est_m_rd_clk_en_sel", 1)
        self.clk_en_wst_s_d = self.var("clk_en_wst_s_d", 1)
        self.clk_en_est_m = self.var("clk_en_est_m", 1)
        self.if_est_m_wr_en_w = self.var("if_est_m_wr_en_w", 1)
        self.if_est_m_wr_addr_w = self.var("if_est_m_wr_addr_w", self.addr_width)
        self.if_est_m_wr_data_w = self.var("if_est_m_wr_data_w", self.data_width)
        self.if_est_m_wr_strb_w = self.var("if_est_m_wr_strb_w", self.data_width // 8)
        self.if_est_m_rd_en_w = self.var("if_est_m_rd_en_w", 1)
        self.if_est_m_sub_packet_idx_w = self.var("if_est_m_sub_packet_idx_w", clog2(self._params.mu_word_num_tiles))
        self.if_est_m_rd_addr_w = self.var("if_est_m_rd_addr_w", self.addr_width)
        self.bank_wr_en = self.var("bank_wr_en", 1)
        self.bank_wr_strb = self.var("bank_wr_strb", self._params.bank_strb_width)
        self.bank_wr_addr = self.var("bank_wr_addr", self._params.glb_addr_width)
        self.bank_wr_data = self.var("bank_wr_data", self._params.bank_data_width)
        self.bank_rd_en = self.var("bank_rd_en", 1)
        self.bank_rd_addr = self.var("bank_rd_addr", self._params.glb_addr_width)
        self.bank_sub_packet_idx = self.var("bank_sub_packet_idx", clog2(self._params.mu_word_num_tiles))
        self.sub_packet_idx_d = self.var("sub_packet_idx_d", clog2(self._params.mu_word_num_tiles))
        self.rd_data_e2w_valid_w = self.var("rd_data_e2w_valid_w", 1, size=self.num_tracks, packed=True)
        self.rd_data_e2w_w = self.var("rd_data_e2w_w", width=self.data_width, size =self.num_tracks, packed=True)
        self.rd_data_w2e_valid_w = self.var("rd_data_w2e_valid_w", 1, size=self.num_tracks, packed=True)
        self.rd_data_w2e_w = self.var("rd_data_w2e_w", width=self.data_width, size =self.num_tracks, packed=True)

        self.wr_tile_id_match = self.var("wr_tile_id_match", 1)
        self.rd_tile_id_match = self.var("rd_tile_id_match", 1)
        self.rd_cycle = self.var("rd_cycle", 1)
        self.last_sub_packet = self.var("last_sub_packet", 1)

        # local pararmeters
        self.tile_id_lsb = self._params.bank_addr_width + self._params.bank_sel_addr_width
        self.tile_id_msb = self.tile_id_lsb + self._params.tile_sel_addr_width - 1
        
        if self.rd_channel and (self.data_width != self._params.bank_data_width):
            self.add_bank_rd_addr_sel_pipeline()
        self.add_always(self.tile_id_match)
        if self.wr_channel:
            self.add_always(self.wr_logic, is_partial=(self.data_width != self._params.bank_data_width))
        if self.rd_channel: 
            self.add_always(self.rdrq_logic)
            self.add_always(self.rdrs_logic_w2e, is_partial=(self.data_width != self._params.bank_data_width))
            self.add_always(self.rd_data_logic_e2w)
        self.add_always(self.pipeline)
        self.add_always(self.clk_en_pipeline)
        self.add_always(self.est_m_clk_en_sel_first_cycle_comb)
        if self.wr_channel:
            self.add_always(self.est_m_wr_clk_en_sel_latch)
        if self.rd_channel: 
            self.add_always(self.est_m_rd_clk_en_sel_latch)
        self.add_always(self.est_m_clk_en_sel_comb)
        if self.wr_channel:
            self.add_always(self.est_m_wr_clk_en_mux)
        if self.rd_channel:
            self.add_always(self.est_m_rd_clk_en_mux)
        self.add_sw2bank_clk_en()
        if self.rd_channel:
            self.add_always(self.mu_sub_packet_logic)
            self.add_sub_packet_idx_pipeline()

    @always_comb
    def tile_id_match(self):
        if self.wr_channel:
            self.wr_tile_id_match = self.glb_tile_id == self.if_wst_s.wr_addr[self.tile_id_msb, self.tile_id_lsb]
        if self.rd_channel:
            self.rd_tile_id_match = self.glb_tile_id == self.if_wst_s.rd_addr[self.tile_id_msb, self.tile_id_lsb]


    def add_sub_packet_idx_pipeline(self):
        # ADD + 1 for the if_wst_s_rd_addr -> bank_rd_addr 1 cycle delay introduced by this module (pipeline at bottom of file)
        self.pipeline_sub_packet_idx = Pipeline(width=clog2(self._params.mu_word_num_tiles),
                                       depth=(self._params.sram_macro_read_latency + self._params.glb_bank2sw_pipeline_depth + 1))
        self.add_child("pipeline_sub_packet_idx",
                       self.pipeline_sub_packet_idx,
                       # TODO: Figure out if this should be mclk or gclk. Using mclk for now. 
                       clk=self.mclk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.if_wst_s.sub_packet_idx,
                       out_=self.sub_packet_idx_d)
            

    @always_comb
    def mu_sub_packet_logic(self):
        self.rd_cycle = self.rd_tile_id_match | (self.if_wst_s.sub_packet_idx != 0)
        self.last_sub_packet = self.rd_cycle & (self.if_wst_s.sub_packet_idx == resize(self._params.mu_word_num_tiles - 1, clog2(self._params.mu_word_num_tiles)))

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def clk_en_pipeline(self):
        if self.reset:
            if self.wr_channel:
                self.if_wst_s_wr_clk_en_d = 0
            if self.rd_channel:
                self.if_wst_s_rd_clk_en_d = 0
        else:
            if self.wr_channel:
                self.if_wst_s_wr_clk_en_d = self.if_wst_s.wr_clk_en
            if self.rd_channel:
                self.if_wst_s_rd_clk_en_d = self.if_wst_s.rd_clk_en

    @always_comb
    def est_m_clk_en_sel_first_cycle_comb(self):
        if self.wr_channel:
            self.if_est_m_wr_clk_en_sel_first_cycle = self.if_wst_s.wr_en & (~self.wr_tile_id_match)
        if self.rd_channel:
            # self.if_est_m_rd_clk_en_sel_first_cycle = self.if_wst_s.rd_en & (~self.rd_tile_id_match)

            # TODO: Decide which of the below two implementations to use. First one might be fine b/c the bank gets the correct clk_en at the correct time anyway 
            # self.if_est_m_rd_clk_en_sel_first_cycle = self.if_wst_s.rd_en & (~self.rd_cycle)
            self.if_est_m_rd_clk_en_sel_first_cycle = self.if_wst_s.rd_en & (~self.last_sub_packet)

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def est_m_wr_clk_en_sel_latch(self):
        if self.reset:
            self.if_est_m_wr_clk_en_sel_latch = 0
        else:
            if self.if_wst_s.wr_en == 1:
                # If tile id matches, it does not feedthrough clk_en to the east
                if self.wr_tile_id_match:
                    self.if_est_m_wr_clk_en_sel_latch = 0
                else:
                    self.if_est_m_wr_clk_en_sel_latch = 1
            else:
                if self.if_wst_s.wr_clk_en == 0:
                    self.if_est_m_wr_clk_en_sel_latch = 0

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def est_m_rd_clk_en_sel_latch(self):
        if self.reset:
            self.if_est_m_rd_clk_en_sel_latch = 0
        else:
            if self.if_wst_s.rd_en == 1:
                # If reading the last sub-packet, it does not feedthrough clk_en to the east 
                # if self.rd_tile_id_match:
                if self.last_sub_packet:
                    self.if_est_m_rd_clk_en_sel_latch = 0
                else:
                    self.if_est_m_rd_clk_en_sel_latch = 1
            else:
                if self.if_wst_s.rd_clk_en == 0:
                    self.if_est_m_rd_clk_en_sel_latch = 0

    @always_comb
    def est_m_clk_en_sel_comb(self):
        if self.wr_channel:
            self.if_est_m_wr_clk_en_sel = (
                self.if_est_m_wr_clk_en_sel_first_cycle | self.if_est_m_wr_clk_en_sel_latch)
        if self.rd_channel:
            self.if_est_m_rd_clk_en_sel = (
                self.if_est_m_rd_clk_en_sel_first_cycle | self.if_est_m_rd_clk_en_sel_latch)

    @always_comb
    def est_m_wr_clk_en_mux(self):
        if self.if_est_m_wr_clk_en_sel:
            self.if_est_m.wr_clk_en = self.if_wst_s_wr_clk_en_d
        else:
            self.if_est_m.wr_clk_en = 0

    @always_comb
    def est_m_rd_clk_en_mux(self):
        if self.if_est_m_rd_clk_en_sel:
            self.if_est_m.rd_clk_en = self.if_wst_s_rd_clk_en_d
        else:
            self.if_est_m.rd_clk_en = 0

    def add_sw2bank_clk_en(self):
        if self.wr_channel:
            self.wr_clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_wr_delay + self._params.wr_clk_en_margin)
            if os.getenv('WHICH_SOC') == "amber":
                pass
            else:
                self.wr_clk_en_gen.p_cnt.value = self._params.tile2sram_wr_delay + self._params.wr_clk_en_margin
            self.sw2bank_wr_clk_en = self.var("sw2bank_wr_clk_en", 1)
            self.add_child("sw2bank_wr_clk_en_gen",
                        self.wr_clk_en_gen,
                        clk=self.mclk,
                        reset=self.reset,
                        enable=(self.if_wst_s.wr_en & self.wr_tile_id_match),
                        clk_en=self.sw2bank_wr_clk_en
                        )
            
        if self.rd_channel:
            self.rd_clk_en_gen = GlbClkEnGen(cnt=self._params.tile2sram_rd_delay + self._params.rd_clk_en_margin)
            if os.getenv('WHICH_SOC') == "amber":
                pass
            else:
                self.rd_clk_en_gen.p_cnt.value = self._params.tile2sram_rd_delay + self._params.rd_clk_en_margin
            self.sw2bank_rd_clk_en = self.var("sw2bank_rd_clk_en", 1)
            self.add_child("sw2bank_rd_clk_en_gen",
                        self.rd_clk_en_gen,
                        clk=self.mclk,
                        reset=self.reset,
                        # enable=(self.if_wst_s.rd_en & self.rd_tile_id_match),
                        enable=(self.if_wst_s.rd_en & self.rd_cycle),
                        clk_en=self.sw2bank_rd_clk_en
                        )

        if self.wr_channel and self.rd_channel:
            self.wire(self.clk_en_sw2bank, self.sw2bank_wr_clk_en | self.sw2bank_rd_clk_en)
        elif self.wr_channel:
            self.wire(self.clk_en_sw2bank, self.sw2bank_wr_clk_en)
        elif self.rd_channel:
            self.wire(self.clk_en_sw2bank, self.sw2bank_rd_clk_en)

    @always_comb
    def wr_logic(self, is_partial: bool):
        if self.if_wst_s.wr_en:
            if self.wr_tile_id_match:
                # Do not feedthrough to the east
                self.if_est_m_wr_en_w = 0
                self.if_est_m_wr_addr_w = 0
                self.if_est_m_wr_data_w = 0
                if self.ifc.is_strb is True:
                    self.if_est_m_wr_strb_w = 0
                # Send wr packet to switch
                if is_partial is True:
                    if self.if_wst_s.wr_addr[self._params.bank_byte_offset - 1] == 0:
                        self.bank_wr_en = 1
                        self.bank_wr_addr = self.if_wst_s.wr_addr
                        self.bank_wr_data = concat(const(0, self.bank_msb_data_width), self.if_wst_s.wr_data)
                        self.bank_wr_strb = concat(const(0, self.bank_msb_data_width // 8),
                                                   const(2**(self.bank_lsb_data_width // 8) - 1,
                                                         self.bank_lsb_data_width // 8))
                    else:
                        self.bank_wr_en = 1
                        self.bank_wr_addr = self.if_wst_s.wr_addr
                        self.bank_wr_data = concat(
                            self.if_wst_s.wr_data[self.bank_msb_data_width - 1, 0],
                            const(0, self.bank_lsb_data_width))
                        self.bank_wr_strb = concat(const(2**(self.bank_msb_data_width // 8) - 1,
                                                         self.bank_msb_data_width // 8),
                                                   const(0, self.bank_lsb_data_width // 8))
                else:
                    self.bank_wr_en = 1
                    self.bank_wr_addr = self.if_wst_s.wr_addr
                    self.bank_wr_data = self.if_wst_s.wr_data
                    self.bank_wr_strb = self.if_wst_s.wr_strb
            else:
                # Feedthrough to the east
                self.if_est_m_wr_en_w = self.if_wst_s.wr_en
                self.if_est_m_wr_addr_w = self.if_wst_s.wr_addr
                self.if_est_m_wr_data_w = self.if_wst_s.wr_data
                if self.ifc.is_strb is True:
                    self.if_est_m_wr_strb_w = self.if_wst_s.wr_strb
                # Gate packet to switch
                self.bank_wr_en = 0
                self.bank_wr_addr = 0
                self.bank_wr_data = 0
                self.bank_wr_strb = 0
        else:
            self.if_est_m_wr_en_w = 0
            self.if_est_m_wr_addr_w = 0
            self.if_est_m_wr_data_w = 0
            if self.ifc.is_strb is True:
                self.if_est_m_wr_strb_w = 0
            self.bank_wr_en = 0
            self.bank_wr_addr = 0
            self.bank_wr_data = 0
            self.bank_wr_strb = 0

    @ always_comb
    def rdrq_logic(self):
        if self.if_wst_s.rd_en:

            # CONSUME and DON'T FEEDTHROUGH
            if self.last_sub_packet:
                # Do not feedthrough to the east
                self.if_est_m_rd_en_w = 0
                self.if_est_m_sub_packet_idx_w = 0
                self.if_est_m_rd_addr_w = 0
                # Send rdrq packet to switch
                self.bank_rd_en = 1
                self.bank_rd_addr = self.if_wst_s.rd_addr
                self.bank_sub_packet_idx = self.if_wst_s.sub_packet_idx

            # CONSUME and FEEDTHROUGH
            elif self.rd_cycle:
                # Feedthrough to the east
                self.if_est_m_rd_en_w = self.if_wst_s.rd_en
                # INCREMENT sub_packet counter             
                self.if_est_m_sub_packet_idx_w = self.if_wst_s.sub_packet_idx + 1
                self.if_est_m_rd_addr_w = self.if_wst_s.rd_addr
                # Send rdrq packet to switch
                self.bank_rd_en = 1
                self.bank_rd_addr = self.if_wst_s.rd_addr
                self.bank_sub_packet_idx = self.if_wst_s.sub_packet_idx

            # DON'T CONSUME and FEEDTHROUGH
            else:
                # Feedthrough to the east
                self.if_est_m_rd_en_w = self.if_wst_s.rd_en
                self.if_est_m_sub_packet_idx_w = self.if_wst_s.sub_packet_idx
                self.if_est_m_rd_addr_w = self.if_wst_s.rd_addr
                self.bank_rd_en = 0
                self.bank_rd_addr = 0
                self.bank_sub_packet_idx = 0

        else:
            self.if_est_m_rd_en_w = 0
            self.if_est_m_sub_packet_idx_w = 0
            self.if_est_m_rd_addr_w = 0
            self.bank_rd_en = 0
            self.bank_rd_addr = 0
            self.bank_sub_packet_idx = 0

    @ always_comb
    def rdrs_logic_w2e(self, is_partial: bool):
        self.rd_data_w2e_w = 0
        self.rd_data_w2e_valid_w = 0
        for sub_packet in range(self.num_tracks):
            if (sub_packet == self.sub_packet_idx_d) & (self.rdrs_packet['rd_data_valid'] == 1):
                    if is_partial:
                        if self.bank_rd_addr_sel_d == 0:
                            self.rd_data_w2e_w[sub_packet] = self.rdrs_packet['rd_data'][self.data_width - 1, 0]
                        else:
                            self.rd_data_w2e_w[sub_packet] = self.rdrs_packet['rd_data'][self.data_width * 2 - 1, self.data_width]
                        self.rd_data_w2e_valid_w[sub_packet] = 1
                    else:
                        self.rd_data_w2e_w[sub_packet] = self.rdrs_packet['rd_data']
                        self.rd_data_w2e_valid_w[sub_packet]= 1
            elif self.if_wst_s.rd_data_w2e_valid[sub_packet] == 1:
                self.rd_data_w2e_w[sub_packet] = self.if_wst_s.rd_data_w2e[sub_packet]
                self.rd_data_w2e_valid_w[sub_packet] = 1

    @ always_comb
    def rd_data_logic_e2w(self):
        self.rd_data_e2w_w = self.if_est_m.rd_data_e2w
        self.rd_data_e2w_valid_w = self.if_est_m.rd_data_e2w_valid

    def add_bank_rd_addr_sel_pipeline(self):
        self.bank_rd_latency = self._params.tile2sram_rd_delay + 1  # rdrq latency
        self.bank_rd_addr_sel_d = self.var("bank_rd_addr_sel_d", 1)
        self.bank_rd_addr_sel_pipeline = Pipeline(width=1, depth=self.bank_rd_latency)
        self.add_child("bank_rd_addr_sel_pipeline",
                       self.bank_rd_addr_sel_pipeline,
                       clk=self.gclk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.bank_rd_addr[self._params.bank_byte_offset - 1],
                       out_=self.bank_rd_addr_sel_d)


    # TODO: Potentially change this gclk to mclk for now till I figure out how clock gating will work with the loop 
    # @ always_ff((posedge, "gclk"), (posedge, "reset"))
    @ always_ff((posedge, "mclk"), (posedge, "reset"))
    def pipeline(self):
        if self.reset:
            if self.wr_channel:
                self.if_est_m.wr_en = 0
                if self.ifc.is_strb is True:
                    self.if_est_m.wr_strb = 0
                self.if_est_m.wr_addr = 0
                self.if_est_m.wr_data = 0

            if self.rd_channel:    
                self.if_est_m.rd_en = 0
                self.if_est_m.sub_packet_idx = 0
                self.if_est_m.rd_addr = 0
                self.if_wst_s.rd_data_e2w = 0
                self.if_wst_s.rd_data_e2w_valid = 0
                self.if_est_m.rd_data_w2e = 0
                self.if_est_m.rd_data_w2e_valid = 0
    

            if self.wr_channel:
                self.wr_packet['wr_en'] = 0
                self.wr_packet['wr_strb'] = 0
                self.wr_packet['wr_addr'] = 0
                self.wr_packet['wr_data'] = 0

            if self.rd_channel:
                self.rdrq_packet['rd_en'] = 0
                self.rdrq_packet['rd_addr'] = 0
                self.rdrq_packet['sub_packet_idx'] = 0
        else:
            if self.wr_channel:
                self.if_est_m.wr_en = self.if_est_m_wr_en_w
                if self.ifc.is_strb is True:
                    self.if_est_m.wr_strb = self.if_est_m_wr_strb_w
                self.if_est_m.wr_addr = self.if_est_m_wr_addr_w
                self.if_est_m.wr_data = self.if_est_m_wr_data_w

            if self.rd_channel:
                self.if_est_m.rd_en = self.if_est_m_rd_en_w
                self.if_est_m.sub_packet_idx = self.if_est_m_sub_packet_idx_w
                self.if_est_m.rd_addr = self.if_est_m_rd_addr_w
                self.if_wst_s.rd_data_e2w = self.rd_data_e2w_w
                self.if_wst_s.rd_data_e2w_valid = self.rd_data_e2w_valid_w
                self.if_est_m.rd_data_w2e = self.rd_data_w2e_w
                self.if_est_m.rd_data_w2e_valid = self.rd_data_w2e_valid_w

            if self.wr_channel:
                self.wr_packet['wr_en'] = self.bank_wr_en
                self.wr_packet['wr_strb'] = self.bank_wr_strb
                self.wr_packet['wr_addr'] = self.bank_wr_addr
                self.wr_packet['wr_data'] = self.bank_wr_data

            if self.rd_channel:
                self.rdrq_packet['rd_en'] = self.bank_rd_en
                self.rdrq_packet['rd_addr'] = self.bank_rd_addr
                self.rdrq_packet['sub_packet_idx'] = self.bank_sub_packet_idx
