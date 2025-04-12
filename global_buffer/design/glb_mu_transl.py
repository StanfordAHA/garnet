from kratos import Generator, always_comb, always_ff, clog2, clock_en, const, posedge, ternary, concat
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.fifo import FIFO
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.mux import Mux


class GlbMUTransl(Generator):
    def __init__(self, _params: GlobalBufferParams):
        self._params = _params
        super().__init__(f"glb_mu_transl")
      
        # Clock and Reset
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        # I/Os

        # Tileline request collateral
        self.addr_in = self.input("addr_in", self._params.mu_addr_width)
        self.rq_in_vld = self.input("rq_in_vld", 1)
        self.rq_in_rdy = self.output("rq_in_rdy", 1)
        self.size_in = self.input("size_in", self._params.mu_tl_num_burst_bits) # log2 (number of bytes requested)
        self.source_in = self.input("source_in", self._params.mu_tl_source_width)

        # Tilelink response collateral
        self.size_out = self.output("size_out", self._params.mu_tl_num_burst_bits)
        self.opcode_out = self.output("opcode_out", self._params.mu_tl_opcode_width)
        self.source_out = self.output("source_out", self._params.mu_tl_source_width)

        self.rd_data_out = self.output("rd_data_out", self._params.mu_word_width)
        self.resp_out_vld = self.output("resp_out_vld", 1)
        self.resp_out_rdy = self.input("resp_out_rdy", 1) 

        # To/From GLB
        self.addr2glb = self.output("addr2glb", self._params.glb_addr_width)
        self.rd_en2glb = self.output("rd_en2glb", 1)

        self.rd_data_in = self.input("rd_data_in", self._params.mu_word_width)
        self.rd_data_in_vld = self.input("rd_data_in_vld", 1)

        # Localparam
        self.num_tile_id_bits_in_mu_addr = self._params.tile_sel_addr_width - clog2(self._params.mu_word_num_tiles)
        self.addr_incr_value = pow(2, self._params.mu_word_byte_offset)
        self.num_glb_reqs_bitwidth = int(clog2(self._params.mu_rd_max_num_glb_reqs)) + 1
        self.byte_mask_bitwidth = clog2(self._params.mu_word_num_tiles) + self._params.bank_sel_addr_width + self._params.bank_byte_offset

        # Local vars
        self.glb_req_counter = self.var("glb_req_counter",self.num_glb_reqs_bitwidth)
        self.next_glb_req_counter = self.var("next_glb_req_counter",self.num_glb_reqs_bitwidth) 
        self.burst_addr_incr = self.var("burst_addr_incr", self._params.mu_addr_width)
        self.addr_to_adjuster = self.var("addr_to_adjuster", self._params.mu_addr_width)
        self.rd_en2glb_w = self.var("rd_en2glb_w", 1)
        self.addr_to_glb_w = self.var("addr_to_glb_w", self._params.glb_addr_width)
        self.num_glb_reqs = self.var("num_glb_reqs", self.num_glb_reqs_bitwidth)
        self.next_size_cached = self.var("next_size_cached", self._params.mu_tl_num_burst_bits)
        self.size_cached = self.var("size_cached", self._params.mu_tl_num_burst_bits)
        self.next_source_cached = self.var("next_source_cached", self._params.mu_tl_source_width)
        self.source_cached = self.var("source_cached", self._params.mu_tl_source_width)
        self.rd_data_in_masked = self.var("rd_data_in_masked", self._params.mu_word_width)
        self.selected_byte = self.var("selected_byte", 8)

        # Pipeline signals
        self.size_resp_pipeline_in = self.var("size_resp_pipeline_in", self._params.mu_tl_num_burst_bits)
        self.source_resp_pipeline_in = self.var("source_resp_pipeline_in", self._params.mu_tl_source_width)

        self.size_resp_pipeline_out = self.var("size_resp_pipeline_out", self._params.mu_tl_num_burst_bits)
        self.source_resp_pipeline_out = self.var("source_resp_pipeline_out", self._params.mu_tl_source_width)

        self.byte_mask_pipeline_in = self.var("byte_mask_pipeline_in", self.byte_mask_bitwidth)
        self.byte_mask_pipeline_out = self.var("byte_mask_pipeline_out", self.byte_mask_bitwidth)

        # FIFO signals
        self.addr_fifo_full = self.var("addr_fifo_full", 1)
        self.addr_fifo_empty = self.var("addr_fifo_empty", 1)
        self.addr_fifo_almost_full = self.var("addr_fifo_almost_full", 1)

        self.addr_fifo_out = self.var("addr_fifo_out", self._params.mu_addr_width)  
        self.addr_fifo_out_valid = self.var("addr_fifo_out_valid", 1)
        self.addr_fifo_pop = self.var("addr_fifo_pop", 1)
        self.data_out_fifo_full = self.var("data_out_fifo_full", 1)
        self.data_out_fifo_empty = self.var("data_out_fifo_empty", 1)
        self.data_out_fifo_almost_full = self.var("data_out_fifo_almost_full", 1)

        self.size_req_fifo_out = self.var("size_req_fifo_out", self._params.mu_tl_num_burst_bits)  
        self.source_req_fifo_out = self.var("source_req_fifo_out", self._params.mu_tl_source_width)

        self.rd_data_out_to_fifo = self.var("rd_data_out_to_fifo", self._params.mu_word_width)

        self.add_addr_in_fifo_logic()
        self.add_data_out_fifo_logic()
        self.add_size_in_fifo_logic()
        self.add_source_in_fifo_logic()
        self.add_size_out_fifo_logic()
        self.add_source_out_fifo_logic()
        self.add_size_out_pipeline()
        self.add_source_out_pipeline()
        self.add_byte_mask_pipeline()
        self.add_always(self.burst_addr_incr_ff)
        self.add_always(self.glb_req_counter_ff)
        self.add_always(self.size_cache_ff)
        self.add_always(self.source_cache_ff)
        self.add_always(self.output_logic)
        self.add_always(self.address_adjustment_logic)
        self.add_always(self.size_in_to_num_glb_reqs_logic)
        self.add_always(self.byte_mask_extraction_logic)
        self.add_always(self.byte_select_mux_logic)
        self.add_always(self.data_out_mux_logic)
        


        ###################
        # Begin read_req_fsm
        ###################

        # State definition
        self.read_req_fsm = self.add_fsm("read_req_seq", reset_high=True)
        READY = self.read_req_fsm.add_state("READY")
        BUSY = self.read_req_fsm.add_state("BUSY")
        self.read_req_fsm.set_start_state(READY)

        # Bind FSM outputs 
        self.read_req_fsm.output(self.addr_fifo_pop)
        self.read_req_fsm.output(self.rd_en2glb_w)    
        self.read_req_fsm.output(self.addr_to_adjuster)
        self.read_req_fsm.output(self.next_glb_req_counter)
        self.read_req_fsm.output(self.next_size_cached)
        self.read_req_fsm.output(self.size_resp_pipeline_in)
        self.read_req_fsm.output(self.next_source_cached)
        self.read_req_fsm.output(self.source_resp_pipeline_in)
       
        # Next State Logic 
        # Next sate is busy if the address is valid and number of glb requests > 1 
        READY.next(BUSY, self.addr_fifo_out_valid & (self.num_glb_reqs[self.num_glb_reqs_bitwidth - 1, 1] != 0)) 
        READY.next(READY, None)

        BUSY.next(READY, self.glb_req_counter == 1)
        BUSY.next(BUSY, None)

        # FSM Output Logic
        READY.output(self.addr_fifo_pop, 1)
        READY.output(self.rd_en2glb_w, self.addr_fifo_out_valid)
        READY.output(self.addr_to_adjuster, self.addr_fifo_out)
        READY.output(self.next_glb_req_counter, self.num_glb_reqs - 1) 
        READY.output(self.next_size_cached, self.size_req_fifo_out)
        READY.output(self.size_resp_pipeline_in, self.size_req_fifo_out)
        READY.output(self.next_source_cached, self.source_req_fifo_out)
        READY.output(self.source_resp_pipeline_in, self.source_req_fifo_out)

        BUSY.output(self.addr_fifo_pop, 0)
        BUSY.output(self.rd_en2glb_w, 1)
        BUSY.output(self.addr_to_adjuster, self.burst_addr_incr)
        BUSY.output(self.next_glb_req_counter, self.glb_req_counter - 1) 
        BUSY.output(self.next_size_cached, self.size_cached)
        BUSY.output(self.size_resp_pipeline_in, self.size_cached)
        BUSY.output(self.next_source_cached, self.source_cached)
        BUSY.output(self.source_resp_pipeline_in, self.source_cached)
       
        # Realize FSM
        self.read_req_fsm.realize()

        ###################
        # End read_req_fsm
        ###################


    def add_addr_in_fifo_logic(self):
        # TODO: finalize the depth of this fifo in the parameters
        self.addr_fifo = FIFO(self._params.mu_addr_width, self._params.mu_tl_req_fifo_depth)
        self.add_child("addr_fifo",
                       self.addr_fifo,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                    #    flush=self.st_dma_start_pulse_r,
                        # TODO: Figure out what to put here for flush
                       flush=const(0, 1), 
                       data_in=self.addr_in,
                       data_out=self.addr_fifo_out,
                       push=self.rq_in_vld,
                       pop=self.addr_fifo_pop,
                       full=self.addr_fifo_full,
                       empty=self.addr_fifo_empty,
                       almost_full=self.addr_fifo_almost_full,
                       almost_full_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)),
                       almost_empty_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)))
        
        self.wire(self.rq_in_rdy, ~self.addr_fifo_full)
        self.wire(self.addr_fifo_out_valid, ~self.addr_fifo_empty)

    def add_size_in_fifo_logic(self):
        self.size_req_fifo = FIFO(self._params.mu_tl_num_burst_bits, self._params.mu_tl_req_fifo_depth)
        self.add_child("size_req_fifo",
                       self.size_req_fifo,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                    #    flush=self.st_dma_start_pulse_r,
                        # TODO: Figure out what to put here for flush
                       flush=const(0, 1), 
                       data_in=self.size_in,
                       data_out=self.size_req_fifo_out,
                       push=self.rq_in_vld,
                       pop=self.addr_fifo_pop,
                       almost_full_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)),
                       almost_empty_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)))
        
    def add_source_in_fifo_logic(self):
        self.source_req_fifo = FIFO(self._params.mu_tl_source_width, self._params.mu_tl_req_fifo_depth)
        self.add_child("source_req_fifo",
                        self.source_req_fifo,
                        clk=self.clk,
                        clk_en=const(1, 1),
                        reset=self.reset,
                    #    flush=self.st_dma_start_pulse_r,
                        # TODO: Figure out what to put here for flush
                        flush=const(0, 1), 
                        data_in=self.source_in,
                        data_out=self.source_req_fifo_out,
                        push=self.rq_in_vld,
                        pop=self.addr_fifo_pop,
                        almost_full_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)),
                        almost_empty_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)))  


    def add_size_out_pipeline(self):
        self.size_out_pipeline = Pipeline(width=self._params.mu_tl_num_burst_bits,
                                                   depth=self._params.mu_glb_rd_latency - 2, # -2 to remove both the input FIFO and output FIFO
                                                   flatten_output=False) 
        self.add_child("size_out_pipeline",
                       self.size_out_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.size_resp_pipeline_in,
                       out_=self.size_resp_pipeline_out)
        
    def add_source_out_pipeline(self):
        self.source_out_pipeline = Pipeline(width=self._params.mu_tl_source_width,
                                                   depth=self._params.mu_glb_rd_latency - 2, # -2 to remove both the input FIFO and output FIFO 
                                                   flatten_output=False) 
        self.add_child("source_out_pipeline",
                       self.source_out_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.source_resp_pipeline_in,
                       out_=self.source_resp_pipeline_out)    
        
    def add_byte_mask_pipeline(self):
        self.byte_mask_pipeline = Pipeline(width=self.byte_mask_bitwidth,
                                                   depth=self._params.mu_glb_rd_latency - 2, # -2 to remove both the input FIFO and output FIFO 
                                                   flatten_output=False) 
        self.add_child("byte_mask_pipeline",
                       self.byte_mask_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.byte_mask_pipeline_in,
                       out_=self.byte_mask_pipeline_out)    
        
    
    def add_data_out_fifo_logic(self):
        self.data_out_fifo = FIFO(self._params.mu_word_width, self._params.mu_tl_resp_fifo_depth)
        self.add_child("data_out_fifo",
                       self.data_out_fifo,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                    #    flush=self.st_dma_start_pulse_r,
                        # TODO: Figure out what to put here for flush
                       flush=const(0, 1), 
                       data_in=self.rd_data_out_to_fifo,
                       data_out=self.rd_data_out,
                       push=self.rd_data_in_vld,
                       pop=self.resp_out_rdy,
                       full=self.data_out_fifo_full,
                       empty=self.data_out_fifo_empty,
                       almost_full=self.data_out_fifo_almost_full,
                       almost_full_diff=const(2, clog2(self._params.mu_tl_resp_fifo_depth)),
                       almost_empty_diff=const(2, clog2(self._params.mu_tl_resp_fifo_depth)))
        
        self.wire(self.resp_out_vld, ~self.data_out_fifo_empty)    

    def add_size_out_fifo_logic(self):
        self.size_resp_fifo = FIFO(self._params.mu_tl_num_burst_bits, self._params.mu_tl_resp_fifo_depth)
        self.add_child("size_resp_fifo",
                       self.size_resp_fifo,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                    #    flush=self.st_dma_start_pulse_r,
                        # TODO: Figure out what to put here for flush
                       flush=const(0, 1), 
                       data_in=self.size_resp_pipeline_out,
                       data_out=self.size_out,
                       push=self.rd_data_in_vld,
                       pop=self.resp_out_rdy,
                       almost_full_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)),
                       almost_empty_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)))
        
    def add_source_out_fifo_logic(self):
        self.source_resp_fifo = FIFO(self._params.mu_tl_source_width, self._params.mu_tl_resp_fifo_depth)
        self.add_child("source_resp_fifo",
                        self.source_resp_fifo,
                        clk=self.clk,
                        clk_en=const(1, 1),
                        reset=self.reset,
                    #    flush=self.st_dma_start_pulse_r,
                        # TODO: Figure out what to put here for flush
                        flush=const(0, 1), 
                        data_in=self.source_resp_pipeline_out,
                        data_out=self.source_out,
                        push=self.rd_data_in_vld,
                        pop=self.resp_out_rdy,
                        almost_full_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)),
                        almost_empty_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)))  

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def glb_req_counter_ff(self):
        if self.reset:
            self.glb_req_counter = 0
        else:
            self.glb_req_counter = self.next_glb_req_counter 


    @always_ff((posedge, "clk"), (posedge, "reset"))
    def size_cache_ff(self):
        if self.reset:
            self.size_cached = 0
        else:
            self.size_cached = self.next_size_cached    

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def source_cache_ff(self):
        if self.reset:
            self.source_cached = 0
        else:
            self.source_cached = self.next_source_cached                 

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def burst_addr_incr_ff(self):
        if self.reset:
            self.burst_addr_incr = 0
        else:
            self.burst_addr_incr = self.addr_to_adjuster + self.addr_incr_value 

    @always_comb
    def size_in_to_num_glb_reqs_logic(self):
        # 2^7 = 128 bytes = 4 requests (MAXIMUM)
        if self.size_req_fifo_out == 7:
            self.num_glb_reqs = 4

        # 2^6 = 64 bytes = 2 requests    
        elif self.size_req_fifo_out == 6:
            self.num_glb_reqs = 2

        # Anything smaller only needs 1 request     
        else:
            self.num_glb_reqs = 1

    @always_comb
    def output_logic(self):
        self.addr2glb = self.addr_to_glb_w
        self.rd_en2glb = self.rd_en2glb_w
        self.opcode_out = const(self._params.mu_tl_rd_resp_opcode, self._params.mu_tl_opcode_width)

    # Adjusted address consists of 3 components:
    # 1. The tileID bits provided by MU, referring to a group of GLB tiles 
    # 2. Inserted 0s at MSBs of tileID, to refer to base tile of that group
    # 3. Inserted 0 for the bank ID
    # 4. Rest of address (ignoring addr[4] and addr[3]. These are the bits that are replaced by 0s above for tileID and bank ID)
    @always_comb
    def address_adjustment_logic(self):
        if self.num_tile_id_bits_in_mu_addr > 0:
            self.addr_to_glb_w = concat(self.addr_to_adjuster[self._params.mu_addr_width - 1, self._params.mu_addr_width - 1 - (self.num_tile_id_bits_in_mu_addr - 1)], 
                                                const(0, clog2(self._params.mu_word_num_tiles)),
                                                const(0, self._params.bank_sel_addr_width),
                                                self.addr_to_adjuster[self._params.mu_addr_width - 1 - (self.num_tile_id_bits_in_mu_addr), clog2(self._params.mu_word_num_tiles) + self._params.bank_sel_addr_width + self._params.bank_byte_offset],
                                                self.addr_to_adjuster[self._params.bank_byte_offset - 1, 0])
        else:
            self.addr_to_glb_w = concat(const(0, clog2(self._params.mu_word_num_tiles)),
                                                 const(0, self._params.bank_sel_addr_width),
                                                 self.addr_to_adjuster[self._params.mu_addr_width - 1 - (self.num_tile_id_bits_in_mu_addr), clog2(self._params.mu_word_num_tiles) + self._params.bank_sel_addr_width + self._params.bank_byte_offset],
                                                 self.addr_to_adjuster[self._params.bank_byte_offset - 1, 0])


    @always_comb
    def byte_mask_extraction_logic(self):
        self.byte_mask_pipeline_in = self.addr_to_adjuster[self.byte_mask_bitwidth - 1, 0]       


    # TODO: May need to pipeline this path for timing closure 
    @always_comb
    def byte_select_mux_logic(self):
        if self.byte_mask_pipeline_out == 0:
            self.selected_byte = self.rd_data_in[7, 0]
        elif self.byte_mask_pipeline_out == 1:
            self.selected_byte = self.rd_data_in[15, 8]
        elif self.byte_mask_pipeline_out == 2:
            self.selected_byte = self.rd_data_in[23, 16]
        elif self.byte_mask_pipeline_out == 3:
            self.selected_byte = self.rd_data_in[31, 24]
        elif self.byte_mask_pipeline_out == 4:
            self.selected_byte = self.rd_data_in[39, 32]
        elif self.byte_mask_pipeline_out == 5:
            self.selected_byte = self.rd_data_in[47, 40]
        elif self.byte_mask_pipeline_out == 6:
            self.selected_byte = self.rd_data_in[55, 48]
        elif self.byte_mask_pipeline_out == 7:
            self.selected_byte = self.rd_data_in[63, 56]
        elif self.byte_mask_pipeline_out == 8:
            self.selected_byte = self.rd_data_in[71, 64]
        elif self.byte_mask_pipeline_out == 9:
            self.selected_byte = self.rd_data_in[79, 72]
        elif self.byte_mask_pipeline_out == 10:
            self.selected_byte = self.rd_data_in[87, 80]
        elif self.byte_mask_pipeline_out == 11:
            self.selected_byte = self.rd_data_in[95, 88]
        elif self.byte_mask_pipeline_out == 12:
            self.selected_byte = self.rd_data_in[103, 96]
        elif self.byte_mask_pipeline_out == 13:
            self.selected_byte = self.rd_data_in[111, 104]
        elif self.byte_mask_pipeline_out == 14:
            self.selected_byte = self.rd_data_in[119, 112]
        elif self.byte_mask_pipeline_out == 15:
            self.selected_byte = self.rd_data_in[127, 120]
        elif self.byte_mask_pipeline_out == 16:
            self.selected_byte = self.rd_data_in[135, 128]
        elif self.byte_mask_pipeline_out == 17:
            self.selected_byte = self.rd_data_in[143, 136]
        elif self.byte_mask_pipeline_out == 18:
            self.selected_byte = self.rd_data_in[151, 144]
        elif self.byte_mask_pipeline_out == 19:
            self.selected_byte = self.rd_data_in[159, 152]
        elif self.byte_mask_pipeline_out == 20:
            self.selected_byte = self.rd_data_in[167, 160]
        elif self.byte_mask_pipeline_out == 21:
            self.selected_byte = self.rd_data_in[175, 168]
        elif self.byte_mask_pipeline_out == 22:
            self.selected_byte = self.rd_data_in[183, 176]
        elif self.byte_mask_pipeline_out == 23:
            self.selected_byte = self.rd_data_in[191, 184]
        elif self.byte_mask_pipeline_out == 24:
            self.selected_byte = self.rd_data_in[199, 192]
        elif self.byte_mask_pipeline_out == 25:
            self.selected_byte = self.rd_data_in[207, 200]
        elif self.byte_mask_pipeline_out == 26:
            self.selected_byte = self.rd_data_in[215, 208]
        elif self.byte_mask_pipeline_out == 27:
            self.selected_byte = self.rd_data_in[223, 216]
        elif self.byte_mask_pipeline_out == 28:
            self.selected_byte = self.rd_data_in[231, 224]
        elif self.byte_mask_pipeline_out == 29:
            self.selected_byte = self.rd_data_in[239, 232]
        elif self.byte_mask_pipeline_out == 30:
            self.selected_byte = self.rd_data_in[247, 240]
        elif self.byte_mask_pipeline_out == 31:
            self.selected_byte = self.rd_data_in[255, 248]
        else:
            self.selected_byte = 0


    @always_comb
    def data_out_mux_logic(self):
        self.rd_data_in_masked = concat(const(0, self._params.mu_word_width - 8), self.selected_byte)

        if self.source_resp_pipeline_out == self._params.input_scale_req_src_code:
            self.rd_data_out_to_fifo = self.rd_data_in_masked
        else:
            self.rd_data_out_to_fifo = self.rd_data_in