from kratos import Generator, always_latch


class CG(Generator):
    def __init__(self, name: str):
        super().__init__(name)
        self.E = self.input("E", 1)
        self.CLK = self.clock("CLK")
        self.TE = self.input("TE", 1)
        self.Z = self.output("Z", 1)

        self.enable_latch = self.var("enable_latch", 1)
        self.add_always(self.clk_en_latch)
        self.wire(self.Z, (self.CLK & self.enable_latch))

    @always_latch
    def clk_en_latch(self):
        if (~self.CLK):
            self.enable_latch = self.E
