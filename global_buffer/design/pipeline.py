from kratos import Generator, always_ff, posedge, resize, clog2


class Pipeline(Generator):
    def __init__(self, width: int,  depth: int, is_clk_en=False, flatten_output=False):
        name_suffix = ""
        if is_clk_en:
            name_suffix += "_stall"
        if flatten_output:
            name_suffix += "_array"
        super().__init__(f"pipeline_W_{width}_D_{depth}{name_suffix}")
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.width = width
        self.depth = depth
        self.depth_width = clog2(self.depth)

        if is_clk_en:
            self.clk_en = self.clock_en("clk_en")

        self.in_ = self.input("in_", self.width)
        if flatten_output:
            self.out_ = self.output("out_", self.width, size=self.depth)
        else:
            self.out_ = self.output("out_", self.width)

        self.pipeline_r = self.var(
            "pipeline_r", width=self.width, size=self.depth, explicit_array=True)

        if is_clk_en:
            self.add_always(self.pipeline_clk_en)
        else:
            self.add_always(self.pipeline)

        if flatten_output:
            self.wire(self.out_, self.pipeline_r)
        else:
            self.wire(self.out_, self.pipeline_r[self.depth-1])

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline_clk_en(self):
        if self.reset:
            for i in range(self.depth):
                self.pipeline_r[i] = 0
        elif self.clk_en:
            for i in range(self.depth):
                if i == 0:
                    self.pipeline_r[i] = self.in_
                else:
                    self.pipeline_r[i] = self.pipeline_r[resize(
                        i-1, self.depth_width)]

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline(self):
        if self.reset:
            for i in range(self.depth):
                self.pipeline_r[i] = 0
        else:
            for i in range(self.depth):
                if i == 0:
                    self.pipeline_r[i] = self.in_
                else:
                    self.pipeline_r[i] = self.pipeline_r[resize(
                        i-1, self.depth_width)]
