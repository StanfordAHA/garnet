from from_verilog import FromVerilog


class PECore(FromVerilog):
    def __init__(self):
        super().__init__("experimental/simple_cgra/pe_core.v")
