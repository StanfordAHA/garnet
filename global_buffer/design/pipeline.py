from kratos import Generator, always_ff, posedge, resize


class Pipeline(Generator):
    def __init__(self, is_clk_en=False, flatten_output=False):
        name_suffix = ""
        if is_clk_en:
            name_suffix += "_stall"
        if flatten_output:
            name_suffix += "_array"
        super().__init__(f"pipeline{name_suffix}")
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")

        # parameters
        self.depth_width = 16
        self.p_width = self.param("WIDTH", 16, initial_value=16)
        self.p_depth = self.param("DEPTH", self.depth_width, initial_value=1)
        assert self.p_width.value < 2**16
        assert self.p_depth.value < 2**self.depth_width

        self.flatten_output = flatten_output

        if is_clk_en:
            self.clk_en = self.clock_en("clk_en")

        self.in_ = self.input("in_", self.p_width)
        if self.flatten_output:
            self.out_ = self.output("out_", self.p_width, size=self.p_depth)
        else:
            self.out_ = self.output("out_", self.p_width)

        self.pipeline_r = self.var(
            "pipeline_r", width=self.p_width, size=self.p_depth)

        if is_clk_en:
            self.add_always(self.pipeline_clk_en)
        else:
            self.add_always(self.pipeline)

        if self.flatten_output:
            self.wire(self.out_, self.pipeline_r)
        else:
            self.wire(self.out_, self.pipeline_r[self.p_depth-1])

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline_clk_en(self):
        if self.reset:
            for i in range(self.p_depth.value):
                self.pipeline_r[i] = 0
        elif self.clk_en:
            for i in range(self.p_depth.value):
                if i == 0:
                    self.pipeline_r[i] = self.in_
                else:
                    self.pipeline_r[i] = self.pipeline_r[resize(
                        i-1, self.depth_width)]

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline(self):
        if self.reset:
            for i in range(self.p_depth.value):
                self.pipeline_r[i] = 0
        else:
            for i in range(self.p_depth.value):
                if i == 0:
                    self.pipeline_r[i] = self.in_
                else:
                    self.pipeline_r[i] = self.pipeline_r[resize(
                        i-1, self.depth_width)]
