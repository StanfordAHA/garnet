from kratos import Generator, always_comb, always_ff, clog2, clock_en, const, posedge, ternary, concat
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.fifo import FIFO


class GlbMUTransl(Generator):
    def __init__(self, _params: GlobalBufferParams):
        self._params = _params
        super().__init__(f"glb_mu_transl_{self._params.mu_addr_width}_{self._params.glb_addr_width}")
      
        # Clock and Reset
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        # I/Os
        self.addr_in = self.input("addr_in", self._params.mu_addr_width)
        self.addr_in_vld = self.input("addr_in_vld", 1)
        self.addr_in_rdy = self.output("addr_in_rdy", 1)

        self.addr2glb = self.output("addr2glb", self._params.glb_addr_width)
        self.rd_en2glb = self.output("rd_en2glb", 1)

        self.rd_data_in = self.input("rd_data_in", self._params.mu_word_width)
        self.rd_data_in_vld = self.input("rd_data_in_vld", 1)

        self.rd_data_out = self.output("rd_data_out", self._params.mu_word_width)
        self.rd_data_out_vld = self.output("rd_data_out_vld", 1)
        self.rd_data_out_rdy = self.input("rd_data_out_rdy", 1) 

        # Localparam
        self.num_tile_id_bits_in_mu_addr = self._params.tile_sel_addr_width - clog2(self._params.mu_word_num_tiles)
        self.burst_msb = self._params.mu_addr_width - 1
        self.burst_lsb = self.burst_msb - self._params.mu_addr_num_burst_bits + 1
        self.addr_incr_value = pow(2, self._params.bank_byte_offset)

        # Local vars
        self.burst_counter = self.var("burst_counter",self._params.mu_addr_num_burst_bits)
        self.next_burst_counter = self.var("next_burst_counter",self._params.mu_addr_num_burst_bits) 
        self.burst_addr_incr = self.var("burst_addr_incr", self._params.glb_addr_width)
        self.adjusted_addr_fifo_out = self.var("adjusted_addr_fifo_out", self._params.glb_addr_width)
        self.read_en2glb_w = self.var("read_en2glb_w", 1)
        self.addr_to_glb_w = self.var("addr_to_glb_w", self._params.glb_addr_width)

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

        self.add_addr_in_fifo_logic()
        self.add_data_out_fifo_logic()
        self.add_always(self.burst_addr_incr_ff)
        self.add_always(self.burst_counter_ff)
        self.add_always(self.output_logic)
        self.add_always(self.tile_ID_logic)


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
        self.read_req_fsm.output(self.addr_to_glb_w)
        self.read_req_fsm.output(self.next_burst_counter)
       
        # Next State Logic 
        # Next sate is busy if the address is valid and burst > 1 
        READY.next(BUSY, self.addr_fifo_out_valid & (self.addr_fifo_out[self.burst_msb, self.burst_lsb+1] != 0))
        READY.next(READY, None)

        BUSY.next(READY, self.burst_counter == 1)
        BUSY.next(BUSY, None)

        # FSM Output Logic
        READY.output(self.addr_fifo_pop, 1)
        READY.output(self.read_en2glb_w, self.addr_fifo_out_valid)
        READY.output(self.addr_to_glb_w, self.adjusted_addr_fifo_out)
        READY.output(self.next_burst_counter, self.addr_fifo_out[self.burst_msb, self.burst_lsb] - 1)

        BUSY.output(self.addr_fifo_pop, 0)
        BUSY.output(self.read_en2glb_w, 1)
        BUSY.output(self.addr_to_glb_w, self.burst_addr_incr)
        BUSY.output(self.next_burst_counter, self.burst_counter - 1)
       
        # Realize FSM
        self.read_req_fsm.realize()

        ###################
        # End read_req_fsm
        ###################


    def add_addr_in_fifo_logic(self):
        # ADDRESS FIFO
        # TODO: finalize the depth of this fifo in the parameters
        self.addr_fifo = FIFO(self._params.mu_addr_width, self._params.mu_addr_fifo_depth)
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
                       push=self.addr_in_vld,
                       pop=self.addr_fifo_pop,
                       full=self.addr_fifo_full,
                       empty=self.addr_fifo_empty,
                       almost_full=self.addr_fifo_almost_full,
                       almost_full_diff=const(2, clog2(self._params.mu_addr_fifo_depth)),
                       almost_empty_diff=const(2, clog2(self._params.mu_addr_fifo_depth)))
        
        self.wire(self.addr_in_rdy, ~self.addr_fifo_full)
        self.wire(self.addr_fifo_out_valid, ~self.addr_fifo_empty)

    def add_data_out_fifo_logic(self):
        # DATA OUT FIFO
        # TODO: Create mu_data_out_fifo_depth in params
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
    def burst_counter_ff(self):
        if self.reset:
            self.burst_counter = 0
        else:
            self.burst_counter = self.next_burst_counter 

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def burst_addr_incr_ff(self):
        if self.reset:
            self.burst_addr_incr = 0
        else:
            self.burst_addr_incr = self.addr_to_glb_w + self.addr_incr_value 

    @always_comb
    def output_logic(self):
        self.addr2glb = self.addr_to_glb_w
        self.rd_en2glb = self.read_en2glb_w

    # Adjusted address consists of 3 components:
    # 1. The tileID bits provided by MU, referring to a group of GLB tiles 
    # 2. Inserted 0s at MSBs of tileID, to refer to base tile of that group
    # 3. Rest of address 
    @always_comb
    def tile_ID_logic(self):
        if self.num_tile_id_bits_in_mu_addr > 0:
            self.adjusted_addr_fifo_out = concat(self.addr_fifo_out[self.burst_lsb - 1, self.burst_lsb - 1 - (self.num_tile_id_bits_in_mu_addr - 1)], 
                                                const(0, clog2(self._params.mu_word_num_tiles)),
                                                self.addr_fifo_out[self.burst_lsb - 1 - (self.num_tile_id_bits_in_mu_addr), 0])
        else:
            self.adjusted_addr_fifo_out = concat(const(0, clog2(self._params.mu_word_num_tiles)),
                                                self.addr_fifo_out[self.burst_lsb - 1 - (self.num_tile_id_bits_in_mu_addr), 0])