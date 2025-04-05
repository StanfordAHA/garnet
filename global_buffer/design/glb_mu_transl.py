from kratos import Generator, always_comb, always_ff, clog2, clock_en, const, posedge, ternary, concat
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.fifo import FIFO


class GlbMUTransl(Generator):
    def __init__(self, _params: GlobalBufferParams):
        self._params = _params
        super().__init__(f"glb_mu_transl")
      
        # Clock and Reset
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        # I/Os
        self.addr_in = self.input("addr_in", self._params.mu_addr_width)
        self.rq_in_vld = self.input("rq_in_vld", 1)
        self.rq_in_rdy = self.output("rq_in_rdy", 1)

        # log2(number of bytes requested)
        self.size_in = self.input("size_in", self._params.mu_tl_num_burst_bits)

        self.addr2glb = self.output("addr2glb", self._params.glb_addr_width)
        self.rd_en2glb = self.output("rd_en2glb", 1)

        self.rd_data_in = self.input("rd_data_in", self._params.mu_word_width)
        self.rd_data_in_vld = self.input("rd_data_in_vld", 1)

        self.rd_data_out = self.output("rd_data_out", self._params.mu_word_width)
        self.rd_data_out_vld = self.output("rd_data_out_vld", 1)
        self.rd_data_out_rdy = self.input("rd_data_out_rdy", 1) 

        # Localparam
        self.num_tile_id_bits_in_mu_addr = self._params.tile_sel_addr_width - clog2(self._params.mu_word_num_tiles)
        self.addr_incr_value = pow(2, self._params.mu_word_byte_offset)
        self.num_glb_reqs_bitwidth = int(clog2(self._params.mu_rd_max_num_glb_reqs)) + 1

        # Local vars
        self.glb_req_counter = self.var("glb_req_counter",self.num_glb_reqs_bitwidth)
        self.next_glb_req_counter = self.var("next_glb_req_counter",self.num_glb_reqs_bitwidth) 
        self.burst_addr_incr = self.var("burst_addr_incr", self._params.mu_addr_width)
        self.addr_to_adjuster = self.var("addr_to_adjuster", self._params.mu_addr_width)
        self.read_en2glb_w = self.var("read_en2glb_w", 1)
        self.addr_to_glb_w = self.var("addr_to_glb_w", self._params.glb_addr_width)
        self.num_glb_reqs = self.var("num_glb_reqs", self.num_glb_reqs_bitwidth)


        # FIFO signals
        self.addr_fifo_full = self.var("addr_fifo_full", 1)
        self.addr_fifo_empty = self.var("addr_fifo_empty", 1)
        self.addr_fifo_almost_full = self.var("addr_fifo_almost_full", 1)

        self.addr_fifo_out = self.var("addr_fifo_out", self._params.mu_addr_width)  
        self.addr_fifo_out_valid = self.var("addr_fifo_out_valid", 1)
        self.addr_fifo_pop = self.var("addr_fifo_pop", 1)

        self.size_fifo_out = self.var("size_fifo_out", self._params.mu_tl_num_burst_bits)  

        self.data_out_fifo_full = self.var("data_out_fifo_full", 1)
        self.data_out_fifo_empty = self.var("data_out_fifo_empty", 1)
        self.data_out_fifo_almost_full = self.var("data_out_fifo_almost_full", 1)

        self.add_addr_in_fifo_logic()
        self.add_data_out_fifo_logic()
        self.add_size_in_fifo_logic()
        self.add_always(self.burst_addr_incr_ff)
        self.add_always(self.glb_req_counter_ff)
        self.add_always(self.output_logic)
        self.add_always(self.address_adjustment_logic)
        self.add_always(self.size_in_to_num_glb_reqs_logic)


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
        self.read_req_fsm.output(self.read_en2glb_w)    
        self.read_req_fsm.output(self.addr_to_adjuster)
        self.read_req_fsm.output(self.next_glb_req_counter)
       
        # Next State Logic 
        # Next sate is busy if the address is valid and number of glb requests > 1 
        READY.next(BUSY, self.addr_fifo_out_valid & (self.num_glb_reqs[self.num_glb_reqs_bitwidth - 1, 1] != 0)) #FIXME 
        READY.next(READY, None)

        BUSY.next(READY, self.glb_req_counter == 1) #FIXME
        BUSY.next(BUSY, None)

        # FSM Output Logic
        READY.output(self.addr_fifo_pop, 1)
        READY.output(self.read_en2glb_w, self.addr_fifo_out_valid)
        READY.output(self.addr_to_adjuster, self.addr_fifo_out)
        READY.output(self.next_glb_req_counter, self.num_glb_reqs - 1) # FIXME 

        BUSY.output(self.addr_fifo_pop, 0)
        BUSY.output(self.read_en2glb_w, 1)
        BUSY.output(self.addr_to_adjuster, self.burst_addr_incr)
        BUSY.output(self.next_glb_req_counter, self.glb_req_counter - 1) 
       
        # Realize FSM
        self.read_req_fsm.realize()

        ###################
        # End read_req_fsm
        ###################


    def add_addr_in_fifo_logic(self):
        # ADDRESS FIFO
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
        # BURST SIZE FIFO 
        self.size_fifo = FIFO(self._params.mu_tl_num_burst_bits, self._params.mu_tl_req_fifo_depth)
        self.add_child("size_fifo",
                       self.size_fifo,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                    #    flush=self.st_dma_start_pulse_r,
                        # TODO: Figure out what to put here for flush
                       flush=const(0, 1), 
                       data_in=self.size_in,
                       data_out=self.size_fifo_out,
                       push=self.rq_in_vld,
                       pop=self.addr_fifo_pop,
                       almost_full_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)),
                       almost_empty_diff=const(2, clog2(self._params.mu_tl_req_fifo_depth)))
    
    def add_data_out_fifo_logic(self):
        # DATA OUT FIFO
        self.data_out_fifo = FIFO(self._params.mu_word_width, self._params.mu_data_out_fifo_depth)
        self.add_child("data_out_fifo",
                       self.data_out_fifo,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                    #    flush=self.st_dma_start_pulse_r,
                        # TODO: Figure out what to put here for flush
                       flush=const(0, 1), 
                       data_in=self.rd_data_in,
                       data_out=self.rd_data_out,
                       push=self.rd_data_in_vld,
                       pop=self.rd_data_out_rdy,
                       full=self.data_out_fifo_full,
                       empty=self.data_out_fifo_empty,
                       almost_full=self.data_out_fifo_almost_full,
                       almost_full_diff=const(2, clog2(self._params.mu_data_out_fifo_depth)),
                       almost_empty_diff=const(2, clog2(self._params.mu_data_out_fifo_depth)))
        
        self.wire(self.rd_data_out_vld, ~self.data_out_fifo_empty)    

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def glb_req_counter_ff(self):
        if self.reset:
            self.glb_req_counter = 0
        else:
            self.glb_req_counter = self.next_glb_req_counter 

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def burst_addr_incr_ff(self):
        if self.reset:
            self.burst_addr_incr = 0
        else:
            self.burst_addr_incr = self.addr_to_adjuster + self.addr_incr_value 

    @always_comb
    def size_in_to_num_glb_reqs_logic(self):

        # 2^7 = 128 bytes = 4 requests (MAXIMUM)
        if self.size_fifo_out == 7:
            self.num_glb_reqs = 4

        # 2^6 = 64 bytes = 2 requests    
        elif self.size_fifo_out == 6:
            self.num_glb_reqs = 2

        # Anything smaller only needs 1 request     
        else:
            self.num_glb_reqs = 1

    @always_comb
    def output_logic(self):
        self.addr2glb = self.addr_to_glb_w
        self.rd_en2glb = self.read_en2glb_w

    # Adjusted address consists of 3 components:
    # 1. The tileID bits provided by MU, referring to a group of GLB tiles 
    # 2. Inserted 0s at MSBs of tileID, to refer to base tile of that group
    # 3. Inserted 0 for the bank ID
    # 4. Rest of address (ignoring bottom 2 bits. These are the bits that are replaced by 0s above for tileID and bank ID)
    @always_comb
    def address_adjustment_logic(self):
        if self.num_tile_id_bits_in_mu_addr > 0:
            self.addr_to_glb_w = concat(self.addr_to_adjuster[self._params.mu_addr_width - 1, self._params.mu_addr_width - 1 - (self.num_tile_id_bits_in_mu_addr - 1)], 
                                                const(0, clog2(self._params.mu_word_num_tiles)),
                                                const(0, self._params.bank_sel_addr_width),
                                                self.addr_to_adjuster[self._params.mu_addr_width - 1 - (self.num_tile_id_bits_in_mu_addr), clog2(self._params.mu_word_num_tiles) + self._params.bank_sel_addr_width])
        else:
            self.addr_to_glb_w = concat(const(0, clog2(self._params.mu_word_num_tiles)),
                                                 const(0, self._params.bank_sel_addr_width),
                                                 self.addr_to_adjuster[self._params.mu_addr_width - (self.num_tile_id_bits_in_mu_addr), clog2(self._params.mu_word_num_tiles) + self._params.bank_sel_addr_width])