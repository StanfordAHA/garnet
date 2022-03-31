from kratos import always_ff, always_comb, posedge, Generator, clog2
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
        self.cycle_count = self.input("cycle_count", self._params.cycle_count_width)
        self.current_addr = self.input("current_addr", self._params.cycle_count_width)
        self.finished = self.input("finished", 1)
        self.valid_output = self.output("valid_output", 1)

        # local variables
        self.valid_gate = self.var("valid_gate", 1)

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
        self.valid_output = (self.cycle_count == self.current_addr) & (~self.valid_gate)
