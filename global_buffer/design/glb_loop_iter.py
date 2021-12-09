from kratos import Generator, clog2, always_ff, always_comb, posedge, const
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbLoopIter(Generator):
    ''' Generate loop iteration '''

    def __init__(self, _params: GlobalBufferParams):
        super().__init__(f"glb_loop_iter")
        self._params = _params

        # INPUTS
        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")

        self.ranges = self.input("ranges", self._params.axi_data_width,
                                 size=self._params.loop_level,
                                 packed=True, explicit_array=True)
        self.dim = self.input("dim", 1 + clog2(self._params.loop_level))
        self.step = self.input("step", 1)
        self.mux_sel_out = self.output("mux_sel_out", max(clog2(self._params.loop_level), 1))
        self.restart = self.output("restart", 1)

        # local varaibles
        self.dim_counter = self.var("dim_counter", self._params.axi_data_width,
                                    size=self._params.loop_level,
                                    packed=True,
                                    explicit_array=True)

        self.max_value = self.var("max_value", self._params.loop_level)
        self.mux_sel = self.var("mux_sel", max(clog2(self._params.loop_level), 1))
        self.wire(self.mux_sel_out, self.mux_sel)

        self.not_done = self.var("not_done", 1)
        self.clear = self.var("clear", self._params.loop_level)
        self.inc = self.var("inc", self._params.loop_level)

        self.is_maxed = self.var("is_maxed", 1)
        self.wire(self.is_maxed, (self.dim_counter[self.mux_sel]
                                  == self.ranges[self.mux_sel]) & self.inc[self.mux_sel])

        self.add_code(self.set_mux_sel)
        for i in range(self._params.loop_level):
            self.add_code(self.set_clear, idx=i)
            self.add_code(self.set_inc, idx=i)
            self.add_code(self.dim_counter_update, idx=i)
            self.add_code(self.max_value_update, idx=i)

        self.wire(self.restart, self.step & (~self.not_done))

    @always_comb
    # Find lowest ready
    def set_mux_sel(self):
        self.mux_sel = 0
        self.not_done = 0
        for i in range(self._params.loop_level):
            if ~self.not_done:
                if ~self.max_value[i] & (i < self.dim):
                    self.mux_sel = i
                    self.not_done = 1

    @always_comb
    def set_clear(self, idx):
        self.clear[idx] = 0
        if ((idx < self.mux_sel) | (~self.not_done)) & self.step:
            self.clear[idx] = 1

    @always_comb
    def set_inc(self, idx):
        self.inc[idx] = 0
        if (const(idx, 5) == 0) & self.step & (idx < self.dim):
            self.inc[idx] = 1
        elif (idx == self.mux_sel) & self.step & (idx < self.dim):
            self.inc[idx] = 1

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def dim_counter_update(self, idx):
        if self.reset:
            self.dim_counter[idx] = 0
        else:
            if self.clear[idx]:
                self.dim_counter[idx] = 0
            elif self.inc[idx]:
                self.dim_counter[idx] = self.dim_counter[self.mux_sel] + 1

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def max_value_update(self, idx):
        if self.reset:
            self.max_value[idx] = 0
        elif self.clk_en:
            if self.clear[idx]:
                self.max_value[idx] = 0
            elif self.inc[idx]:
                self.max_value[idx] = self.is_maxed
