from kratos import Generator, always_ff, posedge


class GlbClkEnGen(Generator):
    def __init__(self, cnt: int):
        super().__init__(f"glb_clk_en_gen_{cnt}")
        self.cnt = cnt
        self.p_cnt = self.param("cnt", width=32, value=32)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.enable = self.input("enable", 1)
        self.clk_en = self.output("clk_en", 1)
        self.clk_en_cnt = self.var("clk_en_cnt", 32)

        self.add_always(self.clk_en_gen_counter)
        self.wire(self.clk_en, self.enable | (self.clk_en_cnt > 0))

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def clk_en_gen_counter(self):
        if self.reset:
            self.clk_en_cnt = 0
        else:
            if self.enable:
                self.clk_en_cnt = self.p_cnt - 1
            elif self.clk_en_cnt > 0:
                self.clk_en_cnt = self.clk_en_cnt - 1
