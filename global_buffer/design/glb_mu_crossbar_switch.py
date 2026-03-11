from kratos import Generator, always_ff, always_comb, posedge, concat, const, clog2, resize
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_tile_ifc import GlbTileInterface
from global_buffer.design.glb_tile_data_loop_ifc import GlbTileDataLoopInterface
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.pipeline import Pipeline
from global_buffer.design.glb_clk_en_gen import GlbClkEnGen
import os


class GlbMUCrossbarSwitch(Generator):
    def __init__(self, _params: GlobalBufferParams):
        name = "glb_mu_crossbar_switch"
        super().__init__(name)


        self._params = _params
        self.header = GlbHeader(self._params)

        # Clock and reset
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        # I/O
        self.mu_crossbar_rd_addr_d = self.input("mu_crossbar_rd_addr_d", self._params.glb_addr_width)
        self.mu_crossbar_rd_en = self.input("mu_crossbar_rd_en", 1)
        self.rdrq_packet = self.output("rdrq_packet", self.header.mu_crossbar_rdrq_packet_t)
        self.rdrs_packet = self.input("rdrs_packet", self.header.rdrs_packet_t, size=self._params.banks_per_tile) # size > 1 for multibank HW
        # self.mu_crossbar_rd_data_out = self.output("mu_crossbar_rd_data_out", self._params.mu_word_width/self._params.mu_word_num_tiles)
        self.mu_crossbar_rd_data_out = self.output("mu_crossbar_rd_data_out", 128)
        self.mu_crossbar_rd_data_valid_out = self.output("mu_crossbar_rd_data_valid_out", 1)
        self.clk_en_mu_crossbar2bank = self.output("clk_en_mu_crossbar2bank", 1)

        # local variables
        self.mu_crossbar_rd_en_d = self.var("mu_crossbar_rd_en_d", 1)

        self.add_always(self.rdrq_logic)
        self.add_always(self.rdrs_logic)
        self.add_always(self.rd_en_pipeline)
        self.add_crossbar2bank_clk_en_gen()


    def add_crossbar2bank_clk_en_gen(self):
        self.bank_clk_en_gen = GlbClkEnGen(cnt=self._params.bankmux2sram_rd_delay + 2) # add + 1 for margin to ensure the clock enable is high for the entire duration of the read transaction
        self.bank_clk_en_gen.p_cnt.value = self._params.bankmux2sram_rd_delay + 2
        self.add_child("bank_clk_en_gen",
                    self.bank_clk_en_gen,
                    clk=self.clk,
                    reset=self.reset,
                    enable=self.mu_crossbar_rd_en,
                    clk_en=self.clk_en_mu_crossbar2bank
                )


    @always_comb
    def rdrq_logic(self):
        self.wire(self.rdrq_packet["rd_addr"], self.mu_crossbar_rd_addr_d)
        # Delay rd_en by 1 cycle to align with rd_addr
        self.wire(self.rdrq_packet["rd_en"], self.mu_crossbar_rd_en_d)

    @always_comb
    def rdrs_logic(self):
        # for i in range(self._params.banks_per_tile):
        #     self.mu_crossbar_rd_data_out[(i+1)*self._params.bank_data_width-1, i*self._params.bank_data_width] = self.rdrs_packet[i]["rd_data"]

        self.mu_crossbar_rd_data_out[63, 0] = self.rdrs_packet[0]["rd_data"]
        self.mu_crossbar_rd_data_out[127, 64] = self.rdrs_packet[1]["rd_data"]
        self.mu_crossbar_rd_data_valid_out = self.rdrs_packet[0]["rd_data_valid"]


    @ always_ff((posedge, "clk"), (posedge, "reset"))
    def rd_en_pipeline(self):
        if self.reset:
            self.mu_crossbar_rd_en_d = 0
        else:
           self.mu_crossbar_rd_en_d = self.mu_crossbar_rd_en
