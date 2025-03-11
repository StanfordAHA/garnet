from kratos import Generator, always_comb, const, concat
from kratos import Generator, RawStringStmt, always_ff, posedge
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
        # self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.rd_addr_build_in = self.input("rd_addr_build_in", self._params.glb_addr_width)
        self.rd_addr_build_out = self.output("rd_addr_build_out", self._params.glb_addr_width)

        # local_variables 
        self.rd_addr_build_out_w = self.var("rd_addr_build_out_w", self._params.glb_addr_width)
        self.tile_id_incr = self.var("tile_id_incr", self._params.tile_sel_addr_width)

        # localparam
        self.tile_sel_msb = _params.bank_addr_width + _params.bank_sel_addr_width + _params.tile_sel_addr_width - 1
        self.tile_sel_lsb = _params.bank_addr_width + _params.bank_sel_addr_width

        self.add_always(self.tile_id_add_ff)
        self.add_always(self.addr_build_comb)

    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def tile_id_add_ff(self):
        if self.reset:
            self.rd_addr_build_out = 0
        else:
            self.rd_addr_build_out = self.rd_addr_build_out_w

    @ always_comb
    def addr_build_comb(self):
        self.tile_id_incr = self.rd_addr_build_in[self.tile_sel_msb, self.tile_sel_lsb] + 1
        self.rd_addr_build_out_w = concat(self.tile_id_incr, self.rd_addr_build_in[self.tile_sel_lsb - 1, 0])

    
