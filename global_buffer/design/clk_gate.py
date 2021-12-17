from kratos import Generator, always_latch


class ClkGate(Generator):
    def __init__(self):
        super().__init__("clk_gate")
        self.clk = self.clock("clk")
        self.enable = self.input("enable", 1)
        self.gclk = self.output("gclk", 1)

        self.enable_latch = self.var("enable_latch", 1)
        self.add_always(self.clk_en_latch)
        self.wire(self.gclk, (self.clk & self.enable_latch))

    @always_latch
    def clk_en_latch(self):
        if (~self.clk):
            self.enable_latch = self.enable
