from kratos import Generator, always_ff, posedge


class SRAM(Generator):
    def __init__(self, name: str):
        super().__init__(name)
        self.CLK = self.clock("CLK")
        self.CEB = self.input("CEB", 1)
        self.WEB = self.input("WEB", 1)
        self.BWEB = self.input("BWEB", 64)
        self.D = self.input("D", 64)
        self.A = self.input("A", 11)
        self.Q = self.output("Q", 64)
        self.RTSEL = self.input("RTSEL", 2)
        self.WTSEL = self.input("WTSEL", 2)

        self.data_array = self.var("data_array", 64, size=2048)

        self.add_always(self.ff)

    @always_ff((posedge, "CLK"))
    def ff(self):
        if self.CEB == 0:
            self.Q = self.data_array[self.A]
            if self.WEB == 0:
                for i in range(64):
                    if self.BWEB[i] == 0:
                        self.data_array[self.A][i] = self.D[i]
