from kratos import Generator, always_latch


class GlbClkGate(Generator):
    def __init__(self):
        self.clk_in = self.clock("clk")
        self.enable = self.input("enable", 1)
        self.gclk = self.output("glck")

        self.enable_latch = self.input("enable_latch", 1)
        self.add_always(self.clk_en_latch)
        self.wire(self.gclk, (self.clk_in & self.enable_latch))

    @always_latch
    def clk_en_latch(self):
        if (~self.clk_in):
            self.enable_latch = self.enable
