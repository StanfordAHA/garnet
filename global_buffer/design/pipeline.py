from kratos import Generator, always_ff, posedge, resize
import math


class Pipeline(Generator):
    def __init__(self, width: int, depth: int, is_clk_en=False, flatten_output=False):
        super().__init__(
            f"pipeline_W_{width}_D_{depth}{'_clk_en' if is_clk_en else ''}")
        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.width = width
        self.depth = depth
        self.flatten_output = flatten_output
        self.depth_width = math.ceil(math.log(self.depth, 2))

        if is_clk_en:
            self.clk_en = self.clock_en("clk_en")

        self.in_ = self.input("in_", self.width)
        if self.flatten_output:
            if self.width == 1:
                self.out_ = self.output("out_", self.depth)
            else:
                self.out_ = self.output("out_", self.width, size=self.depth)
        else:
            self.out_ = self.output("out_", self.width)

        if self.width == 1:
            self.pipeline_r = self.var(
                "pipeline_r", width=self.depth)
        else:
            self.pipeline_r = self.var(
                "pipeline_r", width=self.width, size=self.depth)

        if is_clk_en:
            self.add_always(self.pipeline_clk_en)
        else:
            self.add_always(self.pipeline)

        if self.flatten_output:
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
