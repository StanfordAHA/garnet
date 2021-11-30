from kratos import Generator, always_ff, posedge, resize, clog2, const


class Pipeline(Generator):
    def __init__(self, width: int, depth: int, flatten_output=False, reset_high=False):
        name_suffix = ""
        if flatten_output:
            name_suffix += "_array"
        if reset_high:
            name_suffix += "_reset_high"
        super().__init__(f"pipeline_w_{width}_d_{depth}{name_suffix}")
        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")
        self.width = width
        self.depth = depth
        self.reset_high = reset_high

        if self.depth == 0:
            self.in_ = self.input("in_", self.width)
            self.out_ = self.output("out_", self.width)
            self.wire(self.out_, self.in_)
        else:
            self.depth_width = max(clog2(self.depth), 1)

            self.in_ = self.input("in_", self.width)
            if flatten_output:
                self.out_ = self.output("out_", self.width, size=self.depth)
            else:
                self.out_ = self.output("out_", self.width)

            if self.depth == 1 and self.width == 1:
                self.pipeline_r = self.var(
                    "pipeline_r", width=self.width, size=self.depth)
            else:
                self.pipeline_r = self.var(
                    "pipeline_r", width=self.width, size=self.depth, explicit_array=True)

            if flatten_output:
                self.wire(self.out_, self.pipeline_r)
            else:
                self.wire(self.out_, self.pipeline_r[self.depth - 1])
            self.add_always(self.pipeline)

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline(self):
        if self.reset:
            for i in range(self.depth):
                if self.reset_high:
                    self.pipeline_r[i] = const(2 ** self.width - 1, self.width)
                else:
                    self.pipeline_r[i] = 0
        elif self.clk_en:
            for i in range(self.depth):
                if i == 0:
                    self.pipeline_r[i] = self.in_
                else:
                    self.pipeline_r[i] = self.pipeline_r[resize(
                        i - 1, self.depth_width)]
