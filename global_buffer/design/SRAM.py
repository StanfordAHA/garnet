from kratos import Generator, always_ff, posedge


class SRAM(Generator):
    def __init__(self, process: str, name: str, word_size: int, depth: int):
        super().__init__(name)
        self.data_array = self.var("data_array", word_size, size=depth)

        if process == "TSMC":
            self.CLK = self.clock("CLK")
            self.CEB = self.input("CEB", 1)
            self.WEB = self.input("WEB", 1)
            self.BWEB = self.input("BWEB", 64)
            self.D = self.input("D", 64)
            self.A = self.input("A", 11)
            self.Q = self.output("Q", 64)
            self.RTSEL = self.input("RTSEL", 2)
            self.WTSEL = self.input("WTSEL", 2)

            self.add_always(self.tsmc_ff)
        elif process == "GF":
            self.CLK = self.clock("CLK")
            self.CEN = self.input("CEN", 1)
            self.RDWEN = self.input("RDWEN", 1)
            self.BW = self.input("BW", 64)
            self.D = self.input("D", 64)
            self.A = self.input("A", 11)
            self.Q = self.output("Q", 64)
            self.T_LOGIC = self.input("T_LOGIC", 1)
            self.T_Q_RST = self.input("T_Q_RST", 1)
            self.MA_SAWL1 = self.input("MA_SAWL1", 1)
            self.MA_SAWL0 = self.input("MA_SAWL0", 1)
            self.MA_WL1 = self.input("MA_WL1", 1)
            self.MA_WL0 = self.input("MA_WL0", 1)
            self.MA_WRAS1 = self.input("MA_WRAS1", 1)
            self.MA_WRAS0 = self.input("MA_WRAS0", 1)
            self.MA_VD1 = self.input("MA_VD1", 1)
            self.MA_VD0 = self.input("MA_VD0", 1)
            self.MA_WRT = self.input("MA_WRT", 1)
            self.MA_STABAS1 = self.input("MA_STABAS1", 1)
            self.MA_STABAS0 = self.input("MA_STABAS0", 1)

            self.add_always(self.gf_ff)

    @always_ff((posedge, "CLK"))
    def tsmc_ff(self):
        if self.CEB == 0:
            self.Q = self.data_array[self.A]
            if self.WEB == 0:
                for i in range(64):
                    if self.BWEB[i] == 0:
                        self.data_array[self.A][i] = self.D[i]

    @always_ff((posedge, "CLK"))
    def gf_ff(self):
        if self.CEN == 0:
            self.Q = self.data_array[self.A]
            if self.RDWEN == 0:
                for i in range(64):
                    if self.BW[i]:
                        self.data_array[self.A][i] = self.D[i]
