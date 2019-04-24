import magma
from gemstone.generator.generator import Generator
from gemstone.generator.const import Const
from gemstone.generator.from_verilog import FromVerilog
import os


class Pad(Generator):
    def __init__(self, is_input, is_vertical):
        super().__init__()
        self.is_input = is_input
        self.is_vertical = is_vertical
        if self.is_input:
            pad_type = magma.In(magma.Bit)
            fabric_type = magma.Out(magma.Bit)
        else:
            pad_type = magma.Out(magma.Bit)
            fabric_type = magma.In(magma.Bit)
        self.add_ports(
            pad=pad_type,
            fabric=fabric_type
        )

        pad_verilog_file = "/tsmc16/TSMCHOME/digital/Front_End/verilog/" \
                           "tphn16ffcllgv18e_090a/tphn16ffcllgv18e.v"
        module = "PRWDWUWSWCDGH_"
        if self.is_vertical:
            module += "V"
        else:
            module += "H"
        

        exists = os.path.isfile(pad_verilog_file)
        if exists:
            self.pad = FromVerilog(pad_verilog_file, module)
            # Wire up input/output/control signals to pad
            self.wire(self.ports.pad, self.pad.ports.PAD)
            self.wire(Const(magma.bit(self.is_input)), self.pad.ports.IE)
            if self.is_input:
                self.wire(self.ports.fabric, self.pad.ports.C)
                self.wire(Const(magma.bit(0)), self.pad.ports.I)
            else:
                self.wire(self.ports.fabric, self.pad.ports.I)
        else:
            # Just pass wire through from pad to fabric
            self.wire(self.ports.pad, self.ports.fabric)



    def compile(self):
        raise NotImplementedError()

    def name(self):
        pad_name = "pad_"
        if self.is_input:
            pad_name += "in_"
        else:
            pad_name += "out_"
        if self.is_vertical:
            pad_name += "v"
        else:
            pad_name += "h"
        
        return pad_name 
