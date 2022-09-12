from kratos import Generator, always_ff, posedge


class GFSRAM(Generator):
    def __init__(self, num_words=2048, word_width=64):
        super().__init__(f"IN12LP_S1DB_W{num_words:05}B{word_width:03}M08S2_HB")
        self.num_words = num_words
        self.word_width = word_width
        self.CLK = self.clock("CLK")
        self.CEN = self.input("CEN", 1)
        self.RDWEN = self.input("RDWEN", 1)
        self.A = self.input("A", self.num_words.bit_length() - 1)
        self.D = self.input("D", self.word_width)
        self.BW = self.input("BW", self.word_width)
        self.Q = self.output("Q", self.word_width)
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

        self.data_array = self.var("data_array", self.word_width, size=self.num_words)

        self.add_always(self.ff)

    @always_ff((posedge, "CLK"))
    def ff(self):
        if self.CEN == 0:
            self.Q = self.data_array[self.A]
            if self.RDWEN == 0:
                for i in range(self.word_width):
                    if self.BW[i] == 0:
                        self.data_array[self.A][i] = self.D[i]
