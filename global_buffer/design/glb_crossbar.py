from kratos import Generator, always_comb, clog2


class GlbCrossbar(Generator):
    def __init__(self, width=1, num_input=16, num_output=8):
        self.width = width
        self.num_input = num_input
        self.num_output = num_output
        super().__init__(f"glb_crossbar_I_{self.num_input}_O_{self.num_output}_W_{self.width}")

        self.in_ = self.input("in_", self.width, size=self.num_input, packed=True)
        self.out_ = self.output("out_", self.width, size=self.num_output, packed=True)
        self.sel_ = self.input("sel_", clog2(self.num_input), size=self.num_output, packed=True)

        self.add_always(self.crossbar_logic)

    @always_comb
    def crossbar_logic(self):
        for i in range(self.num_output):
            self.out_[i] = self.in_[self.sel_[i]]
