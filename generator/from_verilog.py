import magma
from generator.from_magma import FromMagma


class FromVerilog(FromMagma):
    def __init__(self, filename):
        underlying = magma.DefineFromVerilogFile(filename)[0]
        super().__init__(underlying)
