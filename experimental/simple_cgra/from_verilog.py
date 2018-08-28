from from_magma import FromMagma
import magma


class FromVerilog(FromMagma):
    def __init__(self, filename):
        underlying = magma.DeclareFromVerilogFile(filename)[0]
        super().__init__(underlying)
