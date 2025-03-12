from kratos import Generator, always_comb, const, concat
from kratos import Generator, RawStringStmt, always_ff, posedge, resize, clog2
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_header import GlbHeader
import os


class GlbAddrBuilder(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_addr_builder")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.rdrq_packet_build_in = self.input("rdrq_packet_build_in", self.header.rdrq_packet_t)
        self.rdrq_packet_incr_out = self.output("rdrq_packet_incr_out", self.header.rdrq_packet_t)
        self.rdrq_packet_build_out = self.output("rdrq_packet_build_out", self.header.rdrq_packet_t)

        # local_variables 
        self.rdrq_packet_incr_out_w = self.var("rdrq_packet_incr_out_w", self.header.rdrq_packet_t)
        self.tile_id_incr = self.var("tile_id_incr", self._params.tile_sel_addr_width)
        self.rd_addr_build_out_d_arr = self.var("rd_addr_build_out_d_arr", self._params.glb_addr_width, size=self._params.num_mu_addr_builder_tiles, explicit_array=True)
        self.rd_en_build_out_d_arr = self.var("rd_en_build_out_d_arr", 1, size=self._params.num_mu_addr_builder_tiles, explicit_array=True)
        self.glb_tile_id_n = self.var("glb_tile_id_n", self._params.tile_sel_addr_width)

        # localparam
        self.tile_sel_msb = _params.bank_addr_width + _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1
        self.tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width


         # Addr delay pipeline
        self.addr_delay_pipeline = Pipeline(width=self._params.glb_addr_width,
                                       depth=self._params.num_mu_addr_builder_tiles, flatten_output=True)
        self.add_child("addr_delay_pipeline",
                       self.addr_delay_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.rdrq_packet_build_in['rd_addr'],
                       out_=self.rd_addr_build_out_d_arr)
        
        # rd_en delay pipeline
        self.rd_en_delay_pipeline = Pipeline(width=1,
                                       depth=self._params.num_mu_addr_builder_tiles, flatten_output=True)
        self.add_child("rd_en_delay_pipeline",
                       self.rd_en_delay_pipeline,
                       clk=self.clk,
                       clk_en=const(1, 1),
                       reset=self.reset,
                       in_=self.rdrq_packet_build_in['rd_en'],
                       out_=self.rd_en_build_out_d_arr)


        self.wire(self.glb_tile_id_n, ~self.glb_tile_id)
        self.wire(self.rdrq_packet_build_out['rd_addr'], self.rd_addr_build_out_d_arr[resize(self.glb_tile_id_n, clog2(self._params.num_mu_addr_builder_tiles))])
        self.wire(self.rdrq_packet_build_out['rd_en'], self.rd_en_build_out_d_arr[resize(self.glb_tile_id_n, clog2(self._params.num_mu_addr_builder_tiles))])

   
        self.add_always(self.tile_id_incr_ff)
        self.add_always(self.tile_id_incr_comb)

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def tile_id_incr_ff(self):
        if self.reset:
            self.rdrq_packet_incr_out = 0
        else:
            self.rdrq_packet_incr_out = self.rdrq_packet_incr_out_w

    @ always_comb
    def tile_id_incr_comb(self):
        self.tile_id_incr = self.glb_tile_id + 1
        self.rdrq_packet_incr_out_w['rd_addr'] = concat(self.tile_id_incr, self.rdrq_packet_build_in[self.tile_sel_lsb - 1, 0])
        self.rdrq_packet_incr_out_w['rd_en'] = self.rdrq_packet_build_in['rd_en']