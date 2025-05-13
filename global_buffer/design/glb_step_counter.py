from kratos import always_ff, always_comb, posedge, Generator, const
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbStepCounter(Generator):
    ''' Output high on mod 8 step '''

    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_sched_gen")
        self._params = _params

        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")
        self.step = self.input("step", 1)
        self.restart = self.input("restart", 1)
        self.mod_8_step = self.output("mod_8_step", 1)

        # local variables
        self.step_count = self.var("step_count", self._params.cycle_count_width)

        self.add_always(self.step_count_ff)
        self.add_always(self.mod_8_step_logic)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def step_count_ff(self):
        if self.reset:
            self.step_count = 0
        elif self.clk_en:
            if self.restart:
                self.step_count = 0
            elif self.step:
                self.step_count = self.step_count + 1

    @always_comb
    def mod_8_step_logic(self):
        self.mod_8_step = (self.step_count[2, 0] == const(7, 3))