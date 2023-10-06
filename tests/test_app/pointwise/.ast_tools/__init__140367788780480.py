def __init__(self):

    # Data registers
    self.rega: DataReg = DataReg()
    self.regb: DataReg = DataReg()
    self.regc: DataReg = DataReg()

    # Bit Registers
    self.regd: BitReg = BitReg()
    self.rege: BitReg = BitReg()
    self.regf: BitReg = BitReg()

    # Execution
    self.alu: ALU = ALU()
    self.fpu: FPU = FPU()
    self.fp_custom: FPCustom = FPCustom()

    # Lut
    self.lut: LUT = LUT()

    # Condition code
    self.cond: Cond = Cond()
