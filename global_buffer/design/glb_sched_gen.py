from kratos import always_ff, always_comb, posedge, Generator, const, clog2
from global_buffer.design.glb_addr_gen import GlbAddrGen
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbSchedGen(Generator):
    ''' Generate schedule '''

    def __init__(self, _params: GlobalBufferParams):
        super().__init__(f"glb_sched_gen")
        self._params = _params

        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")
        self.restart = self.input("restart", 1)
        self.cycle_count = self.input("cycle_count", self._params.axi_data_width)
        self.strides = self.input("strides", self._params.axi_data_width,
                                  size=self._params.loop_level,
                                  packed=True, explicit_array=True)
        self.start_addr = self.input("start_addr", self._params.axi_data_width)
        self.mux_sel = self.input("mux_sel", max(clog2(self._params.loop_level), 1))
        self.finished = self.input("finished", 1)
        self.valid_output = self.output("valid_output", 1)

        # local variables
        self.valid_out = self.var("valid_out", 1)
        self.addr_out = self.var("addr_out", self._params.axi_data_width)
        self.valid_gate = self.var("valid_gate", 1)

        # wiring
        self.wire(self.valid_output, self.valid_out)

        self.add_child(f"glb_sched_addr_gen",
                       GlbAddrGen(self._params),
                       clk=self.clk,
                       clk_en=self.clk_en,
                       start_addr=self.start_addr,
                       strides=self.strides,
                       reset=self.reset,
                       step=self.valid_out,
                       mux_sel=self.mux_sel,
                       addr_out=self.addr_out,
                       restart=self.restart)

        self.add_always(self.valid_gate_ff)
        self.add_always(self.set_valid_out)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def valid_gate_ff(self):
        if self.reset:
            self.valid_gate = 1
        elif self.clk_en:
            if self.restart:
                self.valid_gate = 0
            elif self.finished:
                self.valid_gate = 1

    @always_comb
    def set_valid_out(self):
        self.valid_out = (self.cycle_count == self.addr_out) & (~self.valid_gate)
